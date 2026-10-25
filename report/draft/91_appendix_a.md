# Appendix A. Limitations and Dual-Use / Ethical Considerations

## A.1 What the results do and do not establish

**Small n and a ceiling.** Each cell has n = 5. Every Llama rate is 0/5 (95% CI 0.00-0.43) or 5/5 (0.57-1.00). We cannot detect any difference between conditions, so "not supported" for H1 and H4 does not mean "no effect". <!-- src: results/tables.md -->

**One fully tested family.** The preregistered core is Llama 3.3 70B only. This is a declared deviation from the planned two families. Haiku 4.5 failed the positive control, and the Sonnet 4.5 fallback stopped after 8 of its pilot games. <!-- src: run_all_deviations.json; RESULTS_SUMMARY.md Deviations -->

**Declared deviations.** We re-pinned Llama from one provider to another after timeouts and re-ran the affected logs. We dropped the Sonnet fallback after it was billed to credits. The credit cap ended the runs. Five locked-test fixes were approved after the fact. The frozen preregistration files still list no deviations; we did not edit them. Section 3 lists each one.

**Design limits.** Sellers are memoryless after the offer round. The offer contains the deal price, so "do" includes anchoring on that number. "Say" is a forced label (accept, decline or no_message), not evidence of agreement. The base rate is not time-matched, so its p-value is descriptive. D3 is not testable on flat prices.

**Arms not run.** The credit cap stopped the message monitor (H6), the ethics sentence (H7), the memory arm, the gpt-oss THINK arm and the extra replicates. "0/0 (n/a)" in the defense tables means not run, not zero. <!-- src: results/defenses.md; RESULTS_SUMMARY.md -->

**Seeds.** We treat seeds as replicates. Providers may ignore the seed, and most games are flat.

**THINK.** The showcase has n = 2 games, one model and one seed. A keyword coder with known misfires labels the traces, and we corrected it by reading them. Reasoning traces are not faithful evidence of why a model acted.

## A.2 Dual-use and ethics

**The offers are plain.** We used short, fixed texts and did not optimize them for persuasion.

**What we publish.** We publish rates, codes and excerpts of one sentence at most. We do not publish raw reasoning traces. One incident: raw Qwen traces were committed and pushed to a work branch by mistake. They were untracked in the next commit but remain in that branch's history. <!-- src: THINK_ARM.md "Publication note" -->

**Evasion risk.** Our data show a pattern a colluding agent could use: say "no" and keep the price high. A monitor that reads only messages would miss it. Our monitor rule is public, so it can be evaded. We see this as a reason to audit prices against a baseline, not messages alone.

**No human subjects.** The study uses simulated sellers only. It involves no humans, no real market and no personal data.
