# AUDIT
Audits are done in a FRESH Claude session (new chat, no memory of writing the code) with the reviewer prompt in .claude/commands/audit.md, then read by the owner.
The author of the code must not audit it alone.

## Checklist (tick only with evidence, put the evidence in the log below)
- [ ] Every requirement in SPEC.md has a test or a MANUAL check, listed in TRACEABILITY.md
- [ ] Definitions in code match PREREGISTRATION.md word for word (verbal, behavioral, false positive, base rate)
- [x] B and B_T texts differ only by the label
- [ ] No hardcoded result, no expected value copied from the code's own output
- [x] No test was weakened, skipped or deleted since the last gate (check git diff of tests/)
- [ ] Mocks appear only in tests and dry runs; real configs use `mock: false`
- [ ] Every log in runs/ has model, family, seed, config hash, git commit, cost
- [ ] `reproduce` works with no API key and no network, twice with identical output
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
