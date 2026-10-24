"""Gap tests for tools/check_ops.py found by the mutation check (separate from the locked file)."""
from tools import check_ops

HEADER = "| Who | Branch | Files / areas | Started | Expected end |\n|---|---|---|---|---|\n"


def test_empty_who_fails():
    text = "## Active claims\n" + HEADER + "|  | wip/phase-4-a-b | viz/ | 2026-10-24 | 2026-10-25 |\n"
    assert len(check_ops.claim_errors(text)) == 1


def test_empty_areas_fails():
    text = "## Active claims\n" + HEADER + "| Artem | wip/phase-4-a-b |  | 2026-10-24 | 2026-10-25 |\n"
    assert len(check_ops.claim_errors(text)) == 1
