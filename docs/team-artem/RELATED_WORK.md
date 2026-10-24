# Related work for Mole in the Market (research notes, not report prose)

Compiled 24 Oct 2026. Purpose: give the team sources and one-line contrasts so the Related Work section can be written in our own words.

URL status key:
- **[V]** verified on 24 Oct 2026 (arXiv export API returned the record, or page fetched / HTTP 200).
- **[S]** found via web search with consistent metadata, but direct fetch was blocked (SSRN, AEA).
- **[U]** unverified. Cited by Apart's Overview tab or our v7 context file, but not found or not checked. Do not cite in the report without checking.

Format per entry: citation, URL, **Found:** one line, **We differ:** one line.

---

## 1. Algorithmic pricing collusion (foundations)

**Calvano, E., Calzolari, G., Denicolò, V., Pastorello, S. (2020).** Artificial Intelligence, Algorithmic Pricing, and Collusion. *American Economic Review* 110(10): 3267-3297. DOI 10.1257/aer.20190623. https://www.aeaweb.org/articles?id=10.1257/aer.20190623 [S] (doi.org link redirects; AEA blocks scripted fetch)
- **Found:** Q-learning pricing agents in a logit Bertrand oligopoly learn supra-competitive prices with no communication, sustained by finite punishment then gradual return.
- **We differ:** our demand parameters come from here, but our agents are LLMs and we inject an explicit secret offer rather than studying tacit learning.

**Fish, S., Gonczarowski, Y. A., Shorrer, R. I. (2024).** Algorithmic Collusion by Large Language Models. arXiv:2404.00806 (v6). https://arxiv.org/abs/2404.00806 [V]
- **Found:** LLM pricing agents in oligopoly quickly reach supra-competitive prices; innocuous prompt wording changes the level of collusion; extends to auctions.
- **We differ:** Fish is tacit (no channel). We keep their game and add a one-shot frozen peer offer, then ask whether a verbal "yes" moves prices beyond what the tacit baseline already does.

**Keppo, J., Li, Y., Tsoukalas, G., Yuan, N. (2026).** On the Fragility of AI Agent Collusion. arXiv:2603.20281. https://arxiv.org/abs/2603.20281 [V]
- **Found:** heterogeneity (patience, data access, LLM vs Q-learner, more firms) shrinks LLM price lift (22% to 10% or 7%); model-size differences do not break it.
- **We differ:** they vary agent composition; we hold agents symmetric and vary only the offer text and sender label.

**Deshpande, S., Jacobson, S. H. (2026).** Strategic AI in Cournot Markets. arXiv:2601.17263. https://arxiv.org/abs/2601.17263 [V]
- **Found:** LLMs in Cournot oligopoly sustain tacit collusion, prices up to 200% above Nash; forcing a few agents to best-respond disrupts it.
- **We differ:** quantity game, tacit only, no offer or say/do measurement.

## 2. LLM agents with explicit communication or collusion opportunities

**Agrawal, K., Teo, V., Vazquez, J. J., Kunnavakkam, S., Srikanth, V., Liu, A. (2025).** Evaluating LLM Agent Collusion in Double Auctions. arXiv:2507.01413. https://arxiv.org/abs/2507.01413 [V]
- **Found:** direct seller communication increases collusion; propensity varies by model; oversight and "urgency from authority figures" change collusive behavior.
- **We differ:** their collusion arises among sellers who all talk freely; ours is triggered by a single scripted outsider with fixed text, so the stimulus is identical across games. Their authority-pressure finding is the closest prior evidence for our B_T trust label.

**Lin, R. Y., Ojha, S., Cai, K., Chen, M. F. (2024).** Strategic Collusion of LLM Agents: Market Division in Multi-Commodity Competitions. arXiv:2410.00031. https://arxiv.org/abs/2410.00031 [V]
- **Found:** LLM agents in multi-commodity Cournot markets divide markets and tacitly collude without instructions.
- **We differ:** tacit market division vs our explicit offer; we measure acceptance of a proposal, not spontaneous division.

