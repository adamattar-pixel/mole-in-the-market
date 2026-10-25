# THIRD_PARTY - preexisting code, reused code, borrowed ideas
No third-party code reused, design inspired by the sources below. The commit tagged `preexisting-baseline` holds only the scaffolding (docs, spec, CI), no harness code. Everything after that tag is new work done during the sprint.

| Source | What we use | License | Status |
|---|---|---|---|
| ArnolFokam/ai-collusion-research-sprint | Not used. No third-party code reused: the harness in harness/ is written from scratch during the sprint, design inspired by the Fish-style duopoly setup (decision D4) | No LICENSE visible, derived from an MIT repo | Not used, idea only |
| luciasauer/algorithmic_pricing_llms (Fish-style duopoly) | Reference for economics checks (R01): formulas compared, no code copied | MIT (checked 2026-10-26) | Reference only |
| mattriemer/LLMCartel, andyjliu/llm-agent-collusion | Optional references, read only | No LICENSE file in either repo (checked 2026-10-26): all rights reserved, nothing reused | Reference only |

Borrowed ideas (no code copied unless stated): identity labels on messages (Daniel Elliott), permutation test for short games (Raj-Taware), paired episodes (munip), preregistration and labels folder (ayodejiades), `reproduce` command structure (Apache 2.0 repo, reimplemented by us), offers from the environment reduce with ethical framing (Voluntary Collusion, citation only).

Visual replay page (Phase 8, optional): style inspired by GridReady (kuular.site), idea only, no code or images copied. No library vendored so far (native JavaScript and SVG); any library added goes to viz/vendor/ with its license and is listed here.

Tools: code written with the help of an AI coding assistant (Claude Code), reviewed and run by the team. The report is written by the authors without AI (ops/DECISIONS.md D27); a superseded AI draft is kept, clearly marked, in report/ai_draft/. Numbers, tables and figures come from committed code outputs.

Reference repos read for comparison on 2026-10-26 (shallow clones outside this repo, nothing executed, no code or text copied, no idea reused closely enough to need its own entry): luciasauer/algorithmic_pricing_llms (MIT), andyjliu/llm-agent-collusion (no license file), umass-ai-safety/colosseum (no license file), mattriemer/LLMCartel (no license file), smojha/collusive-llm-agents (no license file), Ostailor/Steganographic_Collusion (MIT), AgentSafety2025/LLM-Agent-collusion (license file present), Jerick-1380/LLM-Trust-Breaking (no license file), linhkid/TraceGuard (MIT), EmanueleLM/focal-points (README only, on the web). They confirmed our design choices; the only change they prompted is generic README wording (which commands reproduce the results).
