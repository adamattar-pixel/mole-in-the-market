Research questions in depth
The full questions from the organizing team, with the results each one builds on. The practical starts further down give starter code and a weekend-sized project for each.

1) Markets and Collusion
1.1. Which variables are necessary for collusion to emerge in markets? Previous experiments controlled various levers to check whether collusion emerged:
What are other scenarios and levers that could cause collusion to form? Ideally these would be single effects so that they can be isolated, and have an objective way to get measured. These variables are not necessarily unique to LLMs. Inspiration might be had from considering cases of collusion between humans. It would be interesting to understand if certain variables are more impactful for LLMs than for humans, and if there are variables unique to collusion between LLMs.
Adding more diverse types of agents and making them competitive with each other decreases collusion in an economic setting (Keppo et al. 2026).
Seemingly innocuous cues in prompts can increase collusion, as measured by pricing deviating from economic expectations on competitiveness (Fish et al. 2024).
Letting pairs of agents talk directly in private can introduce collusion (Nakamura et al. 2026).
1.2. Once collusion has formed, is it robust to replacing some of the participants? Rematching breaks Q-learning pricing collusion permanently, because trained policies overfit their training rival (Eschenbaum et al. 2022). Collusion occurs between a 32B and 14B DeepSeek-Qwen family mismatched in size, but not when LLMs were paired with Q-learners (Keppo et al. 2026). Models from similar families coordinate better on tasks that require coordination (Aharon et al. 2026). There are no replacement studies yet where models are substituted (e.g. because they are taken out due to monitoring concerns) but the newcomers re-engage in collusion. Does replacing offenders remove or recreate collusion?
1.3. Can we improve on existing collusion detection methods? Several adjacent methods and results offer starting points:
Can we take these or similar methods from the literature and improve upon them or relate them to the pure collusion setting? For example, can we identify and measure settings in which two agents from different model providers and running different harnesses have a propensity to coordinate, because they have high mutual "Schelling salience" (Rippin et al. 2026) on that task and make similar choices? And can we find anti-examples where this breaks down?
Two deployments of the same base model have slight correlations in some economic settings while different base models have zero correlation (Xu et al. 2026)
Interpretability-based detectors (Rose et al. 2026)
Measuring whether independent agents select compatible steganographic schemes, keys and parameters (Rippin et al. 2026)
1.4. Can we use information-theoretic approaches to detect collusion in multi-agent games? A measure called pairwise net influence can identify colluding pairs among three or four agents in small discrete games (Bonjour et al. 2022). It assumes exactly two colluders and hasn't been applied to language-model-based agents yet. Other approaches rely on model internals via interpretability-based probes (Rose et al. 2026). Can we find an example of these techniques or variations of them working on a set of agents in a toy or realistic scenario?
1.5. Which single restriction removes the most collusion at the least cost? Single restrictions have been measured individually:
An even better approach may be to introduce a single participant playing a no-regret strategy, which can be enough to destabilise a collusive equilibrium (Collina et al. 2025). Can we set up controlled experiments with multiple controllable levers that can show what disrupts collusive behavior the most at the least overall monitoring/intervention costs?
Raising sampling temperature weakens cross-agent dependence (Xu et al. 2026)
Throttling messaging pushes coordination down (Agrawal et al. 2025)
Introducing agents from a non-LLM architecture (e.g. a Q-learner) into the mix collapses price collusion (Keppo et al. 2026)
A system-prompt instruction produces only small and unreliable shifts in one experiment (Bracale Syrnikov et al. 2026)
Whereas strongly worded instructions to compete aggressively pushed prices below the competitive level in another experiment (Dhanda 2026).
In one setting, agents need to post a refundable deposit that they forfeit if caught colluding, and with that deposit removed, colluding costs them nothing, and every tested model colluded in every run (Q. Liu et al. 2026).
In this track, the results we build on are native to markets, though you should feel free to explore them beyond this setting as the questions themselves are more general, and there are clear overlaps with some later tracks, e.g. information-theoretic approaches to detect collusion would fit well in track 2. Environments where humans collude likely offer similar incentives and opportunities for models to collude. Other such environments might include politics, media and marketing. This track is important because it represents a failure mode in a high stakes environment (markets/economics) where misaligned actions from an AI could cause substantial harm. It also provides a useful testbed for collusion. For a contrasting positive view of the role of markets in multi-agent systems, see Tomašev et al. (2026).