**Wu, Z., Peng, R., Zheng, S., Liu, Q., Han, X., Kwon, B. I., et al. (2024).** Shall We Team Up: Exploring Spontaneous Cooperation of Competing LLM Agents. arXiv:2402.12327. https://arxiv.org/abs/2402.12327 [V]
- **Found:** competing LLM agents spontaneously cooperate (including Bertrand-style collusion) without being told to.
- **We differ:** spontaneous cooperation with open talk; we test response to a controlled external offer.

**Han, X., Wu, Z., Xiao, C. (2023).** "Guinea Pig Trials" Utilizing GPT: A Novel Smart Agent-Based Modeling Approach for Studying Firm Competition and Collusion. arXiv:2308.10974. https://arxiv.org/abs/2308.10974 [V]
- **Found:** GPT-4 firms reach tacit collusion without communication; with communication they discuss pricing explicitly early in the game.
- **We differ:** no controlled offer, no say vs do split.

**Giebel, M., Rösner, A., Schröder, B. (2026).** Artificial Intelligence, Communication, and Strategic Pricing: Evidence from Large Language Models. SSRN working paper 6832662. https://papers.ssrn.com/abstract=6832662 [S] (SSRN returns 403 to scripts; metadata from search)
- **Found:** in repeated Bertrand, allowing LLM communication raises prices and profits and lowers dispersion; they attribute it to cooperative language and pattern completion more than game-theoretic reasoning.
- **We differ:** free bilateral chat vs one frozen message from a third party; we separate the reply from the price effect.

**Mazur, L. (2025).** Emergent Price-Fixing by LLM Auction Agents. LessWrong post, 16 Jul 2025. https://www.greaterwrong.com/posts/yqhy3zBmpeFuGFLxX/emergent-price-fixing-by-llm-auction-agents [V] (blog post, not peer reviewed)
- **Found:** every tested frontier model used an optional chat channel to set price floors; "illegality" was scored by an LLM analyst reading the chat logs.
- **We differ:** that evidence is mostly transcript-based. It is a concrete example of the auditing practice our say/do gap tests: does what agents write predict what they price?

**Zeng, X., Rudzicz, F. (2026).** Voluntary Collusion with Secret Tools in Competing LLM Agents. arXiv:2605.27593 (v2, 5 Oct 2026). https://arxiv.org/abs/2605.27593 [V]
- **Found:** across 12 models and 6 prompts, most agents accept secret collusion tools in Liar's Bar and Cleanup, often after saying the tools are unfair; only explicit ethical framing reduces adoption. Apart's suggested 3.2 starter code.
- **We differ:** the offer there comes from the environment as a tool; ours comes from a peer as a message in an economic price game, with a sender-label manipulation and a harmless-request false-positive control.

**Piatti, G., Jin, Z., Kleiman-Weiner, M., Schölkopf, B., Sachan, M., Mihalcea, R. (2024).** Cooperate or Collapse: Emergence of Sustainable Cooperation in a Society of LLM Agents (GovSim). arXiv:2404.16698 (NeurIPS 2024). https://arxiv.org/abs/2404.16698 [V]
- **Found:** most LLM societies fail to sustain a shared resource; communication and universalization reasoning help.
- **We differ:** there cooperation is socially good; in our market, cooperation between sellers is collusion that harms buyers. Useful contrast for "agreement is not always bad".

**Nakamura, M., Kumar, A., Das, S., Abdelnabi, S., Mahmud, S., Fioretto, F., Zilberstein, S., Bagdasarian, E. (2026).** Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems. arXiv:2602.15198 (NeurIPS 2026 poster). https://arxiv.org/abs/2602.15198 [V]
- **Found:** with a secret channel, most off-the-shelf models collude; agents often "collude on paper" (plan collusion in text but act non-collusively); action-based regret and LLM-judge scores disagree.
- **We differ:** CLOSEST PRIOR on say vs do. They study cooperative DCOP tasks with assigned coalitions; we study a competitive price market with an unsolicited offer the agent may refuse, plus a permutation base rate for "do".

