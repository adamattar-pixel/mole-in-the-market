# AUDIT
Audits are done in a FRESH Claude session (new chat, no memory of writing the code) with the reviewer prompt in .claude/commands/audit.md, then read by the owner.
The author of the code must not audit it alone.

## Checklist (tick only with evidence, put the evidence in the log below)
- [ ] Every requirement in docs/SPEC.md has a test or a MANUAL check, listed in TRACEABILITY.md
- [ ] Definitions in code match PREREGISTRATION.md word for word (verbal, behavioral, false positive, base rate)
- [x] B and B_T texts differ only by the label
- [ ] No hardcoded result, no expected value copied from the code's own output
- [x] No test was weakened, skipped or deleted since the last gate (check git diff of tests/)
- [ ] Mocks appear only in tests and dry runs; real configs use `mock: false`
- [ ] Every log in runs/ has model, family, seed, config hash, git commit, cost
- [x] `reproduce` works with no API key and no network, twice with identical output
- [ ] Frozen items unchanged since `prereg-frozen` (git diff against the tag)
- [ ] Every number in the report appears in the `reproduce` output
- [x] No secrets in the repo or history
- [x] Commits: author and committer are the owner, no AI trailer
- [ ] THIRD_PARTY.md lists all reused code and borrowed ideas; preexisting code isolated by the `preexisting-baseline` tag
- [ ] Appendix "Limitations and Dual-Use / Ethical Considerations" present
- [ ] Viz page reads only the exports of `reproduce` (viz/data/)
- [ ] No data from viz/demo/ in runs/, labels.csv or the report
- [ ] Demo banner present when meta.synthetic is true
- [ ] viz/data/games.csv consistent with labels.csv
- [ ] Viz page makes no network request

## Audit log
| Date | Phase | Reviewer session | Findings | Fixed? |
|---|---|---|---|---|
| 2026-10-24 | 2 (self-gate) | author session, NOT an independent audit | Ticked with evidence: B/B_T (test_R04_real_prereg_B_BT_differ_only_by_label green); tests not weakened (`git diff 5c52047 -- tests/` empty); no secrets (`git log -p --all` grep for key patterns = 0, .env not tracked); commits author = committer = Adam Attar, 0 AI trailers. Audit pass 1 in a fresh session: NOT RUN, pending owner (/audit in a new chat) | - |
| 2026-10-24 | 3 (self-gate) | author session, NOT an independent audit | Ticked with evidence: reproduce without key/network and twice identical (test_R15_no_key_no_network, test_R15_run_twice_identical green). Rechecked: `git diff c5adce2 HEAD -- tests/` = 1 line (approved test(fix) cef08e3, D3); phase 2 test files unchanged since 5c52047; no secrets; author = committer = owner, 0 trailers. Not ticked: real configs/runs do not exist yet. Audit pass 2 in a fresh session: NOT RUN, pending owner | - |
| 2026-10-24 | 2 and 3 (audit passes 1 and 2) | independent fresh session (Artem), report docs/team-artem/AUDIT_PASS_1_2.md, audited ef5bccd | pytest: 229 passed, 25 red = locked R24/R25 only (expected). reproduce keyless, twice byte-identical (dry data). Prereg unchanged since tag; tests unweakened (only approved cef08e3); 41/41 commits author=committer=Adam, 0 trailers, 0 secrets. Definitions match prereg word for word. BLOCKER 1: agents are memoryless, offer and own reply absent from prompts after spy_start (runner.py:111, agent.py:42), so the say-do gap is confounded. MAJOR: 2 base rate not time-matched and p ignores sampling; 3 reproduce pools smoke+pilot and never filters mock; 4 tag preexisting-baseline missing; 5 offer leaks the deal price (anchoring); 6 n=5 Wilson width up to 0.65; 7 binary do may hit a ceiling (tacit collusion); 8 spy_start=8 drift; 9 no temperature, seed not honored. 6 minors | no (report only) |
| 2026-10-24 | 4 (pre-run review of R28-R36 and Artem's additions) | independent fresh session (Artem), report docs/team-artem/REVIEW_ARTEM_DIFF.md | 0 blockers, 4 majors: M1 budget cap reset on rerun, M2 resume mixes settings, M3 run_all drops per-step settings, M4 defenses tables missing from reproduce (R30); 4 minors | Yes: M1-M4 and m2, m4 fixed tests-first (see 'Fixes applied' in the report); m1, m3 open |
