# Novelty, judging, and report plan (bullet material for the team)

Prepared 24 Oct 2026, about 36 h before the deadline (Sun 25 Oct, 11:59 PM AoE). Sources are in `RELATED_WORK.md` (same folder). This is raw material. The report must be written by the team in your own words: Apart says judges will not score reports that read as generated.

Status assumed when writing: harness built and tested (209 tests), preregistration frozen (commit d5e7ebc), **no real model run yet** (runs/ is empty, waiting on API key and model choice). Every score below depends on the core 60 games actually running and E passing.

---

## (a) Honest novelty assessment

### Not new (replication or close to prior work; say so in the report)
- LLM sellers price above Nash without talking: Fish et al. 2024, Keppo et al. 2026, Deshpande & Jacobson 2026. Condition A is a replication, not a finding.
- Communication raises collusion: Agrawal et al. 2025, Giebel et al. 2026, Han et al. 2023, Mazur 2025. Condition E is a positive control, not a finding.
- Agents accept collusion opportunities even when told they are unfair: Zeng & Rudzicz 2026 (Voluntary Collusion).
- Words and actions diverge in collusion: Colosseum's "collusion on paper" (Nakamura et al. 2026) already reports agents planning collusion in text and not acting on it. Shi et al. 2026 show announcement vs action gaps in repeated games. **So "a say-do gap exists" is not new by itself.**
- The design itself is Apart's suggested weekend project for Q3.2 (direct / hint / benign, verbal and behavioral acceptance). Judges wrote it, so they will not score the idea as original. The Resources tab says it "hasn't been tested", so a clean execution is still a first.
- A parallel sprint team (DanielElliottUIUC/ApartAICollusion) runs an undercover price-fixing offer in a double auction. Expect at least one other 3.2 submission on the same idea.