2) Detection and Audit of Collusion
2.1. Which kinds of tasks lead to collusion? Some examples from previous work that generated collusion:
Can you think of new tasks/environments/pressures that lead to collusive behavior outside of the market structure?
Models forming prices that violate economic expectations on competitiveness (Fish et al. 2024).
Agents can independently engage in anti-competitive practices (Lin et al. 2024).
In a setting called Colosseum, over half of tested models showed "coalition advantage" when given the opportunity to speak privately in a realistic workplace task (Nakamura et al. 2026).
2.2. Does combining what agents say with what they do beat either alone? Conversations and actions are known to disagree. One way to measure this is via action-level coalition advantage, which has a weak but non-trivial anti-correlation in some collusion settings against LLM-judge conversation scores (Nakamura et al. 2026). Other related results include:
What are other "hybrid techniques" that look for inconsistencies between words and actions, or within their internal attributes like verbosity or action structure, and can we set up examples that show whether we can detect cross-agent consistency, e.g. whether A's behavior is consistent with B's stated plans or has deviated.
In various repeated n-player games, more than 90% of deviations from public announcements were already stated in models' private plans (Shi et al. 2026).
Work in the sabotage setting has set up monitors that look for multiple agents coordinating independently on what they say and do (Radev et al. 2026).
Analyzing an agent's actions from multiple dimensions can improve a single-dimension monitor from 0% to >70% (Nguyen et al. 2026).
Less can be more: sometimes giving a monitor too much detail degrades its performance (Arike et al. 2026).
2.3. What should count as convincing evidence of collusion? Most of the literature cited earlier has documented limitations or failure modes in their respective limitations sections. Antitrust law met the problem of collusion detection with noisy evidence a century ago and answered with the plus-factors doctrine, under which parallel conduct alone is lawful and inferring agreement needs additional evidence (Berger et al. 2025). The ML literature is largely re-deriving this without engaging that doctrine or similar principles by name. Which signals, alone or combined, actually separate deliberate coalitions from innocent correlation, talk without action, and harm without agreement? Is there previous work we can leverage from adjacent literature, like anti-trust law, and how would we operationalize that to detect collusion between AI agents?
This track is about definitions, detection and evidentiary standards in general, with evidence drawn from logged agent trajectories. Markets could still be relevant settings, but we aim at being more general, such as in more commonplace workflows. This track is important for understanding collusion in general. Can we say things about what causes collusion in general?

3) Collusion Carriers and Countermeasures
3.1. Beyond colluding directly via text, can actions, tools or side channels be the conduit for collusion? There are multiple examples of demonstrable collusion that don't involve exchanging explicit text (Fish et al. 2024; Lin et al. 2024; Keppo et al. 2026; Tian 2026). Can the actions a model takes, such as in an agentic harness, in its choice of actions, or even through timing and tool choices, act as a way to signal or coordinate? For an advanced example of models using tools to construct steganographic communication systems, see Rippin et al. 2026.
3.2. Can we disrupt collusion through introducing trusted agents? Law enforcement has long used undercover officers who offer to join a conspiracy and record who accepts. The equivalent here would be to introduce trusted agents (e.g., enforced with a strong system prompt) that offer coordination or collusion opportunities to a group of agents and log which of them reciprocate. Can we set up such scenarios, and do other agents accept, reject, or arouse suspicion depending on how the trusted agent approaches the transactions? This hasn't been tested.
3.3. Can agents identify their peers? One idea for breaking undesirable multi-agent coordination is to set up anonymized or pseudonymous agents, unsure of whom they are communicating with, or where participants and model versions can be swapped in/out on the same transcripts. However, model families can be identified from short role-constrained text, and the fingerprint sits in the text the model generates, so renaming or anonymising agents leaves it in place (Dietrich 2026). Removing a feature part-way through a run, from a coalition that has already settled into a convention, has not been tested. Can we test whether models can recognize their peers and/or detect when their peers have changed, for example, by periodically sending subtle recognition signals?
3.4. What does a coalition do when it learns it is being watched? An agent that knows how it is being monitored can do more than hide from the monitor. As one example, merely telling an agent that it is watched costs a monitor more accuracy than telling the monitor about the agent gains it (Kale et al. 2025), and 20 of 40 catalogued attacks went uncaught by a strong monitor (Najt et al. 2026). When agents had to work out for themselves that they were monitored, by noticing that some of their episodes were being blocked, the intent to conceal appeared in only three cases out of 2,400 and all three failed to act on it (Jiralerspong et al. 2026). What happens if you add multiple agents into the mix and shrink or expand the monitor budget, such that only a subset of outputs can be monitored? If a coalition discovers that some of its output is being read, does it stop coordinating, coordinate less effectively, try to outsmart the monitor, or try to move coordination into a place where there is no monitoring? The nearest existing case is a double auction in which five sellers were told their messages were being monitored. They attempted to work around monitoring using one-character messages and emojis but were not successful, whereas a prompt demanding urgency led to success (Agrawal et al. 2025).
This track studies how the coordination needed for collusion is mediated, and how it can be broken. This is important because we need to be able to prevent and break up collusion, ideally before it happens, or otherwise while it is occurring.