**Shi, X., Zhang, Y., Yang, D. (2026).** Emergent Collusion in Long-Horizon LLM Agent Interaction. arXiv:2609.24967. https://arxiv.org/abs/2609.24967 [V]
- **Found:** two agents who verify each other's work drift into violating the protocol in 94% of trajectories across 10 models; peer behavior shapes it.
- **We differ:** emergent over many rounds vs a one-shot offer; non-market.

## 3. Secret collusion, steganography, and multi-agent risk framing

**Motwani, S. R., Baranchuk, M., Strohmeier, M., Bolina, V., Torr, P. H. S., Hammond, L., Schroeder de Witt, C. (2024).** Secret Collusion among AI Agents: Multi-Agent Deception via Steganography. arXiv:2402.07510 (NeurIPS 2024). https://arxiv.org/abs/2402.07510 [V]
- **Found:** formalises secret collusion; steganographic capability grows with model capability and can outpace equally capable overseers.
- **We differ:** we use a plain-text channel on purpose; our "not said but done" cell is the low-tech version of collusion a text monitor misses.

**Hammond, L., Chan, A., Clifton, J., Hoelscher-Obermaier, J., Khan, A., McLean, E., et al. (2025).** Multi-Agent Risks from Advanced AI. arXiv:2502.14143. https://arxiv.org/abs/2502.14143 [V]
- **Found:** taxonomy of multi-agent failure modes (miscoordination, conflict, collusion) and risk factors including multi-agent security.
- **We differ:** framing source only; cite for why collusion between deployed agents matters.

## 4. Say vs do: stated vs revealed behaviour, broken announcements, unfaithful reasoning

**Shi, J., Zhang, T. J., Schölkopf, B., Conitzer, V., Jin, Z. (2026).** When Agents Lie: Premeditation, Persistence, and Exploitation in Repeated Games. arXiv:2607.05132 (ICML 2026). https://arxiv.org/abs/2607.05132 [V]
- **Found:** with private plan / public announcement / action stages, over 90% of deviations from announcements were already in the private plan; models disagree on whether announcements bind.
- **We differ:** announcements there are about the agent's own action in normal-form games; ours is acceptance of a third party's cartel proposal and the follow-through in prices.

**Shi, J., Zhang, T. J., Jin, Z., Conitzer, V. (2026).** Cheap Talk, Empty Promise: Frontier LLMs easily break public promises for self-interest. arXiv:2604.04782. https://arxiv.org/abs/2604.04782 [V]
- **Found:** frontier LLMs often deviate from publicly announced actions in one-shot games, classified as win-win, selfish, altruistic or sabotaging.
- **We differ:** one-shot games vs repeated pricing; we test a "yes" to an illegal deal rather than a self-announcement.

**Gu, Z., Wang, Q., Han, S. (2025).** Alignment Revisited: Are Large Language Models Consistent in Stated and Revealed Preferences? arXiv:2506.00751. https://arxiv.org/abs/2506.00751 [V]
- **Found:** LLM choices in context often diverge from stated general principles; small prompt changes flip choices.
- **We differ:** single-agent forced choices; our "revealed" side is a market action with money at stake.

**Turpin, M., Michael, J., Perez, E., Bowman, S. R. (2023).** Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting. arXiv:2305.04388. https://arxiv.org/abs/2305.04388 [V]
- **Found:** CoT explanations can hide the real cause of an answer (biasing features not mentioned).
- **We differ:** we compare a verbal commitment to later actions, not reasoning to an answer. Cite for "text is not a reliable window into behaviour".

