"""THINK arm view - EXPLORATORY, not preregistered (docs/team-artem/THINK_ARM.md).

For each THINK game (log field think true) and firm: the say (response_to_message), the do (price) and a
HEURISTIC keyword coding of the raw reasoning trace, in the offer round (spy_start) and the next 3 rounds.
The coder is a transparent rule with no model call; its keyword lists are in configs/exploratory/
espion_think_coder.yaml. Say and do per firm use the preregistered definitions (harness/metrics.py), applied
descriptively. A trace is what the model wrote, not proof of why it acted (CoT faithfulness, THINK_ARM.md).

Outputs in out_dir: think_view.csv (one row per game, firm and round), think_view.md (per game and firm),
think_excerpts.md (offer round, reply, first 400 characters of the trace, next 3 prices), think_traces.md
(offer round and next 3 rounds, at most 1,500 characters of trace per firm) and traces/<game_id>.json (the
full traces of those rounds, sidecar). Dual-use: publish codes and a few short excerpts only.

Usage: python -m tools.think_view runs_exploratory/think results_exploratory/think [--coder PATH]
"""
import argparse
import csv
import json
import re
from pathlib import Path

import yaml

from harness.metrics import behavioral_acceptance_firm, verbal_acceptance_firm
from harness.runlog import load_logs

CODER_PATH = Path(__file__).resolve().parent.parent / "configs" / "exploratory" / "espion_think_coder.yaml"
CODES = ("mentions_deal", "mentions_legality_or_antitrust", "mentions_rival_trust", "intends_to_follow",
         "intends_to_defect")
WINDOW = 3  # rounds after the offer round
NOTE = ("EXPLORATORY, not preregistered: THINK arm. Trace codes come from a heuristic keyword rule "
        "(configs/exploratory/espion_think_coder.yaml), not from a model; a trace is not proof of why a model acted.")
COLUMNS = ("game_id", "family", "model", "condition", "seed", "firm", "round", "rel_round", "price",
           "response_to_message", "say_firm", "do_firm", "has_trace") + CODES
_PUNCT = ".,;:!?\"()[]{}*_"


def load_coder(path=None):
    c = yaml.safe_load(Path(path or CODER_PATH).read_text(encoding="utf-8"))
    if not isinstance(c, dict) or c.get("heuristic") is not True:
        raise ValueError("the THINK coder config must say heuristic: true")
    codes = c.get("codes") or {}
    for k in CODES:
        if not codes.get(k) or not all(isinstance(w, str) and w.strip() for w in codes[k]):
            raise ValueError(f"the THINK coder has no keyword list for {k}")
    neg = c.get("negatable", [])
    if any(k not in CODES for k in neg):
        raise ValueError(f"negatable codes must be among {CODES}: {neg}")
    w = c.get("negation_window_words", 3)
    if isinstance(w, bool) or not isinstance(w, int) or w < 0:
        raise ValueError("negation_window_words must be an integer >= 0")
    return {"heuristic": True, "codes": {k: list(codes[k]) for k in CODES},
            "negations": [str(x).lower() for x in c.get("negations", [])], "negatable": list(neg),
            "negation_window_words": w}


def _pattern(phrase):
    words = [re.escape(w) for w in phrase.lower().split()]
    return re.compile(r"(?<![\w'])" + r"\s+".join(words) + r"(?![\w'])", flags=re.IGNORECASE)


def _negated(text, start, coder):
    n = coder.get("negation_window_words", 3)
    before = [w.strip(_PUNCT).lower() for w in text[:start].split()][-n:] if n else []
    return any(w in coder.get("negations", []) for w in before)


def code_trace(text, coder):
    """{code: 1 or 0}, or {code: None} when there is no trace (None)."""
    if text is None:
        return {k: None for k in CODES}
    text = str(text).replace("’", "'")
    out = {}
    for k in CODES:
        hit = 0
        for phrase in coder["codes"][k]:
            for m in _pattern(phrase).finditer(text):
                if k in coder.get("negatable", []) and _negated(text, m.start(), coder):
                    continue
                hit = 1
                break
            if hit:
                break
        out[k] = hit
    return out


