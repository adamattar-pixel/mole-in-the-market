# Model choice and cost estimate (input for decision D10)

Prepared 2026-10-24 for the owner. Nothing in this file changes the harness or configs. It is a proposal: the owner still makes decision D10.

Prices were fetched from `https://openrouter.ai/api/v1/models` on **2026-10-24 07:48 UTC** (469 models listed). OpenRouter prices change and can differ by upstream provider, so re-check before the real run.

## 1. Token estimate (from the real prompt template)

Method: called `harness.agent.build_messages` with the frozen texts (`load_prereg_texts()`), the frozen demand from `configs/espion_core.yaml` (marginal cost 1.00, `n_rounds` 20, `spy_start` 8) and a realistic history row (`price 1.73, other 1.69, quantity 0.37, profit 27.31`). No offline tokenizer is installed (`tiktoken` absent), so tokens are estimated from characters. The prompt is digit-heavy, and tokenizers split numbers into short pieces, so chars/4 is optimistic. I give a central value (chars/4) and a conservative value (chars/3). Both add about 8 tokens of chat-template overhead per message (2 messages per call).

| Item | Characters | Tokens, central (chars/4) | Tokens, conservative (chars/3) |
|---|---|---|---|
| Round 1 prompt, conditions A, B, B_T, C, D | 419 | ~120 | ~155 |
| Round 1 prompt, condition E (extra instruction) | 485 | ~135 | ~180 |
| Round 20 prompt (19 history lines), A to D | 1,645 | ~430 | ~565 |
| Round 20 prompt, E | 1,711 | ~445 | ~590 |
| One firm, whole game (20 calls), A | 21,100 | ~5,600 | ~7,350 |
| One firm, whole game, E (largest) | 22,598 | ~5,970 | ~7,850 |
| **Both firms, whole game (40 calls)** | 42,200 to 45,200 | **~11,300** | **~15,000** |

The spy message (160 to 174 characters, only in round 8) adds about 50 tokens per firm per game, so conditions differ very little.

Output tokens: the reply is `{"price": ..., "response_to_message": "..."}`, about 30 to 60 tokens per call. Per game: ~1,800 (central) to **~2,400 (conservative, used below)**.

**Reasoning models are different.** A model that thinks before answering (GPT-5 family, Gemini 2.5+/3.x Flash with thinking on, DeepSeek with reasoning, Qwen "thinking", Claude with extended thinking) bills hidden reasoning tokens as output. At 500 to 2,000 reasoning tokens per call, output per game becomes 20,000 to 80,000 tokens, which is 10 to 30 times the costs below. The harness sends no `reasoning`, `max_tokens` or `temperature` parameter (see `harness/clients.py`), so the provider default applies. That is a reason to pick models that do **not** reason by default.

Cost basis used in every table: **15,000 input + 2,400 output tokens per game** (conservative), then a **3x safety margin**.

## 2. Candidate models and current prices

All ids below exist on OpenRouter today (checked in the model list). Prices in USD per 1M tokens. "Seed" = OpenRouter lists `seed` as a supported parameter (the harness sends `seed`; unsupported parameters are dropped). "Reasons" = the model accepts a `reasoning` parameter.

