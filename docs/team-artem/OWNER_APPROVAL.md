# Owner approval: branch `artem-owner-approval`

Prepared 2026-10-24 for Artem (project owner). Base: local `artem` at 00c8f08 (617 tests green).
Nothing here was pushed, no real API call was made, no frozen file (PREREGISTRATION.md,
PREREGISTRATION_ADDENDUM.md) was touched. Commits 1 to 6 start with `PROPOSED (needs owner approval):`,
commits 7 onward with `Owner decision:`. Five commits edit locked tests (rule D1, `test(fix)`).

**Models decided (D23, settles D10 / QUESTIONS #7).** The owners (Artem and Adam) chose
`anthropic/claude-haiku-4.5` (OpenRouter BYOK on Artem's Anthropic key) and `meta-llama/llama-3.3-70b-instruct`
(OpenRouter credits), temperature 1.0, no reasoning key. D22 was already the handoff, so this is D23. Every real
config and the run_all fallbacks hold real ids; with the key unset a real run now stops at the key check, not at
the `tbd` check. Costs: MODEL_AND_COST.md "Final choice". Steps: RUNBOOK_REAL_RUNS.md 1 to 3.

State at the branch tip: `python3 -m pytest` **672 passed**, `python3 -m tools.run_all --dry` exit 0 (mock
client, scratch folder only).

## Merge (one command, from `artem`)

```
git merge --no-ff artem-owner-approval
```

To reject a single commit instead, cherry-pick the others (`git log artem..artem-owner-approval`).

## Commits, in order

| # | Commit | What it changes | Why |
|---|---|---|---|
| 1 | `test(fix): test tbd guards on placeholder copies (#21)` | 5 test files + new `tests/helpers_placeholder.py` | QUESTIONS #21. The locked tests asserted that the repo configs ARE `tbd`. Kept: they pass with `tbd` and with real ids. |
| 2 | `Set model ids, temperature and fallback (D10)` | 6 step configs + `configs/run_all.yaml` | Superseded: ids reverted to `tbd` by 12. |
| 3 | `test(fix)+fix(R19): abstract 150 to 250 words` | `tools/check_submission.py`, its locked test, SPEC R19, notes | The live sprint page changed the rule. |
| 4 | `test(Q23): add failing tests for validate_e --config (locked)` | new `tests/test_artem_validate_e_filter.py` | QUESTIONS #23, tests first (rule D1). |
| 5 | `feat(R13): add --config filter to validate_e (#23)` | `tools/validate_e.py` | QUESTIONS #23. |
| 6 | `docs: owner approval note` | this file, RUNBOOK step 2 note, QUESTIONS #21-23 | Self-explanatory branch. |
| 7 | `Owner decision: use claude-haiku-4.5 as family 1 (D10)` | configs | Reverted by 10 (owner changed course). |
| 8 | `Owner decision: add failing tests for BYOK-safe cost (locked)` | new `tests/test_artem_byok_cost.py` | Tests first for the cost guard (rule D1). |
| 9 | `Owner decision: charge max(usage.cost, tokens x price) per call (R17)` | `harness/clients.py`, `harness/runner.py`, `tools/run.py`, `tools/run_all.py`, new `configs/prices.yaml` | Cost guard, and the `<provider>-fb` label fix. |
| 10 | `Owner decision: test(fix): cost guard tests independent of the model ids` | `tests/test_artem_byok_cost.py` | Two tests of 8 named the Anthropic fallback. |
| 11 | `Owner decision: revert the claude-haiku-4.5 switch` | configs | Revert of 7 (new commit, history kept). |
| 12 | `Owner decision: model ids back to tbd placeholders (D10 waits on Adam)` | configs | Model choice stays with Adam. |
| 13 | `Owner decision: docs for the cost guard and the tbd ids` | this file, RUNBOOK, FIXES_CLIENT.md | Superseded by 14 to 23 for the ids. |
| 14 | `Owner decision: claude-haiku-4.5 and llama-3.3-70b as the 2 families (D22)` | 6 step configs, `configs/run_all.yaml`, `configs/prices.yaml` comments | D23 (the message says D22, fixed by 21). Fallbacks reuse commit 7: Sonnet 4.5 (`anthropic-fb`), Qwen3 (`qwen`). |
| 15 | `Owner decision: add failing tests for upstream_inference_cost logging (locked)` | new `tests/test_artem_upstream_cost.py` | Tests first (rule D1). |
| 16 | `Owner decision: test(fix): upstream_inference_cost only logged when present` | that new test | The locked `test_provenance_missing_fields_are_none` pins the exact `last_call` keys, so absent = no key. |
| 17 | `Owner decision: log usage.cost_details.upstream_inference_cost (BYOK)` | `harness/clients.py`, `tools/run_all.py` (`[smoke]` line) | Log only; the charge stays max(usage.cost, tokens x price). |
| 18 | `Owner decision: add failing tests for the .env loader (locked)` | new `tests/test_artem_envfile.py` | Tests first. |
| 19 | `Owner decision: load the repo-root .env at startup, no new dependency` | new `harness/envfile.py`, `tools/run.py`, `tools/run_all.py`, `tests/conftest.py`, `.env.example` | conftest points the loader at an empty path: the suite never reads a real .env. |
| 20 | `Owner decision: test(fix): docstrings cite D23, not D22` | the 2 new test files | Docstrings only. |
| 21 | `Owner decision: cite D23 for the model choice (D22 is the handoff)` | configs, `harness/envfile.py`, `.env.example` | |
| 22 | `Owner decision: record D23 (model families) and settle QUESTIONS #7` | DECISIONS.md, QUESTIONS.md | |
| 23 | `Owner decision: docs for D23 (BYOK, .env, costs, smoke checks)` | this file, MODEL_AND_COST.md, RUNBOOK | |

Note on 11: its message was set by an accidental `--amend` right after `git revert` and then corrected by a
second amend, on the local, never pushed commit. No other commit was rewritten.

### 8 to 10. Cost guard (R17)

A provider can under-report OpenRouter's `usage.cost` (OpenRouter docs: under BYOK `cost` is only
OpenRouter's fee, and the provider charge is in `cost_details.upstream_inference_cost`). The per-config and
global caps would then never trigger. Now:
- `configs/prices.yaml`: input and output USD per 1M tokens per model id, from
  `https://openrouter.ai/api/v1/models`, fetched 2026-10-24 11:36 UTC (candidates of MODEL_AND_COST.md).
- Each real call is charged `max(usage.cost, prompt_tokens x input + completion_tokens x output)`; that charge
  goes to `cost_usd`, the per-config cap and the global cap. Per call, `provenance` logs `cost_reported`,
  `cost_computed`, `cost_charged` and `cost_source` (`usage_cost` or `token_price`).
- A real run refuses a model with no price: `run_all` before any call (every step, fallback and O1 id), the
  client before any request. Missing token counts or missing `usage.cost` are refused as before (R17).
- `tools/run.py` and `run_all` build the real client with the table. Dry runs are unchanged (mock client).
- Bug found and fixed: `validate_config` required the family label to equal the id prefix, so the earlier
  `openai-fb` fallback made `run_all` refuse a real run. A label `<provider>-fb` is now accepted.
- Tests: `tests/test_artem_byok_cost.py` (29, hand-computed). Mutation check: 11 mutations of the new code
  (charge only usage.cost, only tokens, no price refusal, wrong source, wrong output price, zero price
  accepted, no run_all check, no table in run_all or run.py, `-fb` rule too loose or removed), all killed.

D23 ids are filled and priced (re-checked 2026-10-24 12:06 UTC). Under BYOK `usage.cost` is about 0, so the
token price is what the caps see; `upstream_inference_cost` (Anthropic's bill) is logged per call when present
and summed per family in the `[smoke]` line. Next: the RUNBOOK smoke step, with the owner's GO (H2).

### 1. test(fix) for the placeholder-asserting locked tests (QUESTIONS #21)

The 11 tests of #21, plus one more that #21 missed because it was written later
(`test_M3_override_keeps_each_step_own_family_settings`: it asserted the repo pilot has `temperature: null`).
Checked: with commit 2 alone, exactly these 12 fail and nothing else.

- 7 guard tests (P4 x3, R35 x2, memory arm x1, `test_R36_refuses_tbd_in_repo_configs`): the guard now runs on a
  temporary copy of the same repo config with the model ids put back to `tbd`
  (`tests/helpers_placeholder.py`). Same intent (a real run refuses `tbd` ids) and **stricter**: the refusal must
  now mention `tbd` (`match="tbd"`), so a refusal for another reason (for example the missing API key, which is
  what happens with real ids) no longer passes. Mutation check: replacing the `tbd` check in
  `harness/runner.py` and `tools/run_all.py` with a check that never fires makes all 7 fail.
- `test_real_configs_declare_temperature_placeholder` x4 renamed `test_real_configs_declare_temperature`: the
  key must be present and be null or a number in [0, 2]; `validate_config` still runs.
- M3: the test's pilot copy pins `temperature: None`, so its assertions are unchanged byte for byte.

### 2. Model ids (superseded by D23, commits 14 to 23)

The ids of commit 2 (gpt-5.4 + Llama 3.3) were reverted to `tbd` (commits 11, 12), then set to the D23 pair. `temperature: 1.0` stays in
every real config (FIXES_CLIENT decision 1; the `tbd` guards and tests accept it). Candidates, reasoning and
temperature support per model: MODEL_AND_COST.md (gpt-5.x models do not accept `temperature`).

### 3. Abstract rule (R19)

The live sprint page (fetched 2026-10-24) says "Project title and abstract, 150 to 250 words" in Requirements and
in the Pre-submission checklist. SPEC R19, `tools/check_submission.py` and locked test a0cd120 enforced <= 150.
- `check_submission`: `MIN_ABSTRACT_WORDS = 150`, `MAX_ABSTRACT_WORDS = 250`; CLI line now reads
  `abstract: N words (150 to 250) OK|FAIL`.
- Locked test (test(fix)): 150 and 250 pass, 149 and 251 fail (one test added for the 250 bound). The LaTeX,
  overall and CLI tests used 2- or 4-word abstracts that are now too short: they use a 200-word abstract, and the
  LaTeX test keeps its 4-word count and now expects `abstract_ok` False.
- SPEC.md R19 text; `docs/apart/README.md` note and checklist line (Guidelines.md is kept as the earlier copy);
  the "CONFLICT" notes in report/SKELETON.md, report/SUBMISSION_CHECKLIST.md and NOVELTY_AND_JUDGES.md.

### 4 and 5. validate_e config filter (QUESTIONS #23)

`python -m tools.validate_e runs --config espion_pilot` (repeatable) keeps only the logs whose game id prefix is
that config, the same rule as `reproduce.config_name`. Without `--config` the pooling and the output are
unchanged (locked R13 tests untouched and green). New tests, hand-computed: pilot alone 0.300 PASS, smoke alone
-0.200 FAIL, pooled 0.133 FAIL. The run_all `[gate]` output stays the reference for the E gate; this filter is
for reading it by hand.

## Not done here

- No real run, no key, no push. GO for the smoke run stays with the owner (H2).
- Owner to do on openrouter.ai: BYOK Anthropic key set to "Never use shared capacity", credits on the account
  (RUNBOOK step 1). QUESTIONS #10, #11, #17 (and the caps in #22) still open.
