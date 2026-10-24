# Owner approval: branch `artem-owner-approval`

Prepared 2026-10-24 for Artem (project owner). Base: local `artem` at 00c8f08 (617 tests green).
Nothing here was pushed, no real API call was made, no frozen file (PREREGISTRATION.md,
PREREGISTRATION_ADDENDUM.md) was touched. Every commit starts with `PROPOSED (needs owner approval):`.
Two commits edit locked tests (rule D1). Merging the branch is the owner's approval of those `test(fix)` commits.

State at the branch tip: `python3 -m pytest` **624 passed** (617 + 1 R19 boundary test + 6 new validate_e
tests), `python3 -m tools.run_all --dry` exit 0 (all steps, mock client, writes dry_runs/ only).

## Merge (one command, from `artem`)

```
git merge --no-ff artem-owner-approval
```

To reject a single commit instead, cherry-pick the others (`git log artem..artem-owner-approval`).

## Commits, in order

The task order was configs first, then the test(fix). They are swapped here so every commit on the
branch is green (the test(fix) passes on both the old `tbd` configs and the new ids). The one red commit is
the locked validate_e test commit, by rule D1 (its implementation is the next commit).

| # | Commit | What it changes | Why |
|---|---|---|---|
| 1 | `test(fix): test tbd guards on placeholder copies (#21)` | 5 test files + new `tests/helpers_placeholder.py` | QUESTIONS #21. The locked tests asserted that the repo configs ARE `tbd`, so they go red the moment real ids are filled. |
| 2 | `Set model ids, temperature and fallback (D10)` | 6 step configs + `configs/run_all.yaml` | Decision D10, FIXES_CLIENT decisions 1 and 2, QUESTIONS #22. |
| 3 | `test(fix)+fix(R19): abstract 150 to 250 words` | `tools/check_submission.py`, its locked test, SPEC R19, docs/apart note, stale notes in report/ | The live sprint page changed the rule. |
| 4 | `test(Q23): add failing tests for validate_e --config (locked)` | new `tests/test_artem_validate_e_filter.py` | QUESTIONS #23, tests first (rule D1). |
| 5 | `feat(R13): add --config filter to validate_e (#23)` | `tools/validate_e.py` | QUESTIONS #23. |
| 6 | `docs: owner approval note` | this file, RUNBOOK step 2 note, QUESTIONS #21-23 marked PROPOSED | Self-explanatory branch. |

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

### 2. Model ids, temperature, reasoning, fallback

Ids re-checked on `https://openrouter.ai/api/v1/models` (public, no key) on **2026-10-24 09:09 UTC**
(469 models), prices per 1M tokens in/out:

| Role | Id | Price | Reasoning | `temperature` supported |
|---|---|---|---|---|
| family 1 `openai` | `openai/gpt-5.4` | 2.50 / 15.00 | not mandatory, `default_enabled: false` | **no** (see caveat) |
| family 2 `meta-llama` | `meta-llama/llama-3.3-70b-instruct` | 0.10 / 0.32 | none | yes |
| fallback for `openai`, label `openai-fb` | `openai/gpt-4.1` | 2.00 / 8.00 | none | yes |
| fallback for `meta-llama`, label `qwen` | `qwen/qwen3-235b-a22b-2507` | 0.09 / 0.55 | none | yes |

- `temperature: 1.0` in every real config (FIXES_CLIENT decision 1). No `reasoning` key anywhere: gpt-5.4
  reasons only if asked, Llama has no reasoning (FIXES_CLIENT decision 2). Check `reasoning_used` in the smoke logs.
- One change from the RUNBOOK sed: the gpt-4.1 fallback gets the label `openai-fb`, not `openai`. With the sed,
  gpt-5.4 smoke/pilot logs and gpt-4.1 fallback/core logs would share the family label `openai` and be pooled
  in tables. run_all accepts both labels.
- Budget caps unchanged (QUESTIONS #11, #17, #22 still yours: 1 / 5 / 10 / 7.5 / 2.5, global 30 USD).

**Caveat: gpt-5.4 does not accept `temperature`.** Its model entry and all 7 of its provider endpoints
(OpenAI, OpenAI flex/fast, Azure x3, Bedrock) leave `temperature` out of `supported_parameters`. The same holds
for every GPT-5.x model listed. OpenRouter's documentation says an unsupported parameter is ignored, not rejected
(not checked with a real call). So with this config:
- Llama runs at 1.0; gpt-5.4 runs at its fixed provider sampling, but its game logs still say `temperature: 1.0`
  (the value requested, not the value applied). The report must say so.
- If the smoke run errors on gpt-5.4 instead, that is the reason.

**Alternative (recommended if matched temperature matters):** primary `openai/gpt-4.1` (temperature yes, no
reasoning, cheaper: MODEL_AND_COST.md first recommendation) with fallback `openai/gpt-4o` (temperature yes,
2.50 / 10.00), on top of this branch (checked on a scratch worktree: suite and `run_all --dry` green):
```
for f in configs/espion_smoke.yaml configs/espion_pilot.yaml configs/espion_core.yaml \
         configs/espion_monitor.yaml configs/espion_ethics.yaml configs/exploratory/espion_mem.yaml; do
  sed -i '' -e 's#openai/gpt-5.4#openai/gpt-4.1#g' -e 's#gpt-5.4 reasons only if asked (default_enabled false)#gpt-4.1 has no reasoning#' "$f"
done
sed -i '' -e 's#{"0": openai/gpt-4.1, "1": openai/gpt-4.1}#{"0": openai/gpt-4o, "1": openai/gpt-4o}#' \
  -e 's#gpt-4.1 logs must not share a family label with the gpt-5.4 logs#gpt-4o logs must not share a family label with the gpt-4.1 logs#' configs/run_all.yaml
python3 -m pytest && python3 -m tools.run_all --dry && git commit -am "Use openai/gpt-4.1 as family 1 (temperature supported)"
```
A third option: keep gpt-5.4 and set `temperature: null` everywhere (provider default for both families,
honest logs, but Llama's default then depends on the provider).

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

- No real run, no key, no push. GO for the smoke run stays with you (H2).
- QUESTIONS #10, #11, #17 (and the caps in #22) still need your answer.