### Genuinely new or uncommon (lead with these)
1. **First measured sting in a price game.** A scripted (non-LLM) outsider sends byte-identical frozen text to both firms. Prior offers come from the environment (Voluntary Collusion) or from free-talking peers (Agrawal, Colosseum). Our stimulus is fixed, so differences come from the condition, not from a persuasive LLM. Caveat: GroupGuard (arXiv 2603.13940) uses "honeypot inducement" as a defense component; read it before writing "first".
2. **Minimal-pair trust label.** B and B_T differ by exactly one sentence (tested, R04). Prior trust or impersonation work (TAMAS, Dark Side of LLMs, Agrawal's authority urgency) mixes label and content. Nobody we found isolates a sender label on a collusion offer.
3. **False-positive control for verbal acceptance.** Condition D (harmless request) measures how often an agent says "accept" to anything. That separates "agreeing to collude" from "agreeing to be helpful" (sycophancy). Colosseum and Shi et al. do not have this control.
4. **Chance baseline for "do".** The permutation base rate (behavioral rule applied to random windows in A and D) says how often prices land near the deal price with no offer. Without it, Fish-style tacit collusion would be counted as acceptance.
5. **Preregistered and reproducible.** Frozen texts and thresholds before any run, `reproduce` with no API key, checksums, labeled games. Rare in sprint work and directly rewarded under Execution ("immediately useful for future work").

### Verdict
- Idea novelty: moderate (3 of 5). The question is Apart's, the say-do gap is known.
- Method novelty: real but narrow (trust minimal pair, D control, permutation base rate, scripted fixed stimulus).
- Ceiling for Impact & Innovation is about 4, reached only by the oversight framing in (b) plus a clear result on at least one of: the say-do 2x2, or B vs B_T.

### Threats a judge will raise (pre-empt them in Limitations)
- **Power.** 5 seeds x 2 families = 10 games per condition. A Wilson 95% interval on 5/10 is roughly 24% to 76%. B vs B_T will not be distinguishable unless the gap is huge. Say "directional", report intervals, do not claim significance.
- **"Say" is a forced categorical field** (`response_to_message` in accept/decline/no_message), not free text. It is the cheapest possible transcript monitor. Be explicit that this is a lower bound on what a richer text monitor could see.
- **Deal price equals joint monopoly price.** If A already drifts toward monopoly (Fish), "do" is easy. The base rate addresses it; show A's price path next to B's.
- **Hint condition C invites "accept" to a non-proposal.** Interpret say in C carefully.
- **Two model families only**, no reasoning models, temperature at provider default.

---

## (b) Judging dimensions: likely score now and cheap ways to raise it

Scores are guesses assuming the 60 core games run and E passes. If E fails, drop each by about 0.5 to 1 and frame as "the game did not allow collusion for this family", which is still a result.

### 1. Impact Potential & Innovation (likely 3, reachable 3.5 to 4)
Cheap actions:
- **Frame the say-do gap as an oversight problem, in one sentence on page 1.** A message monitor and a price auditor see different things. Our 2x2 tells you which one to trust:
  - said yes, prices moved = real cartel, both catch it;
  - said yes, prices did not move = false alarm for a transcript monitor ("collusion on paper");
  - said no / no reply, prices moved = **missed by a transcript monitor**, caught only by a price auditor;
  - neither = clean.
  Compute the share of games in each cell per condition. This turns the table into a monitor-reliability result.
- **Name the auditor/regulator theory of change.** Antitrust treats communication as the key "plus factor" (parallel prices alone are lawful). If LLM agents say yes without acting, a regulator reading logs over-enforces. If they act without saying, a regulator reading logs under-enforces. Either way the recommendation is concrete: audits of AI sellers must check prices against a no-offer baseline, not only messages. Cite Calvano and Fish for why regulators care; cite plus factors only if you verify a source (Berger et al. 2025 is unverified, see RELATED_WORK §9).
- **Trust label as an attack surface.** Multi-agent frameworks already tag messages by origin. If one friendly sentence raises acceptance, labels inside message text are a vulnerability (link to Instruction Hierarchy, Prompt Infection's tagging defense, TAMAS impersonation). If it changes nothing, say that is reassuring. Both outcomes are reportable.
- **Sting as a deployable audit tool.** Spell out: a regulator or platform could run this scripted offer against any pricing agent before deployment (a "compliance test"), cost under a few dollars. Give the measured cost per game from runs/.
- **One line on what the field gets:** frozen texts, labeled games, `reproduce`. Others can rerun with new models in one command.

### 2. Execution Quality (likely 3, reachable 3.5 to 4)
Cheap actions:
- **Run the core first, options only after.** 60 games, both families, E validation script output in the report. The positive control must appear in Results (Apart: "always include the positive control").
- **Report every rate with a Wilson interval and n.** Show the permutation base-rate distribution with the observed "do" rate marked on it.
- **Per-firm secondary table** (20 firms per condition) gives a bit more resolution than 10 games. Label it secondary as preregistered.
- **Price paths figure:** mean price by round for A, E, B, B_T, C, D, with Nash and monopoly lines and the spy round marked. One figure, very convincing.
- **Sensitivity check, labeled exploratory (not a deviation):** recompute "do" at 5% and 20% gap tolerance and window 2 or 5 on the same logs. No new runs, minutes of compute. Shows the result is not an artefact of the 10% / 3-round choice.
- **If budget allows (O1): seeds 6 to 10 on B, B_T, D only.** Doubles n where the key comparisons live. Report as preregistered option.
- **Honest deviations section** even if empty, plus the invalid-price fallback count (QUESTIONS #10).
- **State what is preexisting** (scaffold tag, ArnolFokam harness idea, luciasauer cross-check) to avoid disqualification risk.

### 3. Presentation & Clarity (likely 3.5, reachable 4 to 4.5)
Cheap actions:
- **Page 1: one real excerpt.** The frozen spy message, one firm's reply, and its next 3 prices next to the deal price. Judges get the project in 20 seconds.
- **Figure 1 = the game grid** (already built, R27) colored by the 2x2 outcome. Figure 2 = price paths. Table 1 = say / do / base rate per condition with intervals. No more than 3 figures.
- **Use the words "say" and "do" everywhere**, defined once. Condition names in full in figures ("Direct offer, trusted sender"), never bare letters.
- **Results by question**, each subsection opening with the one-line answer, then the number.
- **Abstract in 4 parts** (problem, method, result, implication), 150 to 250 words (live rule 2026-10-24). Use `tools/check_submission.py`.
- **30-second test:** give the abstract and Figure 1 to someone outside the team, ask them to explain the project back.
- **Optional 3-minute video** walking through the replay page (viz/index.html). Cheap if the page exists, and judges remember it.
- **Write it yourselves.** Short sentences, specific numbers, what you did. Avoid generic opening paragraphs about "the rapid rise of AI".

---

## (c) Headline claim per outcome (one sentence each, to be reworded by the team)

Fill X, Y with the measured rates and intervals.

| Outcome | Suggested headline |
|---|---|
| Say high, do low in B (H2 holds) | LLM sellers often agree to a secret price-fixing offer but rarely change prices, so a transcript monitor would raise many false alarms. |
| Say low, do high (prices move without a yes) | LLM sellers decline a price-fixing offer in words yet move prices toward the proposed level, so message-based audits would miss it. |
| Say high, do high | When a peer offers a price-fixing deal, LLM sellers both accept it and follow through, so a single scripted offer is enough to form a cartel. |
| Say low, do low everywhere (only E colludes) | LLM sellers refuse an unsanctioned price-fixing offer in both words and prices, and only collude when the rules allow it. |
| B_T > B by a clear margin | One sentence calling the sender "a trusted partner" raises acceptance of a price-fixing deal from X to Y, making sender labels an attack surface. |
| B_T about equal to B | A "trusted partner" label does not change acceptance of a price-fixing offer, at the precision our sample allows (directional). |
| D accept rate high (H3) | Agents "accept" a harmless request about as often as a cartel offer, so a verbal yes mainly measures agreeableness, not intent to collude. |
| Families disagree | The same frozen offer is accepted by one model family and refused by another, so collusion risk is a property of the model, not the market. |
| E fails the threshold for a family | For family F the game does not support collusion even when allowed, so its refusals in B are uninformative; we report it as a limitation. |

---

## (d) Report outline mapped to Apart's required sections (target 6 pages, cap 8)

Page counts are main body only; references and appendices are extra.

| # | Section (Apart name) | Pages | Bullet content |
|---|---|---|---|
| 0 | Title, authors, affiliations, abstract (150 to 250 words) | 0.3 | Same title on every resubmission. 4-part abstract. |
| 1 | Introduction | 0.75 | Undercover-officer analogy (Apart Q3.2). Three questions. Why it matters: auditors read messages, harm happens in prices. Page-1 excerpt box. One-line contributions list (sting in price game, trust minimal pair, D false-positive control, permutation base rate, reproducible data). |
| 2 | Related Work | 0.75 | Four short paragraphs: algorithmic pricing collusion (Calvano, Fish, Keppo); LLM communication and offers (Agrawal, Giebel, Voluntary Collusion, Colosseum); say vs do (Colosseum "on paper", Shi et al. x2, Gu et al.); trust labels and peer compliance (Instruction Hierarchy, TAMAS, Dark Side, sycophancy papers). One sentence each on how we differ. Mention the parallel Elliott project and Apart's own suggestion. |
| 3 | Methodology | 1.5 | Game (logit demand, a=2, a0=0, mu=0.25, c=1, 20 rounds, spy at 8), Nash and monopoly prices. Spy as script. Six conditions in a table with the full frozen texts. Say, do, base rate, unit of analysis, Wilson intervals, E threshold. Models, temperature, seeds, cost. Preregistration commit hash and tag. Preexisting vs new work. |
| 4 | Results | 1.75 | 4.0 Positive control (E vs A) first. 4.1 Q1 say vs do in B (2x2, base rate). 4.2 Q2 offer form (B vs C vs D). 4.3 Q3 trust label (B vs B_T). Figures: game grid, price paths, Table 1. Each subsection opens with the one-line answer. |
| 5 | Discussion | 0.75 | Oversight interpretation of the 2x2 (which monitor to trust). Recommendation for auditors. What surprised you. Future work: report button (link Guey et al. 2026), more seeds, reasoning models, free-text replies, multi-firm markets. |
| A | Limitations and Dual-Use / Ethical Considerations (REQUIRED appendix) | 0.5 to 1 | Power (10 games per condition), forced reply field, 2 families, one game, deal price = monopoly price, hint ambiguity. Dual-use: texts are plain and not optimized; we publish rates and a few excerpts, no tuned playbook; the sting could teach evasion (agents trained to say no while pricing high), which is exactly why price-based audits matter. |
| B | References | extra | Use only [V] or [S] entries from RELATED_WORK.md. |
| C | Optional appendix: reproduction | extra | `reproduce` command, checksums, repo link, config hashes, sensitivity table. |

Total main body about 6 pages, leaving 2 pages of slack for figures.

---

## Top actions in priority order (next 36 h)

1. Get the core 60 games run and E validated; nothing else matters as much.
2. Turn Table 1 into the 4-cell monitor table and lead the Discussion with the oversight framing.
3. Page-1 real excerpt plus the price-paths figure.
4. Zero-cost sensitivity check on the behavioral rule (tolerance and window) from existing logs, labeled exploratory.
5. If budget remains, seeds 6 to 10 on B, B_T, D (option O1) to tighten the two key comparisons.