| OpenRouter id | Family (prefix) | Open weights | In $/1M | Out $/1M | Seed | Reasons | Cost per game (raw) |
|---|---|---|---|---|---|---|---|
| `openai/gpt-4` | openai | no | 30.00 | 60.00 | yes | no | 0.594 |
| `openai/gpt-4o` | openai | no | 2.50 | 10.00 | yes | no | 0.062 |
| `openai/gpt-4.1` | openai | no | 2.00 | 8.00 | yes | no | 0.049 |
| `openai/gpt-4.1-mini` | openai | no | 0.40 | 1.60 | yes | no | 0.0098 |
| `openai/gpt-4o-mini` | openai | no | 0.15 | 0.60 | yes | no | 0.0037 |
| `anthropic/claude-haiku-4.5` | anthropic | no | 1.00 | 5.00 | no | opt-in | 0.027 |
| `anthropic/claude-haiku-5.5` | anthropic | no | 0.10 | 0.50 | no | yes | 0.0027 |
| `google/gemini-2.5-flash-lite` | google | no | 0.10 | 0.40 | yes | yes | 0.0025 |
| `google/gemini-3.8-flash` (latest Flash) | google | no | 0.825 | 4.125 | yes | yes | 0.022 |
| `meta-llama/llama-3.3-70b-instruct` | meta-llama | yes | 0.10 | 0.32 | yes | no | 0.0023 |
| `meta-llama/llama-3.1-70b-instruct` | meta-llama | yes | 0.40 | 0.40 | yes | no | 0.0070 |
| `mistralai/mistral-small-3.2-24b-instruct` | mistralai | yes | 0.075 | 0.20 | yes | no | 0.0016 |
| `qwen/qwen3-235b-a22b-2507` (instruct, non-thinking) | qwen | yes | 0.09 | 0.55 | yes | no | 0.0027 |
| `deepseek/deepseek-v3.2` | deepseek | yes | 0.28 | 0.42 | yes | yes | 0.0052 |

Notes:
- `openai/gpt-oss-120b` is open weights but its prefix is `openai`. The harness takes the family from the prefix (`model_family` in `harness/runner.py`), so it would count as the same family as GPT-4.1. Do not use it as the "other" family.
- `anthropic/claude-haiku-5.5` is cheap but very new (listed this month), so it is barely studied, and it reasons by default as far as the listing shows. Anthropic models on OpenRouter do not list `seed`.
- Original `openai/gpt-4` (the model closest to Fish et al. 2024) is still listed but costs 12x GPT-4.1. It has an 8k context, which is enough here (~600 tokens max).

## 3. Cost tables (USD, raw / with 3x margin)

Game counts (2 families each):
- **Smoke** (`espion_smoke.yaml`): A, E x 1 seed = 4 games.
- **Pilot** (`espion_pilot.yaml`): A, E x 5 seeds = 20 games.
- **Core config** (`espion_core.yaml`): B, B_T, C, D x 5 seeds = 40 games.
- **Full 60**: pilot + core config = 6 conditions x 5 seeds x 2 families.
- **60 + O1**: seeds 6 to 10 for all 6 conditions = 120 games.

| Pair | Smoke (4) | Pilot (20) | Core config (40) | Full 60 | 60 + O1 (120) |
|---|---|---|---|---|---|
| **gpt-4.1 + llama-3.3-70b** (recommended) | 0.10 / 0.31 | 0.51 / 1.54 | 1.03 / 3.09 | 1.54 / 4.63 | 3.09 / 9.26 |
| gpt-4o + llama-3.3-70b | 0.13 / 0.38 | 0.64 / 1.91 | 1.28 / 3.83 | 1.91 / 5.74 | 3.83 / 11.48 |
| gpt-4.1-mini + llama-3.3-70b | 0.02 / 0.07 | 0.12 / 0.36 | 0.24 / 0.73 | 0.36 / 1.09 | 0.73 / 2.18 |
| gpt-4o-mini + llama-3.3-70b | 0.01 / 0.04 | 0.06 / 0.18 | 0.12 / 0.36 | 0.18 / 0.54 | 0.36 / 1.07 |
| gpt-4o-mini + qwen3-235b-2507 | 0.01 / 0.04 | 0.06 / 0.19 | 0.13 / 0.38 | 0.19 / 0.57 | 0.38 / 1.14 |
| gpt-4o-mini + gemini-2.5-flash-lite | 0.01 / 0.04 | 0.06 / 0.18 | 0.12 / 0.37 | 0.18 / 0.55 | 0.37 / 1.11 |
| gpt-4o-mini + claude-haiku-4.5 | 0.06 / 0.18 | 0.31 / 0.92 | 0.61 / 1.84 | 0.92 / 2.76 | 1.84 / 5.52 |
| gpt-4.1-mini + claude-haiku-4.5 | 0.07 / 0.22 | 0.37 / 1.11 | 0.74 / 2.21 | 1.11 / 3.32 | 2.21 / 6.63 |
| gpt-4 (original) + llama-3.3-70b | 1.19 / 3.58 | 5.96 / 17.89 | 11.93 / 35.78 | 17.89 / 53.66 | 35.78 / 107.33 |

