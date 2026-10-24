# AUDIT
Audits are done in a FRESH Claude session (new chat, no memory of writing the code) with the reviewer prompt in .claude/commands/audit.md, then read by the owner.
The author of the code must not audit it alone.

## Checklist (tick only with evidence, put the evidence in the log below)
- [ ] Every requirement in SPEC.md has a test or a MANUAL check, listed in TRACEABILITY.md
- [ ] Definitions in code match PREREGISTRATION.md word for word (verbal, behavioral, false positive, base rate)
- [ ] B and B_T texts differ only by the label
- [ ] No hardcoded result, no expected value copied from the code's own output
- [ ] No test was weakened, skipped or deleted since the last gate (check git diff of tests/)
- [ ] Mocks appear only in tests and dry runs; real configs use `mock: false`
- [ ] Every log in runs/ has model, family, seed, config hash, git commit, cost
- [ ] `reproduce` works with no API key and no network, twice with identical output
- [ ] Frozen items unchanged since `prereg-frozen` (git diff against the tag)
- [ ] Every number in the report appears in the `reproduce` output
- [ ] No secrets in the repo or history
- [ ] Commits: author and committer are the owner, no AI trailer
- [ ] THIRD_PARTY.md lists all reused code and borrowed ideas; preexisting code isolated by the `preexisting-baseline` tag
- [ ] Appendix "Limitations and Dual-Use / Ethical Considerations" present

## Audit log
| Date | Phase | Reviewer session | Findings | Fixed? |
|---|---|---|---|---|
