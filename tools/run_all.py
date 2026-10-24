"""R36: one command for the whole pipeline (SPEC.md R36, ops/DECISIONS.md D20, RUNBOOK_REAL_RUNS.md).

Order: smoke -> pilot (A, E) -> E gate -> core -> monitor -> ethics -> offline scoring
       [-> --exploratory: memory arm, sensitivity, monitor_view, price_paths] [-> --o1: seeds 6-10, last].
- E gate (ops/PLAN.md Phase 4): per family, on the pilot games only. A failing family is replaced ONCE by its
  fallback (configs/run_all.yaml), whose pilot runs as espion_pilot_fb; if a fallback fails too, or no
  fallback is set, the pipeline stops and prints plan B. The decision is recomputed from the logs on every
  run, so a resumed run takes the same path.
- Global budget cap (configs/run_all.yaml budget_usd) over every step, starting from the spend already in
  the logs; each step config keeps its own cap (R17).
- Resumable: games already logged are skipped (write-once logs, R12).
- Real mode refuses unless PREREGISTRATION.md and PREREGISTRATION_ADDENDUM.md are FROZEN, no model id is
  `tbd`, every step uses the same families, and OPENROUTER_API_KEY is set (its value is never read here;
  the repo-root .env is loaded at startup, harness/envfile.py, without overriding the shell).
- Each step keeps its own family entries (a failing family is swapped for its fallback). One game design and
  matched seeds everywhere; temperature and reasoning must match between pooled or matched steps (pilot and
  core; core, monitor and ethics) unless --allow-settings-mismatch.
- --dry: the same chain on the mock client (dry families, mock costs) into a scratch folder, never runs/.
  The dry client prices at the deal price when the E instruction is in its prompt, so the gate passes;
  --dry-gate fail drops that to exercise the fallback and plan B path. Dry numbers are never results.

Usage:
  python -m tools.run_all --dry [--root dry_runs/run_all] [--exploratory] [--o1] [--dry-gate fail]
  python -m tools.run_all [--stop-after smoke|pilot|gate|core|monitor|ethics|scoring|exploratory]
                          [--exploratory] [--o1] [--allow-settings-mismatch]
Exit code: 0 done or stopped as asked, 1 refused, 2 plan B, 3 budget cap hit.
"""
import argparse
import copy
import json
import os
from pathlib import Path

import yaml

from harness.clients import BudgetExceeded, BudgetTracker, MockClient, OpenRouterClient, load_prices
from harness.conditions import load_prereg_texts
from harness.config import GameConfig
from harness.defenses import addendum_is_frozen
from harness.dryclient import make_dry_client
from harness.envfile import load_env
from harness.runlog import load_logs
from harness.runner import RealRunRefused, family_reasoning, run_batch, validate_config
from harness.validation import e_validation
from tools import monitor_view, price_paths, sensitivity
from tools.reproduce import PREREG_CONFIGS, config_name, filter_logs, reproduce

ROOT = Path(__file__).resolve().parent.parent
CONFIGS = ROOT / "configs"
STEP_FILES = {"smoke": "espion_smoke", "pilot": "espion_pilot", "core": "espion_core",
              "monitor": "espion_monitor", "ethics": "espion_ethics", "exploratory": "exploratory/espion_mem"}
STOP_AFTER = ("smoke", "pilot", "gate", "core", "monitor", "ethics", "scoring", "exploratory")
FALLBACK_PILOT = "espion_pilot_fb"
O1_NAME = "espion_o1"
MEMORY_CONFIG = "espion_mem"
MANAGED = {"espion_smoke", "espion_pilot", FALLBACK_PILOT, "espion_core", "espion_monitor", "espion_ethics",
           MEMORY_CONFIG, O1_NAME}
DRY_COST_PER_CALL = 0.0001
DEFAULT_DRY_ROOT = "dry_runs/run_all"
PLAN_B = ("E gate FAILED after the one allowed model change: stop here, no core run. "
          "Go to plan B (ops/PLAN.md): track 1.5, Pareto curve of restrictions, "
          "docs/context/contexte_projet_v7.md section 10.")


class RunAllRefused(RealRunRefused):
    pass


