# THIRD_PARTY - preexisting code, reused code, borrowed ideas
No third-party code reused, design inspired by the sources below. The commit tagged `preexisting-baseline` holds only the scaffolding (docs, spec, CI), no harness code. Everything after that tag is new work done during the sprint.

| Source | What we use | License | Status |
|---|---|---|---|
| ArnolFokam/ai-collusion-research-sprint | Not used. No third-party code reused: the harness in harness/ is written from scratch during the sprint, design inspired by the Fish-style duopoly setup (decision D4) | No LICENSE visible, derived from an MIT repo | Not used, idea only |
| luciasauer/algorithmic_pricing_llms (Fish-style duopoly) | Reference for economics checks (R01) | TODO check | Reference only |
| mattriemer/LLMCartel, andyjliu/llm-agent-collusion | Optional references | TODO check | Reference only |

Borrowed ideas (no code copied unless stated): identity labels on messages (Daniel Elliott), permutation test for short games (Raj-Taware), paired episodes (munip), preregistration and labels folder (ayodejiades), `reproduce` command structure (Apache 2.0 repo, reimplemented by us), offers from the environment reduce with ethical framing (Voluntary Collusion, citation only).

Visual replay page (Phase 8, optional): style inspired by GridReady (kuular.site), idea only, no code or images copied. No library vendored so far (native JavaScript and SVG); any library added goes to viz/vendor/ with its license and is listed here.

Tools: code written with the help of an AI coding assistant (Claude Code), reviewed and run by the team. The report is written by the team in its own words.
