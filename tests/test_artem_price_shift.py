"""Price paths small multiples (default layout) and the price shift figure (tools/price_paths.py).

EXPLORATORY, descriptive, zero cost. Hand-built logs: spy_start 2, Nash 10, monopoly = deal 20, behavioral
window 3 (PREREGISTRATION.md), so the "do" window is rounds 3, 4, 5. Expected shifts worked out by hand.
"""
import pytest

from harness.conditions import CONDITIONS
from helpers3 import full_log, write_logs
from tools import price_paths as pp

PRE = [(10.0, 10.0)] * 2  # rounds 1, 2 (ignored by the shift)


def g(cond, fam, seed, window, memory=False, extra=((10.0, 10.0),)):
    log = full_log(cond, fam, seed, PRE + list(window) + list(extra), spy_start=2)
    if memory:
        log["memory"] = True
        log["game_id"] = f"espion_mem__{fam}__{cond}__s{seed}"
    return log


# fx: A s1 window mean 10, A s2 window mean 12 -> reference mean 11
# B s1 window (20,18),(19,19),(18,20) -> 19, 19, 19 -> 19 | B s2 16 -> B mean 17.5 -> shift 6.5
# B s3 has only 4 rounds (window incomplete) -> excluded, so n stays 2
# C s1 window mean 11 -> shift 0
# fy: A s1, s2 all 10; D s1, s2 all 13 -> shift 3 with zero spread, so the interval is exactly (3, 3)
def logs():
    return [
        g("A", "fx", 1, [(10.0, 10.0)] * 3), g("A", "fx", 2, [(12.0, 12.0)] * 3),
        g("B", "fx", 1, [(20.0, 18.0), (19.0, 19.0), (18.0, 20.0)]), g("B", "fx", 2, [(16.0, 16.0)] * 3),
        full_log("B", "fx", 3, PRE + [(30.0, 30.0)] * 2, spy_start=2),
        g("C", "fx", 1, [(11.0, 11.0)] * 3),
        g("A", "fy", 1, [(10.0, 10.0)] * 3), g("A", "fy", 2, [(10.0, 10.0)] * 3),
        g("D", "fy", 1, [(13.0, 13.0)] * 3), g("D", "fy", 2, [(12.0, 14.0)] * 3),
    ]


def test_window_mean_both_firms_and_incomplete_window():
    assert pp.window_mean(logs()[2], 3, 5) == pytest.approx(19.0)
    assert pp.window_mean(logs()[4], 3, 5) is None


def test_shift_point_values_by_hand():
    s = pp.price_shift(logs(), n_boot=500, seed=0)
    assert s["fx"]["B"]["shift"] == pytest.approx(6.5)
    assert s["fx"]["B"]["n"] == 2 and s["fx"]["B"]["n_ref"] == 2
    assert s["fx"]["B"]["ref"] == "A"
    assert s["fx"]["C"]["shift"] == pytest.approx(0.0)
    assert s["fy"]["D"]["shift"] == pytest.approx(3.0)
    assert "A" not in s["fx"]  # No spy is the reference, never its own row


def test_bootstrap_interval_bounds_and_degenerate_case():
    s = pp.price_shift(logs(), n_boot=500, seed=0)
    b = s["fx"]["B"]
    # resampled B mean lies in [16, 19], reference mean in [10, 12] -> shift in [4, 9]
    assert 4.0 <= b["lo"] < b["shift"] < b["hi"] <= 9.0
    assert s["fy"]["D"]["lo"] == pytest.approx(3.0) and s["fy"]["D"]["hi"] == pytest.approx(3.0)


def test_bootstrap_is_seeded_and_deterministic():
    assert pp.price_shift(logs(), n_boot=300, seed=7) == pp.price_shift(logs(), n_boot=300, seed=7)


def test_no_reference_means_no_shift_row():
    only_b = [x for x in logs() if x["family"] == "fx" and x["condition"] == "B"]
    assert pp.price_shift(only_b, n_boot=50, seed=0) == {"fx": {}}