class _Budgeted:
    """Client wrapper: every call's cost goes to the global tracker (raises BudgetExceeded over the cap)."""

    def __init__(self, inner, tracker):
        self.inner, self.tracker = inner, tracker

    @property
    def is_mock(self):
        return getattr(self.inner, "is_mock", True)

    @property
    def last_call(self):
        return getattr(self.inner, "last_call", None)

    def complete(self, messages, model, seed, **settings):
        text, cost = self.inner.complete(messages, model, seed, **settings)
        self.tracker.add(cost)
        return text, cost


def _read(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _canon(families):
    return json.dumps([{"family": f["family"], "models": f["models"]} for f in families], sort_keys=True)


def load_settings(configs_dir, exploratory):
    d = Path(configs_dir)
    steps = {k: _read(d / f"{v}.yaml") for k, v in STEP_FILES.items() if k != "exploratory" or exploratory}
    ra = _read(d / "run_all.yaml")
    return {"steps": steps, "budget_usd": float(ra["budget_usd"]), "fallback": dict(ra.get("fallback") or {}),
            "o1_seeds": list(ra.get("o1_seeds", [6, 7, 8, 9, 10])),
            "o1_budget_usd": float(ra.get("o1_budget_usd", 10.0))}


def _derived(st, name, families, **over):
    base = st["steps"]["core" if name == O1_NAME else "pilot"]
    cfg = copy.deepcopy(base)
    cfg.update(name=name, families=copy.deepcopy(families), **over)
    return cfg


# Steps whose games are pooled (pilot A, E with core B, B_T, C, D) or matched (core with monitor, ethics).
POOLED_OR_MATCHED = (("pilot", "core"), ("core", "monitor", "ethics"))
DESIGN_KEYS = ("n_rounds", "spy_start", "demand")


def check_step_settings(st, cfgs, allow_mismatch=False):
    """Review M3: one game design everywhere, matched seeds, and the same temperature and reasoning in pooled or
    matched steps (that last check only is lifted by allow_mismatch)."""
    pilot = st["steps"]["pilot"]
    for c in cfgs:
        for k in DESIGN_KEYS:
            if c.get(k) != pilot.get(k):
                raise RunAllRefused(f"{k} differs between espion_pilot and {c['name']}: one frozen game design "
                                    "in every step")
    for step in ("monitor", "ethics"):
        if st["steps"][step]["seeds"] != st["steps"]["core"]["seeds"]:
            raise RunAllRefused(f"seeds differ between the core and the {step} config (matched episodes)")
    if allow_mismatch:
        return
    for group in POOLED_OR_MATCHED:
        first = st["steps"][group[0]]
        for step in group[1:]:
            other = st["steps"][step]
            for fam in [f["family"] for f in first["families"]]:
                for field, get in (("temperature", lambda c, f: c.get("temperature")),
                                   ("reasoning", family_reasoning)):
                    a, b = get(first, fam), get(other, fam)
                    if a != b:
                        raise RunAllRefused(
                            f"{field} differs between {first['name']} ({a!r}) and {other['name']} ({b!r}) for "
                            f"family {fam}: these steps are pooled or matched. Make them equal, or pass "
                            "--allow-settings-mismatch to run them anyway")


def swap_families(families, swap):
    """A step's own family entries, with each failing family replaced by its fallback entry."""
    return [copy.deepcopy(swap.get(f["family"], f)) for f in families]


def _all_configs(st, o1):
    """Every config the pipeline may run: the steps, the fallback pilot, O1."""
    cfgs = list(st["steps"].values())
    if st["fallback"]:
        cfgs.append(_derived(st, FALLBACK_PILOT, list(st["fallback"].values())))
    if o1:
        cfgs.append(_derived(st, O1_NAME, st["steps"]["core"]["families"], seeds=st["o1_seeds"],
                             budget_usd=st["o1_budget_usd"]))
    return cfgs


def _model_ids(cfgs):
    return [m for c in cfgs for f in c["families"] for m in f["models"].values()]


def check_settings(st, o1, allow_mismatch=False):
    """Guards that need no file other than the configs: families, fallback, config validity, tbd ids, settings."""
    primary = st["steps"]["pilot"]["families"]
    cfgs = _all_configs(st, o1)
    ids = _model_ids(cfgs)
    if any("tbd" in str(m).lower() for m in ids):
        raise RunAllRefused("model ids are placeholders (tbd) in a step config or in the run_all.yaml fallback: "
                            "the owner has not given the models")
    for name, c in st["steps"].items():
        if _canon(c["families"]) != _canon(primary):
            raise RunAllRefused(f"families differ between the pilot and the {name} config (matched episodes "
                                "need the same families in every step)")
    labels = [f["family"] for f in primary]
    fb_labels = [f["family"] for f in st["fallback"].values()]
    for key, fam in st["fallback"].items():
        if key not in labels:
            raise RunAllRefused(f"fallback key {key!r} is not a primary family label {labels}")
        if fam["family"] in set(labels) - {key} or fb_labels.count(fam["family"]) > 1:
            raise RunAllRefused(f"fallback family {fam['family']!r} would merge with another family")
    for c in cfgs:
        try:
            validate_config(c)
        except ValueError as exc:
            raise RunAllRefused(f"config {c.get('name')}: {exc}") from exc
    check_step_settings(st, cfgs, allow_mismatch)


def dryify(st, root):
    """Same steps, mock client and mock families (mock-a, ...; fallbacks mockfb-a, ...), into root."""
    letters = "abcdefghij"
    primary = [f["family"] for f in st["steps"]["pilot"]["families"]]
    fam = {lab: f"mock-{letters[i]}" for i, lab in enumerate(primary)}
    fam.update({v["family"]: f"mockfb-{letters[i]}" for i, v in enumerate(st["fallback"].values())})

    def mock_family(f):
        lab = fam.get(f["family"], f"mock-{f['family']}")
        return {"family": lab, "models": {"0": f"{lab}/m", "1": f"{lab}/m"}}

    out = copy.deepcopy(st)
    for name, c in out["steps"].items():
        c["mock"], c["mock_cost_per_call"] = True, DRY_COST_PER_CALL
        c["families"] = [mock_family(f) for f in c["families"]]
        for k in ("temperature", "reasoning"):
            c.pop(k, None)
        c["out_dir"] = str(Path(root) / ("runs_exploratory/memory" if c.get("memory") else "runs"))
    out["fallback"] = {fam[k]: mock_family(v) for k, v in st["fallback"].items()}
    return out


def dry_client(cfg, e_instruction, gate="pass"):
    base = make_dry_client(cfg)
    if gate == "fail":
        return base
    deal = round(GameConfig.from_dict(cfg).deal_price, 4)

    def reply(messages, model, seed):
        text = base.reply_fn(messages, model, seed)
        if e_instruction in messages[0]["content"]:
            d = json.loads(text)
            d["price"] = deal
            text = json.dumps(d)
        return text

    return MockClient(reply, cost_per_call=base.cost_per_call)


class _RealFactory:
    """One OpenRouter client for every step, charging max(usage.cost, tokens x configs/prices.yaml) (BYOK)."""

    def __init__(self):
        self.client = OpenRouterClient(prices=load_prices())

    def __call__(self, cfg):
        return self.client

    def check_models(self, ids):
        missing = sorted(set(ids) - set(self.client.prices))
        if missing:
            raise RunAllRefused(f"no price in configs/prices.yaml for {missing}: under BYOK the budget caps "
                                "need a price for every model (R17)")


def default_client_factory(dry, gate):
    if dry:
        e_text = load_prereg_texts()["e_instruction"]
        return lambda cfg: dry_client(cfg, e_text, gate)
    if not os.environ.get("OPENROUTER_API_KEY"):
        raise RunAllRefused("OPENROUTER_API_KEY is not set (put it in the repo-root .env, see .env.example, or export it)")
    return _RealFactory()


def smoke_report(logs):
    """Per family: games, mean cost per game, invalid reply rates, served models, providers, reasoning tokens,
    summed upstream_inference_cost (None when no call reported it)."""
    out = {}
    for fam in sorted({g["family"] for g in logs}):
        gl = [g for g in logs if g["family"] == fam]
        replies = sum(2 * g["n_rounds"] for g in gl)
        prov = [f["provenance"] for g in gl for r in g["rounds"] for f in r["firms"].values() if f.get("provenance")]
        known = [g["reasoning_tokens"] for g in gl if g.get("reasoning_tokens") is not None]
        upstream = [p["upstream_inference_cost"] for p in prov if p.get("upstream_inference_cost") is not None]
        out[fam] = {
            "games": len(gl), "mean_cost_usd": sum(g["cost_usd"] for g in gl) / len(gl),
            "invalid_price_rate": sum(g["invalid_prices"] for g in gl) / replies,
            "invalid_response_rate": sum(g["invalid_responses"] for g in gl) / replies,
            "served_models": sorted({p["served_model"] for p in prov if p.get("served_model")}),
            "providers": sorted({p["provider"] for p in prov if p.get("provider")}),
            "reasoning_tokens": sum(known) if known else None,
            "upstream_inference_cost_usd": sum(upstream) if upstream else None,
        }
    return out


def _logs(path, dry, names=None):
    path = Path(path)
    if not path.exists():
        return []
    return [g for g in load_logs(path) if bool(g.get("mock", True)) == dry
            and (names is None or config_name(g) in names)]


def run_pipeline(root, configs_dir=None, dry=False, client_factory=None, exploratory=False, o1=False,
                 stop_after=None, prereg_path=None, addendum_path=None, dry_gate="pass", n_draws=1000, seed=0,
                 log=print, allow_settings_mismatch=False):
    root = Path(root)
    if stop_after is not None and stop_after not in STOP_AFTER:
        raise ValueError(f"stop_after must be one of {STOP_AFTER}")
    st = load_settings(configs_dir or CONFIGS, exploratory)
    texts = load_prereg_texts(prereg_path)
    if dry:
        if root.resolve() == ROOT or (root / "runs").resolve() == (ROOT / "runs").resolve():
            raise RunAllRefused("--dry writes into a scratch folder, never into the repo runs/")
        st = dryify(st, root)
        check_settings(st, o1, allow_settings_mismatch)
    else:
        if texts.get("status") != "FROZEN":
            raise RunAllRefused("PREREGISTRATION.md is not FROZEN")
        if not addendum_is_frozen(addendum_path):
            raise RunAllRefused("PREREGISTRATION_ADDENDUM.md is not FROZEN (R35)")
        check_settings(st, o1, allow_settings_mismatch)
    if client_factory is None:
        client_factory = default_client_factory(dry, dry_gate)
    if not dry and hasattr(client_factory, "check_models"):
        client_factory.check_models(_model_ids(_all_configs(st, o1)))

    runs, mem_dir = root / "runs", root / "runs_exploratory" / "memory"
    tracker = BudgetTracker(st["budget_usd"])
    tracker.total = sum(g["cost_usd"] for p in (runs, mem_dir) for g in _logs(p, dry, MANAGED))
    res = {"status": None, "steps": [], "gate": None, "spent_usd": tracker.total, "dry": dry, "outputs": []}
    mode = "DRY (mock client, not results)" if dry else "REAL"
    log(f"run_all {mode}: root {root}, budget cap {tracker.cap:.2f} USD, already spent {tracker.total:.4f} USD")

    def run_cfg(step, cfg):
        out = Path(cfg["out_dir"]) if dry else root / cfg["out_dir"]
        new = run_batch(cfg, _Budgeted(client_factory(cfg), tracker), out, prereg_path=prereg_path,
                        addendum_path=addendum_path)
        n = sum(1 for g in _logs(out, dry, {cfg["name"]}))
        log(f"[{step}] {cfg['name']}: {len(new)} new games, {n} logged, spent so far {tracker.total:.4f} USD")
        return new

    def done(step):
        res["steps"].append(step)
        if stop_after == step:
            res["status"] = "stopped"
            log(f"stopped after {step} as asked; run the same command again to resume")
            return True
        return False

    try:
        if tracker.total > tracker.cap:
            raise BudgetExceeded(f"spent {tracker.total:.4f} USD in the logs > cap {tracker.cap:.4f} USD")
        steps = st["steps"]
        run_cfg("smoke", steps["smoke"])
        for fam, r in smoke_report(_logs(runs, dry, {"espion_smoke"})).items():
            log(f"[smoke] {fam}: {r['games']} games, cost per game {r['mean_cost_usd']:.6f} USD, invalid prices "
                f"{r['invalid_price_rate']:.3f}, invalid responses {r['invalid_response_rate']:.3f}, served "
                f"{r['served_models'] or 'n/a'}, providers {r['providers'] or 'n/a'}, "
                f"reasoning tokens {r['reasoning_tokens']}, upstream inference cost (BYOK) "
                f"{r['upstream_inference_cost_usd']}")
        if done("smoke"):
            return res
        run_cfg("pilot", steps["pilot"])
        if done("pilot"):
            return res

        threshold = texts["e_threshold_gap_fraction"]
        primary = steps["pilot"]["families"]
        labels = [f["family"] for f in primary]
        pilot = [g for g in _logs(runs, dry, {"espion_pilot"}) if g["family"] in labels]
        r1 = e_validation(pilot, threshold)
        gate = {"threshold": threshold, "primary": {f: bool(r1.get(f, {}).get("pass")) for f in labels},
                "effects": {f: r1.get(f, {}).get("effect_gap_fraction") for f in labels},
                "fallback_used": False, "fallback": {}}
        res["gate"] = gate
        failing = [f for f in labels if not gate["primary"][f]]
        swap, superseded = {}, None
        log(f"[gate] E on the pilot: {gate['primary']} (effects {gate['effects']}, threshold {threshold})")
        if failing:
            if not all(f in st["fallback"] for f in failing):
                res["steps"].append("gate")
                res["status"] = "plan_b"
                log(f"[gate] no fallback set for {failing}. {PLAN_B}")
                return res
            fb = [copy.deepcopy(st["fallback"][f]) for f in failing]
            log(f"[gate] switching {failing} to fallback {[f['family'] for f in fb]} (once)")
            run_cfg("gate", _derived(st, FALLBACK_PILOT, fb))
            fb_labels = [f["family"] for f in fb]
            r2 = e_validation([g for g in _logs(runs, dry, {FALLBACK_PILOT}) if g["family"] in fb_labels], threshold)
            gate["fallback_used"] = True
            gate["fallback"] = {f: bool(r2.get(f, {}).get("pass")) for f in fb_labels}
            log(f"[gate] E on the fallback pilot: {gate['fallback']}")
            if not all(gate["fallback"].values()):
                res["steps"].append("gate")
                res["status"] = "plan_b"
                log(f"[gate] {PLAN_B}")
                return res
            swap = {f: st["fallback"][f] for f in failing}
            superseded = {g["game_id"] for g in pilot if g["family"] in failing}
        if done("gate"):
            return res

        for step in ("core", "monitor", "ethics"):
            cfg = copy.deepcopy(steps[step])
            cfg["families"] = swap_families(cfg["families"], swap)
            run_cfg(step, cfg)
            if done(step):
                return res

        prereg_cfgs = PREREG_CONFIGS + ((FALLBACK_PILOT,) if superseded is not None else ())
        results = root / "results"
        reproduce(runs, results, n_draws=n_draws, seed=seed, viz_dir=root / "viz" / "data",
                  figures_dir=root / "figures", prereg_path=prereg_path, configs=prereg_cfgs, include_mock=dry,
                  exclude_ids=superseded)
        res["outputs"] += [str(results), str(root / "viz" / "data"), str(root / "figures" / "game_grid.pdf")]
        log(f"[scoring] tables, detectors, defenses -> {results}; viz -> {root / 'viz' / 'data'}; "
            f"figure -> {root / 'figures' / 'game_grid.pdf'}")
        if done("scoring"):
            return res

        if exploratory:
            cfg = copy.deepcopy(steps["exploratory"])
            cfg["families"] = swap_families(cfg["families"], swap)
            run_cfg("exploratory", cfg)
            ex = root / "results_exploratory"
            reproduce(mem_dir, ex / "memory", n_draws=n_draws, seed=seed, prereg_path=prereg_path,
                      configs=(MEMORY_CONFIG,), include_mock=dry)
            main_logs, _ = filter_logs(load_logs(runs), prereg_cfgs, include_mock=dry, exclude_ids=superseded)
            (ex / "sensitivity.md").write_text(sensitivity.table_md(sensitivity.sensitivity_rows(main_logs)),
                                               encoding="utf-8")
            mon = ex / "monitor"
            mon.mkdir(parents=True, exist_ok=True)
            cells, monitors = monitor_view.cell_rows(main_logs), monitor_view.monitor_rows(main_logs)
            (mon / "monitor_view.md").write_text(monitor_view.table_md(cells, monitors), encoding="utf-8")
            monitor_view.write_csv(cells, mon / "monitor_cells.csv", "2x2 say x do per family and condition.")
            monitor_view.write_csv(monitors, mon / "monitor_detection.csv", monitor_view.GROUND_TRUTH_NOTE)
            mem_logs, _ = filter_logs(load_logs(mem_dir), (MEMORY_CONFIG,), include_mock=dry)
            all_logs = main_logs + mem_logs
            figs = root / "figures" / "exploratory"
            note = "MOCK GAMES (dry run): not a result" if dry else None
            refs = price_paths.reference_lines(all_logs)
            price_paths.make_price_paths(price_paths.price_paths(all_logs), refs, figs / "price_paths.pdf", note)
            try:
                price_paths.make_price_shift(price_paths.price_shift(all_logs), figs / "price_shift.pdf", note,
                                             refs=refs)
            except ValueError as exc:
                log(f"[exploratory] price_shift.pdf not written: {exc}")
            res["outputs"] += [str(ex), str(figs)]
            log(f"[exploratory] memory arm -> {mem_dir}; tables -> {ex}; figures -> {figs}")
            if done("exploratory"):
                return res

        if o1:
            cfg = _derived(st, O1_NAME, swap_families(steps["core"]["families"], swap), seeds=st["o1_seeds"], budget_usd=st["o1_budget_usd"])
            if dry:
                cfg["out_dir"] = str(runs)
            run_cfg("o1", cfg)
            reproduce(runs, root / "results_o1", n_draws=n_draws, seed=seed, prereg_path=prereg_path,
                      configs=prereg_cfgs + (O1_NAME,), include_mock=dry, exclude_ids=superseded)
            res["outputs"].append(str(root / "results_o1"))
            log(f"[o1] option O1 (diagnostic, not the preregistered tables) -> {root / 'results_o1'}")
            res["steps"].append("o1")
        res["status"] = "done"
    except BudgetExceeded as exc:
        res["status"] = "budget_stop"
        log(f"BUDGET CAP HIT, stopped: {exc}. The game in progress was dropped (no log). Raise budget_usd in "
            "configs/run_all.yaml only with the owner's OK, then rerun to resume.")
    finally:
        res["spent_usd"] = tracker.total
    log(f"run_all: {res['status']}, steps {res['steps']}, spent {res['spent_usd']:.4f} USD")
    return res


EXIT = {"done": 0, "stopped": 0, "plan_b": 2, "budget_stop": 3}


def main(argv=None):
    load_env()  # repo-root .env, if any; never overrides the shell, never printed
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="mock client into a scratch folder (never runs/)")
    ap.add_argument("--root", default=None, help=f"base folder (default: the repo root real, {DEFAULT_DRY_ROOT} dry)")
    ap.add_argument("--configs-dir", default=str(CONFIGS))
    ap.add_argument("--exploratory", action="store_true", help="memory arm + sensitivity, monitor_view, price_paths")
    ap.add_argument("--o1", action="store_true", help="option O1 (seeds 6-10 on B, B_T, C, D), last")
    ap.add_argument("--stop-after", choices=STOP_AFTER, default=None)
    ap.add_argument("--dry-gate", choices=("pass", "fail"), default="pass")
    ap.add_argument("--allow-settings-mismatch", action="store_true",
                    help="run even if temperature or reasoning differ between pooled or matched steps")
    ap.add_argument("--n-draws", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args(argv)
    root = a.root or (DEFAULT_DRY_ROOT if a.dry else ROOT)
    try:
        res = run_pipeline(root, configs_dir=a.configs_dir, dry=a.dry, exploratory=a.exploratory, o1=a.o1,
                           stop_after=a.stop_after, dry_gate=a.dry_gate, n_draws=a.n_draws, seed=a.seed,
                           allow_settings_mismatch=a.allow_settings_mismatch)
    except RealRunRefused as exc:
        print(f"run_all REFUSED: {exc}")
        return 1
    return EXIT[res["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