Reasoning-model scenario (1,000 reasoning tokens per call, 40,000 output per game, raw): claude-haiku-4.5 with thinking 0.215/game, gemini-3.8-flash 0.177/game, gpt-5-mini 0.084/game. Still affordable for 30 games, but the 3x margin no longer covers the uncertainty.

Fit with the existing caps: the configs set `budget_usd` to 1.0 (smoke), 5.0 (pilot) and 10.0 (core). The recommended pair stays under each cap even with the 3x margin (0.31, 1.54, 3.09). Only original `openai/gpt-4` breaks the caps.

## 4. Recommendation

**Family 1: `openai/gpt-4.1`. Family 2: `meta-llama/llama-3.3-70b-instruct`.**

Reasons:
- **Comparability with Fish et al. 2024.** They worked mainly with GPT-4. `gpt-4.1` is the current full-size, non-reasoning GPT-4-line model, so results are closer to theirs than a "mini" model, and it is 12x cheaper than original GPT-4. If the owner wants the closest possible match and accepts the cost, `openai/gpt-4` is still listed, but it would need the core cap raised (about 36 USD with margin for the core config alone).
- **Open weights for reproducibility.** Llama 3.3 70B Instruct has public weights (`meta-llama/Llama-3.3-70B-Instruct` on Hugging Face), so anyone can rerun it outside OpenRouter. Llama models are common in LLM-collusion follow-up work.
- **JSON reliability.** Both are non-reasoning instruction models that follow "reply with JSON only" well, both support `seed` and `response_format`. Neither emits hidden reasoning tokens, so cost is predictable. `parse_reply` already tolerates text around the JSON, and invalid replies are counted, so the invalid-reply rate is itself a reportable check.
- **Cost.** About **1.54 USD raw / 4.63 USD with 3x margin for the full 60 games** (pilot + core), plus 0.31 for smoke.

Cheaper fallback if budget is a concern: `openai/gpt-4o-mini` + `meta-llama/llama-3.3-70b-instruct` (0.54 USD with margin for 60 games). It is the most widely studied cheap GPT model, but further from GPT-4 behavior.

Caveat on Llama via OpenRouter: requests are routed to several upstream providers that may run different quantizations. The harness does not pin a provider today. For a stricter reproducibility claim, the owner could ask for provider pinning (OpenRouter `provider` request field), which would be a harness change and needs its own decision.

**10 seeds (O1):** affordable. Full 120 games with the recommended pair cost about 3.09 USD raw / 9.26 USD with margin.

**Third family:** affordable. Adding `anthropic/claude-haiku-4.5` (non-reasoning by default, widely used) costs about 0.81 USD raw / 2.43 USD with margin for 30 more games (6 conditions x 5 seeds), or 4.86 USD with margin at 10 seeds. Cheaper third options: `qwen/qwen3-235b-a22b-2507` or `mistralai/mistral-small-3.2-24b-instruct` (under 0.25 USD with margin for 30 games). Caution: "2 model families" is a frozen item in PREREGISTRATION.md (D15), so a third family must be reported as an exploratory robustness check, not as part of the preregistered design, unless the owner goes through hard stop H6.

## 5. Config values to paste

The `families` block format is fixed by `harness/runner.py`: the `family` label must equal the id prefix before `/`, and both firms `"0"` and `"1"` need a model. Replace the `families:` block in `configs/espion_smoke.yaml`, `configs/espion_pilot.yaml` and `configs/espion_core.yaml` with:

