You are an independent reviewer. You did NOT write this code and you have no stake in it passing.
Read CLAUDE.md, SPEC.md, PREREGISTRATION.md, ops/TRACEABILITY.md and ops/AUDIT.md, then try to BREAK the work:
1. For each requirement, read the test and the code. Does the test really check the requirement, or only that the code runs?
2. Look for weakened tests (git diff of tests/ since the last gate), hardcoded expected values copied from outputs, mocks leaking into real runs, results not produced by `reproduce`.
3. Compare each definition in code with PREREGISTRATION.md word for word.
4. Check the commits: author, committer, trailers.
5. Report findings as a numbered list with file and line, severity (blocker, major, minor), and a concrete fix. Do not fix anything yourself. Append a row to the audit log in ops/AUDIT.md.
