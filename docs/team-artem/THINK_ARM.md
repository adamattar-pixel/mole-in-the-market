# THINK arm - EXPLORATORY, not preregistered

Status: code, configs and tests only. Not run. No result exists for this arm. It is not part of the frozen
design in PREREGISTRATION.md and must never be reported as a preregistered result.

## Why
The main design measures what a seller says (accept / decline) and what it does (prices). A reasoning model
also writes a trace before it answers. This arm logs that trace and codes it with a fixed keyword rule, so we
can describe, next to say and do, what the trace talks about in the offer round and the 3 rounds after it
(the "do" window). It is a descriptive add-on: it does not test a hypothesis.

## Design
- Third family, `openai/gpt-oss-120b` (open weights, reasoning mandatory, efforts low / medium / high on
  `/api/v1/models`, 2026-10-24), self-play, `reasoning: {effort: low}`, same `temperature: 1.0`.
- Config `configs/exploratory/espion_think.yaml`: conditions A, E, B, B_T, C, D, seeds 1 to 5, the frozen game
  (20 rounds, spy_start 8, logit demand): 6 x 5 = 30 games, 1,200 calls. Flag `think: true`.
- Provider pinned: DeepInfra bf16 (`order: [deepinfra]`, `quantizations: [bf16]`, `allow_fallbacks: false`,
  `require_parameters: true`). On the endpoints data it lists temperature, seed, reasoning and
  include_reasoning, with 100% uptime over the last day.
