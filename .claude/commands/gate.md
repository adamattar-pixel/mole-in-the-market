Run the self-gate for the CURRENT phase in PLAN.md:
1. Run the full test suite and show the complete output.
2. Update TRACEABILITY.md for the requirements of this phase.
3. Fill the AUDIT.md checklist honestly (leave unchecked what you cannot prove).
4. Run `git log -3 --format=fuller` and confirm author = committer = owner, no AI trailer.
5. List anything that deviates from SPEC.md or PREREGISTRATION.md.
If everything is green and no hard stop (H1 to H6 in CLAUDE.md) applies: write the result in PROGRESS.md, commit, `git push origin main`, tag gate-N, and continue with the next phase without waiting.
If something is red or a hard stop applies: fix it, or stop and ask.
