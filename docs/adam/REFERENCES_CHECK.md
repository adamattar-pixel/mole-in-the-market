# References check (2026-10-25) - report/SKELETON.md, "Citations (10)" table
Each URL was fetched on 2026-10-25 and the page's title, authors and year compared with the skeleton entry.
Read only: report/SKELETON.md is not changed.

| # | Skeleton entry | Page says | Status |
|---|---|---|---|
| 1 | Calvano et al. 2020, AER | "Artificial Intelligence, Algorithmic Pricing, and Collusion", Calvano, Calzolari, Denicolò, Pastorello, American Economic Review 110, 2020 | OK |
| 2 | Fish, Gonczarowski, Shorrer 2024 | arXiv 2404.00806 "Algorithmic Collusion by Large Language Models", Fish, Gonczarowski, Shorrer, 2024 | OK |
| 3 | Agrawal et al. 2025, double auctions | arXiv 2507.01413 "Evaluating LLM Agent Collusion in Double Auctions", Agrawal, Teo, Vazquez, Kunnavakkam, Srikanth, Liu, 2025 | OK |
| 4 | Zeng & Rudzicz 2026, Voluntary Collusion | arXiv 2605.27593 "Voluntary Collusion with Secret Tools in Competing LLM Agents", Zeng, Rudzicz, 2026 | OK |
| 5 | Nakamura et al. 2026, Colosseum | arXiv 2602.15198 "Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems", Nakamura et al. (8 authors), 2026 | OK |
| 6 | Shi, Zhang, Schölkopf, Conitzer, Jin 2026, When Agents Lie | arXiv 2607.05132 "When Agents Lie: Premeditation, Persistence, and Exploitation in Repeated Games", same 5 authors, 2026 | OK |
| 7 | Giebel, Rösner, Schröder 2026, SSRN | papers.ssrn.com/abstract=6832662: HTTP 403 to automated fetch | NOT VERIFIED: open it in a browser before citing |
| 8 | Motwani et al. 2024, Secret Collusion | arXiv 2402.07510 "Secret Collusion among AI Agents: Multi-Agent Deception via Steganography", Motwani et al. (7 authors), 2024 | OK |
| 9 | Wallace et al. 2024, Instruction Hierarchy | arXiv 2404.13208 "The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions", Wallace et al. (6 authors), 2024 | OK |
| 10 | Kavathekar et al. 2025, TAMAS | arXiv 2511.05269 "TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems", Kavathekar et al. (5 authors), 2025 | OK |
| opt | Tao et al. 2026, GroupGuard | arXiv 2603.13940 "GroupGuard: A Framework for Modeling and Defending Collusive Attacks in Multi-Agent Systems", Tao et al. (5 authors), 2026 | OK |
| opt | Sharma et al. 2023, Sycophancy | arXiv 2310.13548 "Towards Understanding Sycophancy in Language Models", Sharma et al. (19 authors), 2023 | OK |

Only existence, title, authors and year were checked. Whether each paper says what the "Difference" column
claims was NOT checked: the team should read the abstracts before writing the related-work section.

## Also noticed
- report/SUBMISSION_CHECKLIST.md says the tag `preexisting-baseline` is missing on the remote. It is pushed
  (`git ls-remote --tags origin` lists `refs/tags/preexisting-baseline` -> fd8c920, 2026-10-25). The checklist line is outdated.

## Difference notes vs abstracts (closest works, abstracts read 2026-10-25)
Only the arXiv abstract pages were read, not the full papers.
| # | Skeleton note | What the abstract supports | Advice for the text |
|---|---|---|---|
| opt GroupGuard | "Honeypot as defense component in QA tasks; CHECK before 'first sting'" | Abstract: defense with "active honeypot inducement" to identify and isolate collusive agents; collaborative tasks, five datasets, four topologies; no market or pricing mentioned | Do NOT write "first sting" or "first honeypot". A safe form: "to our knowledge, the first scripted pact offer in a pricing game; honeypots exist as a defense in collaborative tasks (GroupGuard)" |
| 5 Colosseum | "CLOSEST on say vs do; cooperative DCOP, assigned coalitions" | Abstract: cooperative tasks; "collusion on paper" = agents plan to collude in text but often pick non-collusive actions. How coalitions are set is not clear from the abstract | Cite it as the closest prior on say vs do. Check the paper body before writing "assigned coalitions" |
| 4 Voluntary Collusion | "Offer from environment as a tool, non-market games" | Abstract: tools offered by the environment; Liar's Bar and Cleanup; "only explicit ethical framing reduces adoption" | Note supported. The ethical framing result is the prior for B_ETH (H7) |
| 3 Agrawal et al. | "Free seller talk; authority-pressure result = closest prior for B_T" | Abstract: direct seller communication increases collusion; oversight and urgency from authority figures "influence" collusion (direction not stated in the abstract) | Do not state the direction of the authority effect without reading the paper |
| 2 Fish et al. | "Same game, no channel" | Abstract: LLM pricing agents in oligopoly settings reach supracompetitive prices; prompt wording matters. It does not state the number of sellers or the absence of a channel | Check the paper body (setup section) before writing "same game, no channel" |
