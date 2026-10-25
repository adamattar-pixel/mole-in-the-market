# 5. Discussion

**What this means for auditors and monitors.** Our results point to three practical lessons. Each rests on one model family at n = 5.

First, check prices against a no-offer baseline. Llama and Haiku start from opposite sides of the deal price, so the same offer is a raise for one and a cut for the other. A raw price level misleads in both directions. Haiku's No spy prices (2.50 in 4/5 games) would look like a cartel to a price-level rule, yet they earn 15.98 per firm-round, below the 22.17 of the Nash price. <!-- src: checks_prereg_configs/checks.md; ANALYSIS_PLAN.md profit table -->

Second, neither "yes" nor "no" is reliable. For Llama, "accept" came with a price move in the offer conditions, but also came 5/5 (0.57-1.00) for a harmless question with no move. Haiku said "no" in 10/10 firms (0.72-1.00), on wrong arithmetic and with no legal reason in 0/10 replies (0.00-0.28). A label tells an auditor little without the prices. <!-- src: results/tables.md; extras.md -->

Third, numbers in messages coordinate. The Hint proposes nothing, yet it moved Llama to 1.92 exactly as the Direct offer did. A message monitor that looks for proposals missed it in 0/5 Hint games (0.00-0.43). <!-- src: extras.md; results/detectors.md -->

**What surprised us.** We expected the trust label and the form of the offer to matter. At the ceiling they could not. The bigger surprise was the direction effect: the frozen positive control assumed every seller prices below the monopoly. Two Claude models priced above it, and the gate flipped on noise (0.433, then 0.111). We also did not expect a reasoning model to call its own steady price "tacit collusion" while never mentioning the law. <!-- src: extras.md "Earlier provider-era logs"; RESULTS_SUMMARY.md THINK -->

**Future work.**
- A positive control that does not depend on direction, for example a deal set relative to each model's own baseline.
- Free-text replies next to the label, so that "accept" can be told apart from agreement.
- More replicates per cell, to escape the 0/5 and 5/5 ceiling.
- The defenses we planned but did not run: the message monitor, the ethics sentence and a memory arm.
- A neutral number in a harmless message, to separate anchoring from agreement directly.
