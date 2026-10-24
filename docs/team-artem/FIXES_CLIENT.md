# Client fixes before the first real run (audit finding 9, owner's H2 gate)

Requirements touched: R12 (complete logs), R16 (design config), R17 (cost). No frozen item changes.
Tests: `tests/test_artem_client_settings.py` (fake HTTP layer, sockets blocked, no real call).

## What changed

| Config key | Where | Sent to OpenRouter | Logged |
|---|---|---|---|
| `temperature` | top level; null or a number in [0, 2] | `temperature`, only when not null | game log `temperature` (always in real games, null = not sent) |
| `reasoning` | top level, or per family (family wins) | `reasoning` object, only when set | game log `reasoning` (only when set) |

`reasoning` accepts OpenRouter's documented keys: `effort` (none, minimal, low, medium, high, xhigh, max) or `max_tokens` (int >= 0), not both, `exclude` (bool), `enabled` (bool). Both keys are part of the config, so they are already covered by `config_hash`.

Provenance, per call, in `rounds[i].firms[f].provenance` (real client only):
- `served_model`: the response `model` field (the exact model version that answered).
- `provider`: the response `provider` field (the upstream provider OpenRouter routed to).
- `usage`: the raw `usage` object (tokens, `cost`, and any BYOK fields OpenRouter adds).
- `reasoning_tokens`: `usage.completion_tokens_details.reasoning_tokens`, or null if not reported.

Per game: `reasoning_tokens` (sum of reported counts, null if none reported) and `reasoning_used` (true, false, or null when unknown).

Missing response fields are logged as null, never guessed.

## Backward compatibility

- Unset fields: the request body is exactly as before (`model`, `messages`, `seed`, `usage`).
- Dry configs (`espion_dry`, `espion_mem_dry`): logs are byte-identical to before (SHA-256 over all log files, same before and after, with a fixed git_commit). The mock client reports no provenance, so no key is added.
- Real configs (`espion_smoke`, `espion_pilot`, `espion_core`, `exploratory/espion_mem`) now carry `temperature: null` as a marked PLACEHOLDER. This changes their config hash. No real log exists yet (runs/ is empty), so nothing is inconsistent.
- New keys appear in real logs only: `temperature`, `provenance` per call, `reasoning_tokens`, `reasoning_used`, and `reasoning` if set. Readers (`reproduce`, labels, viz) ignore unknown keys.

## Owner decisions (before the smoke run)

1. **Temperature value.** Placeholder `null` keeps the current behaviour (provider default, which can differ between providers of the same model). Recommendation: `temperature: 1.0` in all real configs. Reason: it is the OpenAI API default, so for OpenAI models it changes nothing, while it makes the other family use the same value instead of its provider's default. Fish et al. 2024 are said to have used the default temperature with GPT-4 (UNVERIFIED, check their appendix before citing).
2. **Reasoning per family.** Default is not sent (current behaviour). Recommendation: `reasoning: {effort: none}` on any family whose model reasons by default and allows `none` (for example `openai/gpt-6-luna`, `anthropic/claude-haiku-5.5`, see MODEL_AND_COST.md R1/R2). Leave it unset for models with no reasoning (`meta-llama/llama-3.3-70b-instruct`) or reasoning off by default (`openai/gpt-5.4`). Models with mandatory reasoning cannot use `none`; their lowest effort must be chosen explicitly. Check `reasoning_used` in the smoke logs.
3. **Seeds are replicates.** Many providers ignore `seed` (Anthropic models do not support it). The report should say "replicates". `provider` is now logged, so routing differences are visible, but no provider is pinned (pinning is a separate decision, MODEL_AND_COST.md section on Llama).

## Under-reported cost (R17 guard)

`usage.cost` can be lower than the real charge (OpenRouter docs: under BYOK it is only OpenRouter's fee). Each
real call is therefore charged max(usage.cost, prompt_tokens x input + completion_tokens x output price), with
the per-model prices of `configs/prices.yaml`; both values, the charge and its source are logged in
`provenance` (`cost_reported`, `cost_computed`, `cost_charged`, `cost_source`). A model without a price is
refused. Tests: `tests/test_artem_byok_cost.py`. The project does not use BYOK (owner decision, 2026-10-24).

## Provider routing (pins, 2026-10-24, after the real smoke)

The smoke run showed Llama 3.3 70B served by 6 providers inside single games (AkashML, Cloudflare, DeepInfra,
Novita, Parasail, SambaNova), with different quantizations. A family entry may now carry `provider`, sent
unchanged as OpenRouter's `provider` routing object (https://openrouter.ai/docs/features/provider-routing).
Allowed keys: `order` (non-empty list of provider slugs), `allow_fallbacks` (bool; false needs an order),
`quantizations` (non-empty list of OpenRouter's values), `require_parameters` (bool). It is logged per game as
`provider_routing` (only when set), checked on resume (review M2) and must match between pooled or matched
steps in run_all (review M3). Dry configs and dry run_all drop it, so dry logs are unchanged.

Pins (OpenRouter `/api/v1/models/<id>/endpoints`, fetched 2026-10-24 12:48 UTC):
| Family | Pin | Why |
|---|---|---|
| anthropic (Haiku 4.5), anthropic-fb (Sonnet 4.5) | `order: [anthropic]`, `allow_fallbacks: false` | stays on Anthropic (BYOK key); no `require_parameters`, because Anthropic does not support `seed` and would then be excluded |
| meta-llama (Llama 3.3 70B) | `order: [novita]`, `quantizations: [bf16]`, `allow_fallbacks: false`, `require_parameters: true` | bf16 (no quantization loss), temperature and seed supported, 99.8% uptime over the last day, served about a third of the smoke calls already. 0.135 / 0.40 USD per 1M (the price entry stays 0.10 / 0.32, a locked test; Llama is paid from credits, so usage.cost is the full charge and wins the max) |
| qwen (fallback Qwen3 235B) | `order: [parasail]`, `quantizations: [fp8]`, `allow_fallbacks: false`, `require_parameters: true` | no bf16 endpoint listed; fp8 with temperature and seed, 100% uptime over the last day |
| openai (THINK arm, gpt-oss-120b) | `order: [deepinfra]`, `quantizations: [bf16]`, `allow_fallbacks: false`, `require_parameters: true` | docs/team-artem/THINK_ARM.md |

Alternatives seen for Llama: AkashML fp8 (99.9%), CoreWeave fp16 (99.7%, 0.71 / 0.71). With
`allow_fallbacks: false`, an outage of the pinned provider makes calls fail: rerun the same command later (logs
are write-once, the game in progress is dropped), or change the pin under a new config name.

Reasoning trace: `last_call` also holds `reasoning_text` (message.reasoning, or the joined `reasoning.text`
entries of reasoning_details) and `reasoning_detail_types`, only when the response has them. The returned reply
is always `content`; `parse_reply` strips leaked `<think>` blocks first.

Config hashes: all real configs change (the pin is part of the config). Only the smoke has run; see
RUNBOOK_REAL_RUNS.md step 3 for what to do with the old smoke logs.