def test_memory_arm_uses_memory_no_spy_when_present():
    # A_mem window 14, B_mem window 15 -> shift 1 against A_mem (same longer prompt)
    with_ref = logs() + [g("A", "fx", 1, [(14.0, 14.0)] * 3, memory=True),
                         g("B", "fx", 1, [(15.0, 15.0)] * 3, memory=True)]
    s = pp.price_shift(with_ref, n_boot=50, seed=0)
    assert s["fx"]["B_mem"]["ref"] == "A_mem"
    assert s["fx"]["B_mem"]["shift"] == pytest.approx(1.0)
    assert "A_mem" not in s["fx"]
    # without A_mem the memory arm falls back to the frozen No spy (reference mean 11) -> 15 - 11 = 4
    without = logs() + [g("B", "fx", 1, [(15.0, 15.0)] * 3, memory=True)]
    s2 = pp.price_shift(without, n_boot=50, seed=0)
    assert s2["fx"]["B_mem"]["ref"] == "A"
    assert s2["fx"]["B_mem"]["shift"] == pytest.approx(4.0)


def test_shift_refuses_mixed_spy_rounds_in_a_family():
    bad = logs() + [full_log("E", "fx", 1, [(10.0, 10.0)] * 9, spy_start=5)]
    with pytest.raises(ValueError):
        pp.price_shift(bad, n_boot=10, seed=0)


def test_grid_columns_and_reference_arm():
    lg = logs() + [g("B", "fx", 1, [(15.0, 15.0)] * 3, memory=True)]
    paths = pp.price_paths(lg)
    assert pp.grid_columns(paths) == ["B", "C", "D", "B_mem"]
    assert pp.reference_arm("B", paths["fx"]) == "A"
    assert pp.reference_arm("B_mem", paths["fx"]) == "A"
    lg2 = lg + [g("A", "fx", 1, [(14.0, 14.0)] * 3, memory=True)]
    paths2 = pp.price_paths(lg2)
    assert pp.grid_columns(paths2) == ["B", "C", "D", "B_mem"]  # A_mem is a reference, not a column
    assert pp.reference_arm("B_mem", paths2["fx"]) == "A_mem"


def test_grid_is_default_and_labels_are_full_names(tmp_path):
    lg = logs()
    labels = pp.make_price_paths(pp.price_paths(lg), pp.reference_lines(lg), tmp_path / "g.pdf")
    for name in ("No spy", "Direct offer", "Hint", "Harmless request"):
        assert name in labels
    assert not set(labels) & set(CONDITIONS)


def test_overlay_layout_still_available_and_deterministic(tmp_path):
    lg = logs()
    out = tmp_path / "o.pdf"
    labels = pp.make_price_paths(pp.price_paths(lg), pp.reference_lines(lg), out, layout="overlay")
    first = out.read_bytes()
    assert first.startswith(b"%PDF") and "Direct offer" in labels
    pp.make_price_paths(pp.price_paths(lg), pp.reference_lines(lg), out, layout="overlay")
    assert out.read_bytes() == first
    with pytest.raises(ValueError):
        pp.make_price_paths(pp.price_paths(lg), pp.reference_lines(lg), out, layout="nope")


def test_shift_pdf_deterministic_full_names(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    out = tmp_path / "price_shift.pdf"
    labels = pp.make_price_shift(pp.price_shift(logs(), n_boot=200, seed=0), out)
    first = out.read_bytes()
    assert first.startswith(b"%PDF")
    assert b"CreationDate" not in first and b"ModDate" not in first
    assert {"Direct offer", "Hint", "Harmless request"} <= set(labels)
    assert not set(labels) & set(CONDITIONS)
    pp.make_price_shift(pp.price_shift(logs(), n_boot=200, seed=0), out)
    assert out.read_bytes() == first


def test_cli_writes_both_figures_and_accepts_layout(tmp_path):
    runs = tmp_path / "runs"
    write_logs(logs(), runs)
    pp.main([str(runs), "--out-dir", str(tmp_path / "a"), "--include-mock", "--all-configs"])
    assert (tmp_path / "a" / "price_paths.pdf").exists() and (tmp_path / "a" / "price_shift.pdf").exists()
    pp.main([str(runs), "--out-dir", str(tmp_path / "b"), "--include-mock", "--all-configs",
             "--layout", "overlay"])
    assert (tmp_path / "b" / "price_paths.pdf").exists()