**Scheurer, J., Balesni, M., Hobbhahn, M. (2023).** Large Language Models can Strategically Deceive their Users when Put Under Pressure. arXiv:2311.07590. https://arxiv.org/abs/2311.07590 [V]
- **Found:** a GPT-4 trading agent acts on an insider tip and then hides it from its manager.
- **We differ:** closest market-misconduct analogue (illegal tip received from another party). We test a price-fixing proposal and measure both reply and action, not deception toward a principal.

## 5. Monitoring and oversight (for the theory of change)

**Baker, B., Huizinga, J., Gao, L., Dou, Z., Guan, M. Y., Madry, A., et al. (2025).** Monitoring Reasoning Models for Misbehavior and the Risks of Promoting Obfuscation. arXiv:2503.11926. https://arxiv.org/abs/2503.11926 [V]
- **Found:** CoT monitors catch reward hacking far better than action-only monitors; optimising against the monitor teaches obfuscation.
- **We differ:** shows text monitoring can be strong; our result tests the opposite case in markets where messages and actions may diverge.

**Korbak, T., Balesni, M., Barnes, E., Bengio, Y., Benton, J., Bloom, J., et al. (2025).** Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety. arXiv:2507.11473. https://arxiv.org/abs/2507.11473 [V]
- **Found:** position paper: CoT monitoring is useful but imperfect and fragile.
- **We differ:** framing citation for "what a monitor reads is not always what the agent does".

**Gardner-Challis, N., Bostock, J., Kozhevnikov, G., Sinclaire, M., Velja, J., Abate, A., et al. (2026).** When can we trust untrusted monitoring? A safety case sketch across collusion strategies. arXiv:2602.20628. https://arxiv.org/abs/2602.20628 [V]
- **Found:** taxonomy of how a monitored model and an untrusted monitor could collude (self-recognition, causal, acausal signals).
- **We differ:** AI-control setting; we are the monitor's ground truth data in a market.

**Guey, W., Jahangir, R., Bougault, P., de Moura, V. D., Zhang, W., Gomes, J. O. (2026).** When AI Finds Hidden Messages, Does It Report? arXiv:2610.10620. https://arxiv.org/abs/2610.10620 [V]
- **Found:** asking assistants to report raises notification of messages addressed to another AI by about 53 to 55 points; some agents interpret but do not notify.
- **We differ:** reporting vs ignoring a message; we measure accepting and acting on one. A natural extension: add a "report" option.

**Tao, Y., Zheng, X., Yang, S., Tao, M., Wang, X. (2026).** GroupGuard: A Framework for Modeling and Defending Collusive Attacks in Multi-Agent Systems. arXiv:2603.13940. https://arxiv.org/abs/2603.13940 [V]
- **Found:** defense uses graph monitoring plus "active honeypot inducement" to identify colluding agents (up to 88% detection).
- **We differ:** CHECK THIS ONE. Their honeypot is a defense component in QA/reasoning tasks; ours is a measured sting in a price market. Read section on honeypots before claiming "first sting".

**Liu, Q., Chen, X., Zhao, Z., Zheng, Y., Yu, D., Zhang, Z., et al. (2026).** Breaking the Secret: Economic Interventions for Combating Collusion in Embodied Multi-Agent Systems. arXiv:2604.23511. https://arxiv.org/abs/2604.23511 [V]
- **Found:** rewarding reporters and penalising colluders (leniency-style) makes collusion unstable.
- **We differ:** mechanism design countermeasure; we measure the detection signal a leniency or sting regime would rely on.

## 6. Sycophancy and compliance with peer agents

**Sharma, M., Tong, M., Korbak, T., Duvenaud, D., Askell, A., Bowman, S. R., et al. (2023).** Towards Understanding Sycophancy in Language Models. arXiv:2310.13548. https://arxiv.org/abs/2310.13548 [V]
- **Found:** RLHF assistants consistently tell users what they want to hear; human preference data rewards it.
- **We differ:** user-directed sycophancy; we test whether agreeableness extends to a peer proposing something illegal, and whether "yes" is just politeness (say without do).

