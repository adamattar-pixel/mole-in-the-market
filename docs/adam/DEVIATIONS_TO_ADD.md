# Declared deviations: lines for the owner to add (QUESTIONS #32, decision D29)
The Deviations sections of PREREGISTRATION.md (line 61) and PREREGISTRATION_ADDENDUM.md (line 48) still say
"(none)". Editing a frozen file is hard stop H6, so Claude did not touch them. If the owner (Artem) agrees, he
replaces "(none)" in PREREGISTRATION.md with the three lines below, in his own commit. The addendum needs no
line: none of its parts was run (monitor, ethics) and its definitions were used as frozen.
Facts below come from ops/QUESTIONS.md #24, #26, #27 and run_all_deviations.json.

```
- 2026-10-24 (QUESTIONS #26): Llama 3.3 70B re-pinned from the Novita provider (bf16) to CoreWeave (fp16) after Novita timed out on every call; the Novita-era smoke and pilot logs were archived to runs_archive/novita_v2/ (not deleted) and re-run, so each family has one provider across all scored logs.
- 2026-10-24 (QUESTIONS #27): the Anthropic family (Claude Haiku 4.5) failed the E gate (pilot effect 0.111 < 0.25); its preregistered fallback (Sonnet 4.5) could not finish within the credit cap; 8 partial Sonnet pilot games are archived in runs_archive/sonnet_fb_partial/ (exploratory only).
- 2026-10-24 (QUESTIONS #24, run_all_deviations.json): the core ran on 1 of the 2 preregistered families (Llama only) with `tools.run_all --continue-passing-families` instead of the plan B stop; the 10 Haiku pilot games are excluded from the preregistered tables.
```

The report must state the same three deviations whether or not these lines are added (report/SUBMISSION_CHECKLIST.md).
