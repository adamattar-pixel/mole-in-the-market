# Mole in the Market
Do AI sellers accept a secret price-fixing offer from a peer, and do they change their prices? Apart AI Collusion Research Sprint 2026, track 3.2.

Status: work in progress (see HANDOFF.md and PLAN.md).

## Authors
- Artem (project owner from 2026-10-24)
- Adam Attar (adamattar-pixel)

Affiliations: to be filled by the authors.

## One-minute idea
A spy script offers both sellers of a 2-firm price game the same secret deal ("let's both keep price X"). We measure what they say (accept or decline) and what they do (their prices over the next 3 rounds).

## Run
```
pip install -r requirements.txt
python -m pytest
python -m tools.run configs/espion_dry.yaml            # dry run with the mock client (no key)
python -m tools.reproduce runs results --viz-dir viz/data --figures-dir figures   # every table from runs/, no key
python -m tools.validate_e runs                        # positive control E, PASS/FAIL per family
```
Real runs need the owner's GO, the OpenRouter key and the 2 model families (see HANDOFF.md).

## Preexisting vs new work (required by the sprint rules)
No third-party code is reused; the harness was written during the sprint. The tag `preexisting-baseline` holds only scaffolding. See THIRD_PARTY.md for borrowed ideas and references.

## Dual-use note
Offer texts are frozen and published as is. We report effect sizes and representative excerpts only, not an optimized playbook.