def _check_think(logs):
    bad = [g["game_id"] for g in logs if g.get("think") is not True]
    if bad:
        raise ValueError(f"think_view reads THINK arm logs only (think: true), not: {bad[:3]}")


def _firms(g):
    return sorted(g["rounds"][0]["firms"]) if g["rounds"] else []


def _window(g):
    by_round = {r["round"]: r for r in g["rounds"]}
    return [(t, by_round[t]) for t in range(g["spy_start"], g["spy_start"] + WINDOW + 1) if t in by_round]


def _trace(f):
    return (f.get("provenance") or {}).get("reasoning_text")


def think_rows(logs, coder=None):
    _check_think(logs)
    coder = coder or load_coder()
    rows = []
    for g in sorted(logs, key=lambda x: x["game_id"]):
        for fid in _firms(g):
            say, do = int(verbal_acceptance_firm(g, fid)), int(behavioral_acceptance_firm(g, fid))
            for t, rnd in _window(g):
                f = rnd["firms"][fid]
                trace = _trace(f)
                row = {"game_id": g["game_id"], "family": g["family"], "model": (g.get("models") or {}).get(fid),
                       "condition": g["condition"], "seed": g["seed"], "firm": fid, "round": t,
                       "rel_round": t - g["spy_start"], "price": f["price"],
                       "response_to_message": f["response_to_message"], "say_firm": say, "do_firm": do,
                       "has_trace": int(bool(trace))}
                row.update(code_trace(trace, coder))
                rows.append(row)
    return rows


def excerpts(logs, n_chars=400):
    _check_think(logs)
    out = []
    for g in sorted(logs, key=lambda x: x["game_id"]):
        by_round = {r["round"]: r for r in g["rounds"]}
        s = g["spy_start"]
        for fid in _firms(g):
            f = by_round[s]["firms"][fid] if s in by_round else {}
            out.append({"game_id": g["game_id"], "family": g["family"], "condition": g["condition"],
                        "seed": g["seed"], "firm": fid, "offer_round": s,
                        "response_to_message": f.get("response_to_message"), "reply": f.get("reply"),
                        "trace_excerpt": (_trace(f) or "")[:n_chars],
                        "next_prices": [by_round[t]["firms"][fid]["price"] for t in range(s + 1, s + 1 + WINDOW)
                                        if t in by_round]})
    return out


def trace_excerpt(g, firm, cap=1500):
    """The traces of the offer round and the next 3 rounds for one firm, labelled by round, at most cap chars."""
    parts = []
    for t, rnd in _window(g):
        trace = _trace(rnd["firms"][firm])
        parts.append(f"[round {t}] " + (trace if trace else "(no trace)"))
    return "\n".join(parts).replace("```", "'''")[:cap]


def _fmt(v):
    return "" if v is None else v


def write_csv(rows, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(f"# {NOTE}\n")
        w = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: _fmt(r[k]) for k in COLUMNS})


def table_md(rows):
    lines = ["# THINK arm - EXPLORATORY, not preregistered", "", NOTE, "",
             f"Rounds: the offer round (spy_start) and the next {WINDOW}. Say and do per firm: preregistered "
             "definitions, applied descriptively. Each code cell: rounds flagged / rounds with a trace.", "",
             "| Game | Firm | Condition | Model | Say | Do | Rounds with trace | " + " | ".join(CODES) + " |",
             "|" + "---|" * (7 + len(CODES))]
    keys = []
    for r in rows:
        if (r["game_id"], r["firm"]) not in keys:
            keys.append((r["game_id"], r["firm"]))
    for gid, fid in keys:
        rr = [r for r in rows if r["game_id"] == gid and r["firm"] == fid]
        n = sum(r["has_trace"] for r in rr)
        cells = [f"{sum(r[c] or 0 for r in rr)}/{n}" for c in CODES]
        lines.append(f"| {gid} | {fid} | {rr[0]['condition']} | {rr[0]['model']} | {rr[0]['say_firm']} | "
                     f"{rr[0]['do_firm']} | {n}/{len(rr)} | " + " | ".join(cells) + " |")
    if not keys:
        lines.append("No THINK games.")
    return "\n".join(lines) + "\n"


