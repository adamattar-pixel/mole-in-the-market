"""tools/check_ops.py: every cited ops/ path exists, and every row of the ops/CLAIMS.md
"Active claims" table is well formed (format defined in ops/CLAIMS.md "Row format").
"""
import subprocess
import sys
from pathlib import Path

from tools import check_ops

ROOT = Path(__file__).resolve().parent.parent

HEADER = "| Who | Branch | Files / areas | Started | Expected end |\n|---|---|---|---|---|\n"


def make_repo(tmp_path, rows="", claims=None, files=None):
    (tmp_path / "ops").mkdir()
    if claims is None:
        claims = "# CLAIMS\n\n## Active claims\n" + HEADER + rows
    if claims is not False:
        (tmp_path / "ops" / "CLAIMS.md").write_text(claims, encoding="utf-8")
    for rel, text in (files or {}).items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return tmp_path


# ---- references ----

def test_clean_repo_has_no_errors(tmp_path):
    root = make_repo(tmp_path, files={"README.md": "See ops/CLAIMS.md for claims.\n"})
    assert check_ops.check(root) == []
    assert check_ops.main(["--root", str(root)]) == 0


def test_missing_ops_path_is_reported_with_file_and_line(tmp_path):
    root = make_repo(tmp_path, files={"CLAUDE.md": "line one\nread ops/NOPE.md first\n"})
    errors = check_ops.check(root)
    assert len(errors) == 1
    assert "CLAUDE.md:2" in errors[0] and "ops/NOPE.md" in errors[0]
    assert check_ops.main(["--root", str(root)]) == 1


def test_missing_path_in_python_and_yaml_is_reported(tmp_path):
    root = make_repo(tmp_path, files={"tools/x.py": "# see ops/GONE.md #3\n",
                                      "configs/a.yaml": "# ops/ALSO_GONE.md\n"})
    errors = check_ops.check(root)
    assert len(errors) == 2
    assert any("ops/GONE.md" in e for e in errors)
    assert any("ops/ALSO_GONE.md" in e for e in errors)


def test_trailing_punctuation_and_backticks_are_not_part_of_the_path(tmp_path):
    root = make_repo(tmp_path, files={"a.md": "See ops/CLAIMS.md. Or `ops/CLAIMS.md`, (ops/CLAIMS.md).\n"})
    assert check_ops.check(root) == []


def test_ops_directory_reference_is_valid(tmp_path):
    root = make_repo(tmp_path, files={"a.md": "Process docs live in ops/ and in ops/sub/.\n"})
    (root / "ops" / "sub").mkdir()
    assert check_ops.check(root) == []


def test_lookalikes_are_not_ops_references(tmp_path):
    root = make_repo(tmp_path, files={"a.md": "devops/x.md, https://example.org/ops/y.md, tools/check_ops.py, my_ops/z.md\n"})
    assert check_ops.check(root) == []


def test_tests_and_run_outputs_are_not_scanned(tmp_path):
    root = make_repo(tmp_path, files={"tests/test_x.py": "'ops/NOPE.md'\n",
                                      "runs/g.json": "ops/NOPE.md\n",
                                      "runs/notes.md": "ops/NOPE.md\n",
                                      ".git/x.md": "ops/NOPE.md\n"})
    assert check_ops.check(root) == []


def test_several_references_on_one_line_are_all_checked(tmp_path):
    root = make_repo(tmp_path, files={"a.md": "ops/CLAIMS.md and ops/MISSING_A.md and ops/MISSING_B.md\n"})
    errors = check_ops.check(root)
    assert len(errors) == 2


# ---- claims ----

def test_valid_rows_pass(tmp_path):
    rows = ("| Artem (Claude session 2) | wip/phase-4-artem-detectors | harness/detectors.py, tests/test_d.py | 2026-10-24 | 2026-10-25 |\n"
            "| Adam | wip/phase-7-adam-report | report/ | 2026-10-24 18:00 +08:00 | 2026-10-24 22:30 +08:00 |\n"
            "| Adam (Claude) | artem-ops-reorg | ops/ | 2026-10-24 10:00 UTC | 2026-10-24 10:00 UTC |\n")
    root = make_repo(tmp_path, rows=rows)
    assert check_ops.check(root) == []