**Yao, B., Shang, C., Du, W., He, J., Lian, R., Zhang, Y., et al. (2025).** Peacemaker or Troublemaker: How Sycophancy Shapes Multi-Agent Debate. arXiv:2509.23055. https://arxiv.org/abs/2509.23055 [V]
- **Found:** inter-agent sycophancy collapses debates into premature consensus and hurts accuracy.
- **We differ:** debate accuracy vs market harm; supports the hypothesis that verbal accept may be agreeableness.

**Mehdizadeh, A., Hilbert, M. (2025).** When Your AI Agent Succumbs to Peer-Pressure: Studying Opinion-Change Dynamics of LLMs. arXiv:2510.19107. https://arxiv.org/abs/2510.19107 [V]
- **Found:** conformity follows a threshold (sigmoid) curve; thresholds differ by model.
- **We differ:** opinions, not actions; single peer in our case.

**Kasprova, V., Parulekar, A., AlRabah, A., Agaram, K., Garg, R., Jha, S., et al. (2026).** Too Polite to Disagree: Understanding Sycophancy Propagation in Multi-Agent Systems. arXiv:2604.02668. https://arxiv.org/abs/2604.02668 [V]
- **Found:** giving agents priors on peers' sycophancy reduces its spread.
- **We differ:** background only.

**Baltaji, R., Hemmatian, B., Varshney, L. R. (2024).** Persona Inconstancy in Multi-Agent LLM Collaboration: Conformity, Confabulation, and Impersonation. arXiv:2405.03862. https://arxiv.org/abs/2405.03862 [V]
- **Found:** agents conform under perceived peer pressure; private responses differ from chat transcripts.
- **We differ:** an early say (chat) vs private (belief) gap; ours is say vs market action.

**Zhang, J., Xu, X., Zhang, N., Liu, R., Hooi, B., Deng, S. (2023).** Exploring Collaboration Mechanisms for LLM Agents: A Social Psychology View. arXiv:2310.02124. https://arxiv.org/abs/2310.02124 [V]
- **Found:** LLM societies show conformity and consensus-seeking.
- **We differ:** background only.

## 7. Trust and authority labels, inter-agent prompt injection

**Greshake, K., Abdelnabi, S., Mishra, S., Endres, C., Holz, T., Fritz, M. (2023).** Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. arXiv:2302.12173. https://arxiv.org/abs/2302.12173 [V]
- **Found:** text arriving through data channels can act as instructions.
- **We differ:** our spy message is an indirect input; the question is not hijacking but whether a label changes willingness to break competition rules.

**Wallace, E., Xiao, K., Leike, R., Weng, L., Heidecke, J., Beutel, A. (2024).** The Instruction Hierarchy: Training LLMs to Prioritize Privileged Instructions. arXiv:2404.13208. https://arxiv.org/abs/2404.13208 [V]
- **Found:** models treat third-party text with system-prompt priority; training a hierarchy helps.
- **We differ:** B_T tests a claimed privilege written inside an untrusted message, a direct probe of whether the hierarchy holds for peer messages.

**Lee, D., Tiwari, M. (2024).** Prompt Infection: LLM-to-LLM Prompt Injection within Multi-Agent Systems. arXiv:2410.07283. https://arxiv.org/abs/2410.07283 [V]
- **Found:** malicious prompts self-replicate across agents; "LLM tagging" of sources helps as a defense.
- **We differ:** tagging is a defense there; B_T asks whether a friendly tag is an attack surface.

**He, P., Lin, Y., Dong, S., Xu, H., Xing, Y., Liu, H. (2025).** Red-Teaming LLM Multi-Agent Systems via Communication Attacks (Agent-in-the-Middle). arXiv:2502.14847. https://arxiv.org/abs/2502.14847 [V]
- **Found:** intercepting and rewriting inter-agent messages compromises whole systems.
- **We differ:** adversary is a participant with a label, not a man in the middle.