- The trace is logged per call in `rounds[i].firms[f].provenance.reasoning_text`: `message.reasoning`, or the
  joined `reasoning.text` entries of `message.reasoning_details`. `reasoning_detail_types` lists the entry types
  that came back. A `reasoning.summary` or `reasoning.encrypted` entry is not a raw trace: `reasoning_text` is
  then null (OpenRouter reasoning docs, https://openrouter.ai/docs/use-cases/reasoning-tokens).
- Parsing: price and response come from `message.content` only, never from the trace. Leaked `<think>` /
  `<thinking>` blocks are removed first (closed blocks, text before a stray closing tag, text after an
  unclosed opening tag), `harness/agent.py` `strip_think`. On the 160 smoke replies this changes nothing
  (re-parsed, 0 differences).
- One-game check first: `configs/exploratory/espion_think_smoke.yaml` (B, seed 1, 40 calls).

Not verified with a live call (no paid call in this work): whether DeepInfra returns the raw trace for
gpt-oss-120b. The docs say most models return reasoning but do not list gpt-oss. The one-game check settles it:
`reasoning_text` must be non-null and `reasoning_detail_types` must contain `reasoning.text`. If not, pick
another endpoint from the same list (AkashML bf16 is the next one) and run the check again.

## Separation from the preregistered tables (same pattern as the memory arm)
- `validate_config`: a real config with `think: true` must write under `runs_exploratory/`; `memory` and
  `think` are never both set.
- Logs carry `"think": true` and game ids start with `espion_think__`, which is not in `PREREG_CONFIGS`.
- `harness/labels.py` `check_one_arm`: `make_labels`, `tools/score_detectors.py` (R29 detectors) and
  `tools/reproduce.py` refuse a set of games that mixes frozen, memory and think games.
- `tools/run_all --think` (off by default) runs after the memory step and writes to `runs_exploratory/think/`,
  tables to `results_exploratory/think/tables/`, views to `results_exploratory/think/`.

## THINK coding (tools/think_view.py)
For each game and firm, rounds spy_start to spy_start + 3: price, response, say and do per firm
(preregistered definitions, applied descriptively), and 5 codes of the trace:
`mentions_deal`, `mentions_legality_or_antitrust`, `mentions_rival_trust`, `intends_to_follow`,
`intends_to_defect`.

The coder is a **heuristic**, transparent keyword rule, no model call. Keyword lists live in
`configs/exploratory/espion_think_coder.yaml` (`heuristic: true` is required). A code is 1 when one of its
phrases appears as whole words, case-insensitive. For `intends_to_follow` and `intends_to_defect`, a match does
not count when a negation word ("not", "won't", ...) is among the 3 words just before it. It misses paraphrase,
irony and conditionals ("if I undercut..."). Report it as a keyword count, never as what the model "intends".
Tests: `tests/test_artem_think_arm.py` (hand-written traces, codes worked out by hand).

Outputs (`python3 -m tools.think_view runs_exploratory/think results_exploratory/think`):
- `think_view.csv`: one row per game, firm and round.
- `think_view.md`: per game and firm, say, do, and "rounds flagged / rounds with a trace" per code.
- `think_excerpts.md`: offer round, reply, first 400 characters of the trace, next 3 prices.
- `think_traces.md`: offer round and next 3 rounds, at most 1,500 characters of trace per firm.
- `traces/<game_id>.json`: sidecar with the full traces of those 4 rounds.

## Showcase (owner approved, 4 games, run by the orchestrator after merge)
`configs/exploratory/espion_think_showcase.yaml`: two higher-tier open-weight reasoning models, each its own
family in self-play, conditions B and E, seed 1, `reasoning: {effort: medium}`, out_dir
`runs_exploratory/think_showcase`. Then `python3 -m tools.think_view runs_exploratory/think_showcase
results_exploratory/think_showcase`.

Choice (from `/api/v1/models` and `/endpoints`, 2026-10-24 12:48 UTC). Candidates had to list `reasoning`, be
open weights (an open-weight model's provider returns the model's own trace; closed models may return only a
summary or encrypted content), and have an endpoint with temperature and seed:
| Family | Model | Why | Pinned endpoint |
|---|---|---|---|
| deepseek | `deepseek/deepseek-v4-pro-0813` | GA DeepSeek V4 Pro (1.6T MoE, 49B active), newest DeepSeek flagship | Novita fp8, temperature + seed + reasoning, 100% uptime last day |
| qwen | `qwen/qwen3.8-2.4t-a95b` | open-weight variant of Qwen3.8 Max (2.4T, 95B active) | Novita (re-pinned 2026-10-24 22:10 after a live probe; Alibaba endpoint status unknown), temperature + seed + reasoning; quantization not published |

Other candidates seen: `moonshotai/kimi-k3` (2.8T open weights; most endpoints fp4), `z-ai/glm-5.3`.
"Strongest" is a judgement from size and release, not from a benchmark we ran.

Caveats for the showcase:
- DeepSeek V4 Pro lists efforts max, high, low, none: "medium" is not listed. OpenRouter may map it or ignore
  it. Check `reasoning_tokens` and `reasoning_text` in the first DeepSeek game; if the call fails or no trace
  comes back, use `high` (closest) and say so.
- Raw trace not verified by a live call for either model (same check as above).
- 1 seed per cell: an illustration, not a rate.

## Cost (estimate, not measured)
Inputs: mean prompt 406 to 422 tokens per call in the smoke logs (Llama and Haiku tokenizers; gpt-oss differs),
so about 410. Completion: about 20 to 50 content tokens plus reasoning. Reasoning tokens are billed as output.
The guard charges max(usage.cost, tokens x configs/prices.yaml); for these models the price entry is the higher
of the `/models` price and the pinned endpoint's price, so the guard's number is the upper one.

THINK arm, gpt-oss-120b, 300 to 1,000 reasoning tokens per call (320 to 1,050 completion), 40 calls per game:
| | Price in / out per 1M | Per game | 30 games |
|---|---|---|---|
| Guard (prices.yaml, /models price) | 0.15 / 0.60 | 0.010 to 0.028 USD | 0.30 to 0.83 USD |
| Expected bill (DeepInfra bf16) | 0.037 / 0.17 | 0.0028 to 0.0078 USD | 0.08 to 0.23 USD |
Cap `budget_usd: 1.5` (PROPOSAL). The one-game check is about 0.003 to 0.03 USD (cap 0.1).

Showcase, effort medium, assumed 1,000 to 3,000 reasoning tokens per call (1,050 to 3,050 completion):
| Family | Price in / out per 1M (guard = pinned) | Per game | 2 games |
|---|---|---|---|
| deepseek (Novita fp8) | 0.99 / 2.97 | 0.14 to 0.38 USD | 0.28 to 0.76 USD |
| qwen (Novita) | 2.00 / 6.00 | 0.29 to 0.77 USD | 0.57 to 1.53 USD |
| Total, 4 games | | | 0.85 to 2.29 USD |
Cap `budget_usd: 3.0`. Measure the real numbers in the logs (`cost_usd`, `reasoning_tokens`).

## Caveats
- CoT faithfulness: a trace is not a faithful account of why the model acted. Reasoning models often leave out
  what drove their answer (Anthropic, "Reasoning models don't always say what they think",
  https://www.anthropic.com/research/reasoning-models-dont-say-think). Chain-of-thought monitoring is useful but
  fragile (Korbak et al. 2025, "Chain of Thought Monitorability", https://arxiv.org/abs/2507.11473). So: report
  trace codes next to say and do, never as the cause of the do.
- Keyword coding is crude (see above). Codes are counts of phrases, nothing more.
- Different model, different family: compare within the arm (B vs A, B vs D), not with Haiku or Llama numbers.
- Seeds are replicates (providers may ignore the seed).

## Dual-use
Traces may contain step-by-step reasoning about how to collude or hide it. Publish the codes and a few short
excerpts (a sentence or two) only. Keep `think_excerpts.md`, `think_traces.md` and `traces/` internal unless the
owner decides otherwise. No new persuasive text: the offers are the frozen texts.

## Files
- `harness/clients.py` (trace logging), `harness/agent.py` (`strip_think`), `harness/runner.py` (`think` flag),
  `harness/labels.py` (`check_one_arm`), `tools/think_view.py`, `tools/run_all.py` (`--think`).
- `configs/exploratory/espion_think.yaml`, `espion_think_smoke.yaml`, `espion_think_dry.yaml`,
  `espion_think_showcase.yaml`, `espion_think_coder.yaml`; prices in `configs/prices.yaml`.
- Tests: `tests/test_artem_think_arm.py`, `tests/test_artem_think_showcase.py` (locked).

## Publication note (2026-10-24 23:40 HKT)
The raw Qwen traces (traces/*.json, think_traces.md, think_excerpts.md) were committed by mistake in 8db26d3 and pushed to `wip/phase-4`; they were untracked and git-ignored in the next commit. They remain in that branch's history. Rewriting history needs a force push, which the repo forbids without the owner (ops/QUESTIONS.md #28). The public outputs are the coded table think_view.md / think_view.csv only.