def test_empty_claims_table_passes(tmp_path):
    assert check_ops.claim_errors("## Active claims\n" + HEADER) == []


def test_row_with_missing_cell_fails(tmp_path):
    root = make_repo(tmp_path, rows="| Artem | wip/phase-4-artem-x | viz/ | 2026-10-24 |\n")
    errors = check_ops.check(root)
    assert len(errors) == 1 and "CLAIMS.md" in errors[0]


def test_row_with_extra_cell_fails():
    text = "## Active claims\n" + HEADER + "| A | b | c | 2026-10-24 | 2026-10-24 | extra |\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_row_with_empty_cell_fails():
    text = "## Active claims\n" + HEADER + "| Artem |  | viz/ | 2026-10-24 | 2026-10-25 |\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_branch_with_space_fails():
    text = "## Active claims\n" + HEADER + "| Artem | my branch | viz/ | 2026-10-24 | 2026-10-25 |\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_bad_dates_fail():
    for start, end in [("24/10/2026", "2026-10-25"), ("2026-10-24", "tomorrow"),
                       ("2026-10-24 9:00", "2026-10-25"), ("2026-13-01", "2026-13-02"),
                       ("2026-10-24 25:00", "2026-10-25")]:
        text = "## Active claims\n" + HEADER + f"| Artem | wip/phase-4-a-b | viz/ | {start} | {end} |\n"
        assert len(check_ops.claim_errors(text)) == 1, (start, end)


def test_end_before_start_fails():
    text = "## Active claims\n" + HEADER + "| Artem | wip/phase-4-a-b | viz/ | 2026-10-25 | 2026-10-24 |\n"
    assert len(check_ops.claim_errors(text)) == 1
    text = "## Active claims\n" + HEADER + "| Artem | wip/phase-4-a-b | viz/ | 2026-10-24 18:00 | 2026-10-24 17:59 |\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_each_bad_row_is_reported():
    rows = ("| Artem | wip/phase-4-a-b | viz/ | 2026-10-25 | 2026-10-24 |\n"
            "| ok | wip/phase-4-a-b | viz/ | 2026-10-24 | 2026-10-24 |\n"
            "| bad | row |\n")
    assert len(check_ops.claim_errors("## Active claims\n" + HEADER + rows)) == 2


def test_wrong_header_fails():
    text = "## Active claims\n| Who | Branch | Files | Started | End |\n|---|---|---|---|---|\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_missing_active_claims_section_fails():
    assert len(check_ops.claim_errors("# CLAIMS\nno table here\n")) == 1


def test_tables_outside_active_claims_are_ignored():
    text = ("## Row format\n| not | a | claim |\n\n## Active claims\n" + HEADER +
            "\n## Later section\n| also | ignored |\n")
    assert check_ops.claim_errors(text) == []


def test_missing_claims_file_fails(tmp_path):
    root = make_repo(tmp_path, claims=False)
    errors = check_ops.check(root)
    assert len(errors) == 1 and "CLAIMS.md" in errors[0]


# ---- the real repo and the CLI ----

def test_real_repo_passes():
    assert check_ops.check(ROOT) == []


def test_cli_exit_codes(tmp_path):
    (tmp_path / "good").mkdir()
    (tmp_path / "bad").mkdir()
    good = make_repo(tmp_path / "good", files={"a.md": "ops/CLAIMS.md\n"})
    bad = make_repo(tmp_path / "bad", files={"a.md": "ops/NOPE.md\n"})

    def run(root):
        return subprocess.run([sys.executable, "-m", "tools.check_ops", "--root", str(root)],
                              cwd=ROOT, capture_output=True, text=True)
    ok, ko = run(good), run(bad)
    assert ok.returncode == 0, ok.stderr
    assert ko.returncode == 1
    assert "ops/NOPE.md" in ko.stdout + ko.stderr
