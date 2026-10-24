# Client fixes before the first real run (audit finding 9, owner's H2 gate)

Requirements touched: R12 (complete logs), R16 (design config), R17 (cost). No frozen item changes.
Tests: `tests/test_artem_client_settings.py` (fake HTTP layer, sockets blocked, no real call).

## What changed

| Config key | Where | Sent to OpenRouter | Logged |
|---|---|---|---|
| `temperature` | top level; null or a number in [0, 2] | `temperature`, only when not null | game log `temperature` (always in real games, null = not sent) |
| `reasoning` | top level, or per family (family wins) | `reasoning` object, only when set | game log `reasoning` (only when set) |

`reasoning` accepts OpenRouter's documented keys: `effort` (none, minimal, low, medium, high, xhigh), `max_tokens` (int >= 0), `exclude` (bool), `enabled` (bool). Both keys are part of the config, so they are already covered by `config_hash`.

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

## BYOK cost caveat (from MODEL_AND_COST.md, R3 Option A)

If the Anthropic key is used through OpenRouter BYOK, `usage.cost` may show only OpenRouter's BYOK fee, not the Anthropic charge. The R17 `BudgetTracker` would then undercount Anthropic spend. The raw `usage` object is now logged per call, so the smoke run shows what OpenRouter reports under BYOK. Until checked, the owner should set a spend limit in the Anthropic console as the real guard.