```yaml
families:
  - family: openai
    models: {"0": openai/gpt-4.1, "1": openai/gpt-4.1}
  - family: meta-llama
    models: {"0": meta-llama/llama-3.3-70b-instruct, "1": meta-llama/llama-3.3-70b-instruct}
```

The existing `budget_usd` values (1.0, 5.0, 10.0) can stay as they are.

Optional third family (exploratory, see caveat above), appended to the same list:

```yaml
  - family: anthropic
    models: {"0": anthropic/claude-haiku-4.5, "1": anthropic/claude-haiku-4.5}
```

Optional O1 (10 seeds): `seeds: [6, 7, 8, 9, 10]` in a separate config, so the 5-seed core logs stay untouched.

## Revision 2026-10-24 (newer models)

Follow-up questions: the owner has an 80 USD Anthropic API key, believes "GPT-6" exists and is cheaper, and considers GPT-4 too old. Data comes from the same OpenRouter model list (fetched 2026-10-24 07:48 UTC). Each entry in that list has a `reasoning` object (`mandatory`, `default_enabled`, `supported_efforts`, `default_effort`), which is the source for the reasoning columns below.

### R1. GPT-5 and GPT-6 generation models on OpenRouter

GPT-6 does exist. Prices are USD per 1M tokens. "Default" is what happens when nothing is sent, which is what the current harness does. "Can turn off" means `none` is in `supported_efforts`. If reasoning is mandatory, the lowest setting is listed instead.

| id | In | Out | Reasons by default | Can turn off / lowest |
|---|---|---|---|---|
| `openai/gpt-6-luna` | 0.10 | 0.50 | yes (medium) | yes, `none` |
| `openai/gpt-6-sol` | 2.00 | 10.00 | yes (medium) | yes, `none` |
| `openai/gpt-6.1-sol` | 2.00 | 10.00 | yes (medium) | no, mandatory; lowest `low` |
| `openai/gpt-6-astra` | 10.00 | 50.00 | yes (medium) | no, mandatory; lowest `low` |
| `openai/gpt-5.6-luna` | 0.20 | 1.20 | yes (medium) | yes, `none` |
| `openai/gpt-5.6-terra` | 2.00 | 12.00 | yes (medium) | yes, `none` |
| `openai/gpt-5.6-sol` | 4.00 | 20.00 | yes (medium) | yes, `none` |
| `openai/gpt-5.5` | 5.00 | 30.00 | yes (medium) | yes, `none` |
| `openai/gpt-5.4` | 2.50 | 15.00 | **no** (`default_enabled: false`) | yes, `none` |
| `openai/gpt-5.4-mini` | 0.75 | 4.50 | **no** | yes, `none` |
| `openai/gpt-5.4-nano` | 0.20 | 1.25 | **no** | yes, `none` |
| `openai/gpt-5.2` | 1.75 | 14.00 | yes (medium) | yes, `none` |
| `openai/gpt-5.2-chat` | 1.75 | 14.00 | no (no reasoning parameter) | n/a |
| `openai/gpt-5.1` | 1.25 | 10.00 | **no** (`default_enabled: false`) | yes, `none` |
| `openai/gpt-5`, `gpt-5-mini`, `gpt-5-nano` | 1.25 / 0.25 / 0.05 | 10.00 / 2.00 / 0.40 | yes (medium) | no, mandatory; lowest `minimal` |

The `-pro` variants (5.x, 6.x) cost the same or much more and run at higher effort. The `-codex` variants are coding models. Neither type fits this study.

**Reasoning tokens per call** are not published. They have to be measured. For a short pricing decision my estimate is roughly 0 with `none`, about 100 to 300 at `low`/`minimal`, and about 500 to 1,500 at `medium`. One thing to know: `clients.py` keeps only `usage.cost` and the message text. It does not log `reasoning_tokens`, so the smoke run shows reasoning only indirectly, as output cost far above the ~0.0001 to 0.001 USD per call expected without reasoning.