How to get started
Practical weekend projects, starter code and resource estimates for the research questions on the Overview tab.

Planning assumptions. Repository and paper links were checked on 31 August 2026. Start with 3 to 5 seeds per condition and expand to 10 to 20 only after the positive control works. Estimates assume short outputs, retries and low-cost API models; they exclude participant time and coding-assistant subscriptions. All default routes use a normal 16 GB laptop and no GPU.

Check current rates: OpenAI · Google · Mistral

Track 1: Markets and Collusion
Which variables are necessary for collusion to emerge in markets? (1.1)
Starter code: Fish-style duopoly implementation; duopoly.py; LLMCartel. The independent Fish-style implementation exposes a repeated two-seller pricing game with 300 rounds and visible history. LLMCartel adds convenient prompt, temperature, monitoring and round controls. Together they support clean one-variable-at-a-time ablations.

Weekend project: Reduce the default sweep (the repository's grid of prompt prefixes and demand parameters) to one prompt, parameter value and seed, and first verify sustained prices above the competitive benchmark. Then vary only one feature, for example 0, 10 or 100 visible rounds (the length of price history included in each prompt, not the game length); persistent notes on/off (the plans-and-insights scratchpad from Fish et al.); stable versus shuffled seller names; or temperature, while holding the economics fixed.

Resources: Low-to-medium setup risk. A 300-round two-agent run makes about 600 sequential model calls. Twelve to 24 pilot runs require roughly 7,200 to 14,400 calls. Use one low-cost API provider, a 16 GB laptop and no GPU; budget about $20 to $100.

Is formed collusion robust to replacing some participants? (1.2)
Starter code: LLMCartel; focal-points. LLMCartel is an API-based repeated-pricing harness with configurable models, prompts, rounds and seeds. It does not include checkpoint branching, but a coding agent can add history serialisation. focal-points is a cheaper benign control for testing whether replacement agents independently recover a convention.

Weekend project: Keep pricing runs that cross a predeclared high-price threshold, save the transcript, and branch each history into: no replacement; a fresh instance of the same model; a different model in the same family; and, if an adapter is available, a different provider. Cross each replacement with notes preserved or removed, then compare price, profit and time to recover the convention.

Resources: Medium setup risk because branching is a small new feature. Aim for 10 to 20 base runs and 20 to 40 post-checkpoint branches. Use one provider initially, two only for the cross-provider arm; 16 GB laptop, no GPU; roughly $20 to $100.

Can we improve on existing detection methods? (1.3)
Starter code: LLM agent collusion; paper; focal-points. Agrawal et al.'s official double-auction code already supports different seller and buyer models, seller communication, oversight, pressure and message limits. It is a practical black-box test bed for separating suspicious coordination from shared model priors. focal-points can supply benign Schelling-point examples.

Weekend project: Run a 2x2 study: same-model versus cross-provider sellers, with seller communication on versus off. Score each trajectory with a simple action-dependence statistic and the same LLM judge. Test whether calibrating the detector on no-communication, same-model runs reduces false alarms without masking communication-enabled coordination.

Resources: Low-to-medium setup risk. Start with 3 sellers, 3 buyers, 15 rounds and 3 to 5 seeds per cell, plus 100 to 200 monitor calls. Two API providers make the model-family comparison meaningful. No GPU is needed; budget roughly $20 to $100.

Can information-theoretic methods identify colluding pairs? (1.4)
Starter code: Bonjour et al. paper; Agrawal auction code. Bonjour et al. define pairwise net influence mathematically, but no public author implementation was located. The statistic is compact enough for a coding agent to implement and validate before applying it to an LLM game. The Agrawal environment is a richer follow-up once the method works.

Weekend project: First implement pairwise net influence and test it for free on scripted iterated Rock-Paper-Scissors with one known coordinating pair. Then run a four-agent discrete game with exactly one seeded pair and compare how well net influence, ordinary action correlation and an LLM judge rank the true pair. Under the Markets and Collusion track, treat the Agrawal double auction as the target environment: a dependence statistic validated there doubles as a quantitative plus factor for market cases.

Resources: Low-to-medium engineering risk: the initial harness should be only a few hundred lines. Use local CPU for the statistic, then 20 to 40 LLM games of 15 to 25 rounds. A 16 GB laptop is enough; budget $0 for the scripted test and about $5 to $50 for the LLM pilot.

Which single restriction removes the most collusion at the least cost? (1.5)
Starter code: LLM agent collusion; paper. The official double-auction code already exposes seller communication, oversight, maximum message length, pressure and temperature. That makes several one-factor interventions comparable inside one environment without stitching together unrelated repositories.

Weekend project: First reproduce one coordinated-pricing condition. Rerun identical seeds while changing exactly one restriction: remove seller messages; impose a short message cap; or add an oversight notice (temperature is a useful fourth option). Compare both collusion outcomes (prices and seller profit) and legitimate performance (trade volume and buyer welfare).

Resources: Low setup risk. Start with 3 sellers, 3 buyers, 15 rounds and 3 to 5 seeds; expand toward the published 5-seller/6-buyer, 30-round setting only if the positive control works. Use one API provider, a 16 GB laptop and no GPU; budget $20 to $120.

Track 2: Detection and Audit of Collusion
Which kinds of tasks lead to collusion outside of markets? (2.1)
Starter code: Colosseum; paper. Colosseum already provides Hospital and Jira tasks, assigned colluding pairs, private channels, individual rewards and coalition-advantage metrics. The supplied assigned-pair, private-channel run is the positive control; the project then removes that membership and communication scaffolding.

Weekend project: First reproduce one supplied collusion run. Then compare four matched conditions: assigned pair plus private channel; assigned pair without the channel; a generic channel open to everyone; and neither assignment nor special channel. Keep task, model and seed fixed, and score the best-performing proper subset rather than only the originally assigned pair. Score subsets because the unassigned conditions have no designated pair to score. More broadly, can you work out the core components a task needs for collusion to occur, by ablating affordances within the Hospital and Jira tasks, by using Hospital and Jira as templates for inventing new tasks, or by relaxing or changing the underlying DCOP formalism? The affordance ablation is the safest weekend scope; changing the formalism needs the most new engineering.

Resources: Medium setup risk: preflight the Terrarium/CoLLAB dependencies. Run 20 to 40 short episodes on one API provider. A 16 GB laptop is sufficient; no GPU is needed. Plan for roughly $15 to $75, with $150 as a cautious ceiling for long tool traces.

Does combining what agents say with what they do improve detection? (2.2)
Starter code: LLM-Trust-Breaking; paper; TraceGuard. Shi et al.'s official harness records private plans, public announcements, final actions and outcomes across several social dilemmas, and supports OpenAI/OpenRouter and heterogeneous groups. TraceGuard is a single-agent monitoring system, not a drop-in collusion detector, but its action-trace consistency rubric is reusable.

Weekend project: Generate a small balanced set from one game, then give the same monitor four views: messages only; actions only; raw messages plus actions; and a structured report comparing claims with outcomes. Freeze the monitor model, prompt and threshold before evaluation, and report both accuracy and false-positive rate.

Resources: Low setup risk. About 20 to 40 short trajectories and 160 to 250 monitor calls are enough for a pilot. Use one agent API and one inexpensive monitoring model, a 16 GB laptop and no GPU. Budget about $5 to $30, or $30 to $75 if stronger agent models generate the logs.

What should count as convincing evidence of collusion? (2.3)
Starter code: Colosseum; ColludeBench repository. Colosseum logs support coalition-advantage and causal channel ablations. ColludeBench contains collusive environments, detector code and stored result manifests, but should be preflighted rather than treated as a turnkey bag of raw trajectories.

Weekend project: Assemble three deliberately different case types: coordinated harmful action; similar behaviour caused by common incentives without agreement; and collusive-sounding talk that never changes behaviour. Compute the same conversation, coalition-advantage and dependence evidence for every case. Choose the decision rule on half the examples, freeze it, and test on the rest.

Resources: Medium data-preparation risk; organiser-supplied logs would make this much safer. Reuse 30 to 60 trajectories and make 100 to 300 judge calls. A 16 GB laptop and no GPU are sufficient. Budget $5 to $30 with cached logs, or up to $100 if the team must generate them.

Track 3: Collusion Carriers and Countermeasures
Can actions, tools or side channels carry collusion? (3.1)
Starter code: Colosseum; collusive-llm-agents; paper. Colosseum supplies rich tool-using workflows and a private-message positive control. Lin et al.'s notebooks offer a smaller fallback in which prices or quantity vectors are the observable actions, although the notebooks use an older OpenAI setup and may need minor repair.

Weekend project: In Colosseum, replace private messaging with one ordinary observable action, such as task claiming, tag choice or tool-call order. Compare private text, action-only visibility, and the same actions hidden or canonicalised before the partner sees them. Evidence for an action carrier requires the coalition advantage to survive action-only coordination and weaken when that observation path is cut. If Colosseum is too heavy, run the same visibility ablation on quantity vectors in the Cournot notebook.

Resources: Medium-to-high setup risk; this is best with an organiser-preflighted fork or a coding agent. Run 20 to 40 short episodes on one API provider. A 16 GB laptop and no GPU should suffice; budget $15 to $75, or up to $120 for longer workflows.

Can a trusted agent expose or disrupt a coalition? (3.2)
Starter code: Voluntary Collusion; paper. The repository includes Liar's Bar and Cleanup, explicit secret-alliance controls, persistent alliance memory and logs. It was built for local Llama/Mistral/Qwen models, so the cheapest sprint route is an organiser-preflighted API adapter rather than the original H100-style setup.

Weekend project: Keep the explicit alliance condition as a positive control. Replace the experimenter-selected partner with one scripted or monitor-controlled player that offers the same non-challenge pact to each ordinary agent. Compare a direct offer, an indirect hint and a benign cooperation request, recording both verbal acceptance and repeated preferential play.

Resources: High setup risk without preflight; medium after an API adapter exists. Run 20 to 40 short games on one low-cost provider. A 16 GB laptop and no GPU are then sufficient; budget roughly $10 to $60.

Can agents identify when a peer has been replaced? (3.3)
Starter code: LLM-Trust-Breaking; focal-points. Shi et al.'s harness supports heterogeneous agent-model files and logs behaviour round by round, making it a stronger starting point than rebuilding a game. focal-points offers a cheap benign convention task if the trust games prove noisy.

Weekend project: Add a mid-run swap hook that preserves the displayed identity and transcript. Compare a sham swap, a fresh instance of the same model, a different model in the same family and a different provider. Ask for one same-or-changed guess at the end, but separately measure whether the incumbent's behaviour changes after the swap.

Resources: Low-to-medium setup risk; the swap hook is a modest code change. Run 30 to 60 short pairings, using two providers only for the final condition. A 16 GB laptop and no GPU are enough; budget approximately $10 to $60.

What does a coalition do when it learns it is being watched? (3.4)
Starter code: LLM agent collusion; paper. Agrawal et al.'s harness directly exposes communication, oversight and profit pressure, so it can test adaptation without introducing another task. A small sampling wrapper can vary how much of the message stream the monitor sees.

Weekend project: Run matched conditions with communication and no oversight; silent logging; agents told that messages are monitored; and monitoring plus profit pressure. Expose 25%, 50% or 100% of messages to the monitor, then record prices, message length and vocabulary, and dependence in bids or timing. Claim channel movement only if message-based coordination falls while action-based dependence rises; high prices alone are insufficient.

Resources: Low-to-medium setup risk. Run 20 to 40 matched market sessions on one provider. A 16 GB laptop and no GPU are sufficient; budget about $20 to $120.

Suggested reading
A curated reading list per track will be added here before the sprint. In the meantime, the papers cited under each research question on the Overview tab are the starting points.