def excerpts_md(items):
    lines = ["# THINK arm excerpts - EXPLORATORY, not preregistered", "", NOTE,
             "Dual-use: keep this file internal; publish codes and a few short excerpts only.", ""]
    for e in items:
        lines += [f"## {e['game_id']}, firm {e['firm']}", "",
                  f"- Offer round {e['offer_round']}, response_to_message: {e['response_to_message']}",
                  f"- Reply: `{(e['reply'] or '').replace('`', chr(39))}`",
                  f"- Next {WINDOW} prices: {e['next_prices']}", "", "```text",
                  e["trace_excerpt"].replace("```", "'''") or "(no trace)", "```", ""]
    return "\n".join(lines) + "\n"


def write_outputs(logs, out_dir, coder=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = think_rows(logs, coder)
    write_csv(rows, out_dir / "think_view.csv")
    (out_dir / "think_view.md").write_text(table_md(rows), encoding="utf-8")
    (out_dir / "think_excerpts.md").write_text(excerpts_md(excerpts(logs)), encoding="utf-8")
    return [out_dir / "think_view.csv", out_dir / "think_view.md", out_dir / "think_excerpts.md"]


def export_traces(logs, out_dir, cap=1500):
    """Sidecar traces/<game_id>.json with the full traces of the offer round and the next 3 rounds, plus
    think_traces.md with at most cap characters of trace per firm."""
    _check_think(logs)
    out_dir = Path(out_dir)
    (out_dir / "traces").mkdir(parents=True, exist_ok=True)
    paths = []
    lines = ["# THINK traces - EXPLORATORY, not preregistered", "", NOTE,
             f"Offer round and the next {WINDOW} rounds; at most {cap} characters per firm here, the full traces "
             "are in traces/<game_id>.json. Dual-use: keep internal; publish codes and a few short excerpts only.", ""]
    for g in sorted(logs, key=lambda x: x["game_id"]):
        firms = {}
        for fid in _firms(g):
            firms[fid] = [{"round": t, "price": rnd["firms"][fid]["price"],
                           "response_to_message": rnd["firms"][fid]["response_to_message"],
                           "reply": rnd["firms"][fid].get("reply"), "reasoning_text": _trace(rnd["firms"][fid])}
                          for t, rnd in _window(g)]
            lines += [f"## {g['game_id']}, firm {fid} ({(g.get('models') or {}).get(fid)})", "", "```text",
                      trace_excerpt(g, fid, cap), "```", ""]
        side = out_dir / "traces" / f"{g['game_id']}.json"
        side.write_text(json.dumps({"note": NOTE, "game_id": g["game_id"], "family": g["family"],
                                    "condition": g["condition"], "seed": g["seed"], "models": g.get("models"),
                                    "spy_start": g["spy_start"], "firms": firms}, sort_keys=True, indent=1) + "\n",
                        encoding="utf-8")
        paths.append(side)
    md = out_dir / "think_traces.md"
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return paths + [md]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs_dir", nargs="?", default="runs_exploratory/think")
    ap.add_argument("out_dir", nargs="?", default="results_exploratory/think")
    ap.add_argument("--coder", default=None, help="keyword coder config (default: espion_think_coder.yaml)")
    a = ap.parse_args(argv)
    logs = load_logs(a.runs_dir)
    coder = load_coder(a.coder)
    write_outputs(logs, a.out_dir, coder)
    export_traces(logs, a.out_dir)
    print(f"think_view: {len(logs)} THINK games -> {a.out_dir} (EXPLORATORY, heuristic codes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