**Is GPT-6 cheaper?** Per token, yes: `gpt-6-luna` (0.10 / 0.50) is cheaper than `gpt-4.1` (2.00 / 8.00). But it reasons at medium effort by default, and the harness cannot turn that off today, because it sends no `reasoning` field. With reasoning off it costs about 0.003 USD per game. At medium (~1,000 tokens per call) it costs about 0.023 USD per game, which is still cheap. The bigger problem is that its behavior would then depend on hidden reasoning.

### R2. Anthropic models and cost of the full plan

Full plan = smoke 4 + pilot 20 + core 40 + O1 60 = **124 games, 62 per family**. Same cost basis as above (15,000 input and 2,400 visible output tokens per game), plus reasoning at 40 calls per game, then 3x margin. The cost is for the Anthropic family alone. The other family is paid separately on OpenRouter, because an Anthropic key cannot pay for OpenAI or Llama calls.

| id | In | Out | Reasoning (OpenRouter metadata) | Full plan x3, reasoning off | x3, ~300 tok/call | x3, ~1,000 tok/call | Fits 80 USD? |
|---|---|---|---|---|---|---|---|
| `anthropic/claude-haiku-4.5` | 1.00 | 5.00 | optional, **off by default** | 5.02 | 16.18 | 42.22 | yes |
| `anthropic/claude-haiku-5.5` | 0.10 | 0.50 | optional, default medium, `none` allowed | 0.50 | 1.62 | 4.22 | yes |
| `anthropic/claude-sonnet-5.5` | 2.00 | 10.00 | **mandatory**, default high, lowest `low` | n/a | 32.36 | 84.44 | only at `low` |
| `anthropic/claude-opus-5.5` | 4.00 | 20.00 | mandatory, default high, lowest `low` | n/a | 64.73 | 168.89 | barely, only at `low` |
| `anthropic/claude-fable-5.1` | 10.00 | 50.00 | mandatory, default high | n/a | 161.82 | 422.22 | no |

Older Sonnet 4.5/4.6 (3.00 / 15.00) and Opus 4.5 to 4.8 (5.00 / 25.00) are also listed, with no advantage here. At the default `high` effort, Sonnet and Opus would go over 80 USD. Only Haiku 4.5, Haiku 5.5 with reasoning off, and Sonnet 5.5 at `low` fit comfortably.

For comparison, the other family over the same 62 games, x3 margin, reasoning off: `openai/gpt-5.4` 13.68, `openai/gpt-5.4-mini` 4.10, `openai/gpt-4.1` 9.15, `meta-llama/llama-3.3-70b-instruct` 0.42, `openai/gpt-6-luna` 0.50.

### R3. Can the harness use the Anthropic key directly?

No. `harness/clients.py` has one real client, `OpenRouterClient`. It posts to the hard-coded `https://openrouter.ai/api/v1/chat/completions`, reads only `OPENROUTER_API_KEY`, and `tools/run.py` always builds `OpenRouterClient()` for real runs. There are two options.

**Option A: OpenRouter BYOK (no code change).** Add the Anthropic key in the OpenRouter account settings (Integrations / BYOK). Requests to `anthropic/*` models are then billed to the Anthropic key. An OpenRouter key and credits are still needed, for the OpenAI or Llama family and for OpenRouter's BYOK fee (check the current fee terms). The risk to check in the smoke run: under BYOK, `usage.cost` may show only OpenRouter's fee, not the Anthropic charge. If so, the R17 `BudgetTracker` would undercount Anthropic spend, so the owner should set a spend limit in the Anthropic console as the real guard. The family label stays `anthropic`, and the configs are unchanged apart from the model ids.

