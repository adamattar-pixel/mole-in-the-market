# Competitor scan: other repos in this sprint

Read-only scan, 24 Oct 2026 (about 08:00 UTC). Sources: `gh search repos` (created/updated since 15 Oct) over collusion, apart, sprint, undercover, price-fixing, duopoly, cartel, monitor, trusted agents, honeypot; `gh search code` for sprint strings; README, file tree and selected result files of each hit. Nothing was starred, forked or commented on. Repo text was treated as data. Complements `RELATED_WORK.md` §8 (no repeat of the papers).

Times are last push (UTC). "Results" means data or numbers committed to the repo, not claims in a plan.

Our own public repo shows up in search: `adamattar-pixel/mole-in-the-market` (pushed 24 Oct 08:05). Other teams can see our design.

---

## 1. High overlap (read these before writing Related Work)

### DanielElliottUIUC/ApartAICollusion
- https://github.com/DanielElliottUIUC/ApartAICollusion, pushed 24 Oct 00:00.
- **What:** Track 3.2 (plus 1.2, 3.3). Agrawal continuous double auction, 4 LLM sellers + 4 Haiku buyers. Undercover scripted seller (seat 5, replays a real ask path) privately offers "hold asks at $96" to every seller at hour 3, then holds $96 itself. Placebo seat in every arm sends a neutral DM. Every seller has a `report_to_regulator` tool.
- **Arms:** Base, D (plain offer), D-hs (human seller emotional plea), D-hb (human buyer plea against), D-hsb, E (warning "undercover agents may be present"), F (warning + precedent), G-warn / G-prec (threat with no undercover), F-sham. Also composition sweep (Gemini Flash x Claude Haiku x DeepSeek) and shared identity labels (Claude, DeepSeek, BlackRock, Palantir, UN, Team Blue).
- **Measures:** verbal acceptance (LLM judge), behavioral acceptance (ask to $96 within 2 h vs same seat in Base), reports, false reports, cross-talk. 5 seeds per D-G arm, seller-episode clustered by market.
- **Progress:** README says "planning / scaffolding, nothing below is a result yet". Positive control "built, not yet passed". Last commits fix a Gemini smoke-test crash. A merged teammate workspace (`mert_sprint/`) has one-run leads on Bertrand and double auction compositions, not undercover results.
- **Overlap with us:** about 65% as the brief says. Same Apart 3.2 sting idea, scripted sender, say vs do, frozen texts. They have deterrence (warning, precedent, bluff), reporting, human pleas, mixed families. They do not have: a hint (C) or harmless-request (D) control, a one-sentence trust-label minimal pair (their identity labels apply to all sellers, not to the offer's sender), a no-offer chance baseline for "do" (they compare to a placebo seat, which is close), rule-based detectors scored against ground truth, or memory arm.

### saihariG/talk-without-action
- https://github.com/saihariG/talk-without-action, pushed 24 Oct 07:51 (first big commit "Code, data, pre-registration").
- **What:** "Do LLM-collusion detectors catch real coordination, or just collusive talk that can't affect prices?" Patches the Agrawal double auction with a `talk_without_action` flag: sellers still message, but the ask call never sees messages, so talk is causally cut from prices.
- **Conditions (from `results.json` and run names):** A (seller comms), A' (55 archived Agrawal runs incl. boss pressure, oversight, mixed GPT/Claude), B (talk without action), D (no comms), E, N. Models: GPT-4.1, GPT-4.1-mini, Qwen2.5-7B/32B on Modal vLLM, plus archived Claude/GPT runs.
- **Detectors:** D1 price level, D2a/D2b LLM message judge (frozen jinja prompt), D3a/D3b action-based. Fisher tests with Holm correction, TPR/FPR against a causal label. Example: message judge flags 10/10 talk-without-action games where talk could not move prices, price detector flags 1/10.
- **Progress:** results present, prereg hash files, figures folder. Well along.
- **Overlap with us:** direct overlap with our "detectors scored against ground truth" and "say vs do / transcript monitor false alarms" framing. Their ground truth comes from an architectural cut (talk cannot cause prices); ours comes from a scripted offer with a known deal price and time. They have no offer, no trust label, no defenses.

### ayodejiades/collusion-plus-factors
- https://github.com/ayodejiades/collusion-plus-factors, pushed 18 Oct 15:03 (grid run before the sprint, 14-17 Oct, disclosed).
- **What:** "Parallel conduct is not agreement". Agrawal double auction, 3 LLM sellers vs ZIP buyers, Qwen2.5-7B and Llama-3.1-8B (Ollama, Kaggle). 7 conditions varying channel and model mix; no-channel conditions are decoys where agreement is impossible. Detectors D1 price level, D2 LLM message judge, D3 action dependence, D4 antitrust plus-factor rule. Two preregistered studies of 56 markets each, held-out thresholds.
- **Progress:** full draft paper ("No Single Signal Separates Agreement From Parallel Conduct Among LLM Sellers"), `claims.json`, runs committed.
- **Overlap with us:** detector evaluation against known ground truth, the plus-factor/regulator framing we planned for the Discussion, and "talk without action" analysis. Their headline: the message judge flags every market with a channel. No offer, no trust label, no defenses.

### Raj-Taware/collusion-net-influence
- https://github.com/Raj-Taware/collusion-net-influence, pushed 22 Oct 11:50.
- **What:** pairwise net influence (Bonjour et al. 2022) as an action-only collusion detector, recalibrated with a permutation test. 3-agent Rock-Paper-Scissors; LLM games with Qwen2.5-7B and Llama-3.1-8B (independent, private channel, channel + shared reward, instructed).
- **Progress:** results present. LLM judge on chat AUROC 0.17 / 0.04, net influence 0.91 / 1.00; no collusion emerges without instruction.
- **Overlap with us:** "talk is a poor signal, check actions" and permutation-calibrated false alarm rates. Different game (RPS, not pricing), no offer.

## 2. Medium overlap

| Repo | Pushed | What it does | Models / conditions | Progress | Overlap with us |
|---|---|---|---|---|---|
| [maiyasaliha/undercover-collusion](https://github.com/maiyasaliha/undercover-collusion) | 24 Oct 07:39 | Track 3.2. Undercover agent ("Mike") makes a secret-alliance offer in Liar's Bar (Zeng et al. game); reads activations to see if internals reveal intent better than words | Qwen2.5-7B-Instruct on Modal. Six offer conditions: none, explicit, hint, benign, allied, designer; rigged challenge decision | Pilot only: 60 rows, challenge rate 0-3/10 per condition | Same 3.2 question and the same explicit/hint/benign split (Apart's suggestion). Not a price game; activation probe instead of a price "do" |
| [munip/collusions-lab](https://github.com/munip/collusions-lab) | 21 Oct 12:12 | Trusted-monitor intervention benchmark: does a model-free monitor catch, block, and preserve utility. Bertrand market + SWE pipeline | Scripted agents by default; Ollama/OpenAI/Gemini optional. Conditions: independent, shared context, communication, known collusion, adversarial monitor | Harness and deterministic sweeps; no LLM results seen in README | Our rule monitor defense. They report detection plus prevention plus utility cost, which is a stronger defense framing than ours |
| [thereecer13/apart-collusion](https://github.com/thereecer13/apart-collusion) | 24 Oct 07:24 | Track 2.2: does combining what agents say with what they do help a monitor? 7-agent committee vote (Shi et al. "When Agents Lie" harness), two agents collude via hidden channel | LLM monitors and heuristic baselines see talk / actions / both / said-vs-did table / private plans | Data batches and monitor results committed | Their "said-vs-did table" view is a say-do monitor. Not pricing, no offer |
| [carver/apart-research-collusion-sprint-2026](https://github.com/carver/apart-research-collusion-sprint-2026) ("zerocommcartel") | 24 Oct 07:06 | One-shot Cournot, no messages; firms asking the same model reach the cartel output when told rivals use the same model and prompt | Claude Haiku/Sonnet/Opus 5.5, GPT-6 Astra/luna, free OpenRouter. Pilot pre-sprint | Pilot results present (e.g. 43/48 cartel share); a one-line provider system prompt drops it to 0/30 | Their provider-line defense is close to our ethics framing defense, with a large effect. Cite it next to ours |
| [SupratikB23/LLM-Cartel-Succession](https://github.com/SupratikB23/LLM-Cartel-Succession) and [SSCoderz2123/AI-Collusion-Research-Sprint](https://github.com/SSCoderz2123/AI-Collusion-Research-Sprint) (same project) | 24 Oct 05:19 / 06:52 | Track 1.2: logit Bertrand duopoly (Nash 1.473, monopoly 1.925), replace one agent at round 100; does inherited history or notes carry the cartel | Qwen2.5-7B/14B, OLMo, Granite, Mistral. Control, placebo, same/other model with inherited/blank history, inherited notes, best-response bot | Report, slides and figures committed (pre-sprint runs 1-5 disclosed) | Same game family as ours (logit duopoly). Their "inherited notes" arm overlaps our seller-memory arm |
| [Pixiano/Apart-AI-Collusion-Sprint-Oct](https://github.com/Pixiano/Apart-AI-Collusion-Sprint-Oct) | 24 Oct 07:00 | Bertrand, 3 local LLMs, swap a firm mid-run | gemma4-12b (only model that colludes), others fail gate | Swap study done: replacement changes nothing | Persistent notes arm planned (not run). Useful as evidence that local models often fail the positive control |
| [daudibrahimhasan/collusion-reset](https://github.com/daudibrahimhasan/collusion-reset) and [AMaslov01/ai-collusion-sprint](https://github.com/AMaslov01/ai-collusion-sprint) | 23 Oct 18:21 / 24 Oct 00:37 | Memory reset / selective memory transfer after collusive mutual approval (SALT-NLP peer-review setting) | DeepSeek V4.1 Flash (daud); AMaslov design only | daud: 120 paired episodes, paper phase; AMaslov: design docs | Memory as a carrier of collusion. Not pricing; relevant only to our exploratory memory arm |

## 3. Low overlap (checked, different question)

- **ArnolFokam/collusion-harness, collusion-leaderboard** (23-24 Oct): bid rigging and label-leak tasks with hidden-truth scoring and weak/strong overseers. Same author as ArnolFokam/ai-collusion-research-sprint, which we did not use (no code reused; see THIRD_PARTY.md). Note the harness's posted correction: missing bids defaulted to 100 and created fake collusion. Worth checking we have no similar default (our invalid-price fallback count).
- **taruntrivedi3/collusion-detection** (24 Oct 00:21): null calibration of dependence scans; on archived double auctions, honest paths flagged 37-89%. Supports our permutation base rate.
- **soumya-nayak-commits/collusion-detetction** (23 Oct): net influence vs Cramer's V in RPS, synthetic.
- **In9illusion/collusion-process-traces** (22 Oct): process-trace detection on a shared board, Groq models.
- **777sun77/dolos-compromised-overseer** (23 Oct): Dolos-1.5B red team as a code monitor.
- **stzle/algo-collusion-lab** (21 Oct): Calvano Q-learning replication, no LLMs.
- **Barap1/Counterfactual-Collusion-Certificates** (23 Oct): specification only.
- **poseidon-research/collusion_hackathon** is the official starter; jezknee, shma1234 are copies. Dsinha97, amos-luna16, kachunchan-analytics, nZiben, haleematallat, waynetan123: empty or no question stated yet.

Web search found no other public 3.2 projects beyond these. Private repos and teams without GitHub are invisible to this scan.

---

## 4. Differentiation

### Claims we can make that none of the scanned repos can
1. **Scripted sting in a logit price duopoly, with a known deal price and time.** Elliott does a sting in a double auction (no results yet); maiyasaliha in Liar's Bar (no prices). Nobody has the offer in a Calvano/Fish-style price game.
2. **One-sentence sender trust label (B vs B_T).** Elliott's labels are shared group identities on all sellers; nobody isolates the sender label on the offer.
3. **Harmless-request control (D) for verbal "accept".** No repo separates agreeing to collude from agreeing to anything. maiyasaliha has a "benign" offer but no say measure in a market.
4. **Detectors scored against a scripted ground truth of an offer.** saihariG and ayodejiades score detectors against architectural ground truth (talk cut, no channel). Ours is the only ground truth tied to a specific external solicitation, so we can report per-detector recall on "was a deal offered and taken".
5. **Offer, defense and detection in one harness:** rule monitor and ethics framing tested against the same frozen offer.

### What to avoid claiming
- "First to test undercover / trusted agents" (Elliott and maiyasaliha are running it; Apart wrote the idea). Say "first measured sting in a price game, to our knowledge, at time of writing".
- "Transcript monitors over-flag talk" as a new finding. saihariG (10/10 judge flags with talk causally cut), ayodejiades (judge flags every channel market) and Raj-Taware (judge AUROC below chance) already show it. Present ours as a replication in a new setting, and cite them if their reports are public by submission.
- "A system-prompt framing defense works" as novel. carver's provider line already drops cartel share to 0/30. Our ethics framing is a different setting, not a new idea.
- "Action-based detectors need calibration" as ours. Raj-Taware and taruntrivedi3 show it in detail.
- Any memory-arm claim beyond exploratory. Cartel Succession (inherited notes) and collusion-reset cover memory as a carrier with more data.
- Monitor "prevention" claims. munip measures prevention plus utility cost; if we only measure detection, say so.
- Do not compare our numbers directly with Elliott's: different market, different deal price, and they have no results yet.