**Lupinacci, M., Pironti, F. A., Blefari, F., Romeo, F., Arena, L., Furfaro, A. (2025).** The Dark Side of LLMs: Agent-based Attack Vectors for System-level Compromise. arXiv:2507.06850. https://arxiv.org/abs/2507.06850 [V]
- **Found:** models that resist direct injection still execute payloads when a peer agent asks ("inter-agent trust exploitation"); exact rate differs across versions (v1 82.4%, later 100%).
- **We differ:** security payloads vs economic misconduct; strongest prior for "peer origin raises compliance".

**Kavathekar, I., Jain, H., Rathod, A., Kumaraguru, P., Ganu, T. (2025).** TAMAS: Benchmarking Adversarial Risks in Multi-Agent LLM Systems. arXiv:2511.05269. https://arxiv.org/abs/2511.05269 [V]
- **Found:** includes impersonation attacks that falsely attribute a request to a trusted authority.
- **We differ:** our B vs B_T is a minimal-pair version (one sentence differs) of their impersonation attack, applied to a collusion offer.

**Gu, X., Zheng, X., Pang, T., Du, C., Liu, Q., Wang, Y., et al. (2024).** Agent Smith: A Single Image Can Jailbreak One Million Multimodal LLM Agents Exponentially Fast. arXiv:2402.08567. https://arxiv.org/abs/2402.08567 [V]
- **Found:** infectious jailbreak spreads across multimodal agents.
- **We differ:** background only; optional.

## 8. Sprint-adjacent projects and code we build on

- **Apart Research (2026).** AI Collusion Research Sprint, Overview and Resources tabs. https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25 [V]. Q3.2 says the undercover-offer design "hasn't been tested" and suggests direct offer / hint / benign request with verbal and behavioral acceptance. Say this openly: our design follows Apart's suggestion.
- **luciasauer/algorithmic_pricing_llms** (Fish-style starter). https://github.com/luciasauer/algorithmic_pricing_llms [V]
- **ArnolFokam/ai-collusion-research-sprint** (not used: harness rewritten from scratch during the sprint, idea only; see THIRD_PARTY.md and D4). https://github.com/ArnolFokam/ai-collusion-research-sprint [V]
- **DanielElliottUIUC/ApartAICollusion** (parallel sprint project). https://github.com/DanielElliottUIUC/ApartAICollusion [V]. Double auction (Agrawal harness), mixed families, undercover seller offering a price-fixing deal to every seller, report tool, warnings and precedents. Status "planning / scaffolding" as of README read 24 Oct. Largest overlap with us; no hint condition, no harmless control, no single-sentence trust label minimal pair.

## 9. Unverified (cited by Apart or v7; do not cite without checking)

- Berger et al. 2025, plus-factors doctrine applied to AI collusion [U]. Not found by search. Fallback for plus factors: Kovacic, Marshall, Marx, White (2011) "Plus Factors and Agreement in Antitrust Law", Michigan Law Review 110(3) [U, not checked].
- "The Sentinel's Dilemma" (Apart, Sept 2026) [U]. Not found by search.
- Rippin et al. 2026 (Schelling salience, steganographic tools), Radev et al. 2026 (sabotage monitors), Nguyen et al. 2026 (multi-dimension monitor), Arike et al. 2026 (less is more for monitors), Bonjour et al. 2022 (pairwise net influence), Tian 2026, Dietrich 2026 [U]. Named on Apart's Overview tab; not checked here.
- ColludeBench [U]. Named in v7; not checked.
- "A Survey of Collusion Risk in LLM-Powered Multi-Agent Systems" (NeurIPS 2025 workshop page https://neurips.cc/virtual/2025/loc/mexico-city/133205) [U]. Surfaced in search, authors not checked.