**Option B: a small direct client (code change, needs its own decision).** Add an `AnthropicClient` to `harness/clients.py` that calls `https://api.anthropic.com/v1/messages` with `ANTHROPIC_API_KEY`. Points to handle:
- The system prompt moves to the top-level `system` field.
- `max_tokens` is required.
- The Anthropic API has no `seed` (OpenRouter already drops it for Anthropic models, so nothing changes here).
- The response has no cost field. Cost must be computed from `usage.input_tokens`/`output_tokens` and a price table. This conflicts with the current R17 rule "never run with untracked spend" unless computed cost is accepted.
- Ids must keep the `anthropic/` prefix, because `runner.model_family` needs a `family/model` form. The client strips the prefix before sending.

Files touched: `harness/clients.py` (new client), `tools/run.py` (pick the client by family prefix), `tests/test_R12_R17_pipeline.py` (missing key, request shape, computed cost, budget) and the three real configs. No new dependency (urllib, as now).

Option A is the faster path. Option B only matters if the owner does not want spend routed through OpenRouter.

### R4. Revised recommendation

Constraints: the family count is frozen at 2 (D15). The harness sends no reasoning parameter, so only models that do **not** reason by default behave as intended without a code change. The agent reply is JSON only, and the log keeps only the visible reply. Hidden reasoning is never logged (OpenAI does not expose it at all), so with a reasoning model the reason behind each price or accept/decline decision is invisible. Reasoning also adds output tokens. Behavior is easier to compare across families when neither family reasons.

**Primary family 1: `openai/gpt-5.4`.** It is a current GPT-5-generation model, it is the newest OpenAI model whose reasoning is off by default (`default_enabled: false`), and it is a direct successor of the GPT-4 line used by Fish et al. It supports `seed` and `response_format`. Full plan x3: about 13.7 USD. Cheaper alternative: `openai/gpt-5.4-mini` (4.1 USD).

**Primary family 2: `meta-llama/llama-3.3-70b-instruct`.** It is open weights for reproducibility and has no reasoning. Full plan x3: about 0.4 USD. Swapping in `anthropic/claude-haiku-4.5` as a primary would use the owner's key, but it would lose the open-weights point, so I would keep Llama.

**Optional exploratory third family: `anthropic/claude-haiku-4.5`**, using the Anthropic key through BYOK (Option A). Reasoning is off by default, and full plan x3 is about 5 USD, far under 80 USD. Because of D15 it must be reported as an exploratory robustness check outside the preregistered design.

**GPT-6 and Claude Haiku 5.5:** use them only after a small harness change that sends `reasoning: {"effort": "none"}` per family. The change would touch `harness/clients.py`, the `families` entries in the configs, `harness/runner.py` (to put the setting in the game log and config hash) and the tests. With that change, `openai/gpt-6-luna` and `anthropic/claude-haiku-5.5` both become very cheap and newest-generation (about 0.5 USD each for the full plan x3). Without it they run at medium reasoning by default.

Total for the recommended setup, full plan (124 games) x3 margin: about **14 USD on OpenRouter + about 5 USD on the Anthropic key** (with the third family). Without the third family, about 14 USD.

Config values for the recommended primary pair (replaces the block in section 5):

```yaml
families:
  - family: openai
    models: {"0": openai/gpt-5.4, "1": openai/gpt-5.4}
  - family: meta-llama
    models: {"0": meta-llama/llama-3.3-70b-instruct, "1": meta-llama/llama-3.3-70b-instruct}
```

Optional exploratory third:

```yaml
  - family: anthropic
    models: {"0": anthropic/claude-haiku-4.5, "1": anthropic/claude-haiku-4.5}
```

Budget caps: `gpt-5.4` raises cost per game to about 0.075 USD. The existing caps still hold with the 3x margin: smoke about 0.5 of 1.0, pilot about 2.3 of 5.0, core config about 4.6 of 10.0. A combined O1 config (60 games) needs `budget_usd` of at least 7.
