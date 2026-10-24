# Visual replay page - design brief
Purpose: let the team explore results. It displays results, it never produces any. Dark dashboard style inspired by GridReady (idea only, no code or assets copied).

Status: OPTIONAL, Phase 8 (see PLAN.md). The report figure R27 comes first.

## Layout
3 columns then a lower band (stack in one column on narrow screens).

- Left, "Pick a game": a grid of pixels, one per game. Rows = conditions (A, E, B, B_T, C, D, labelled with their names), columns = family 1 seeds 1 to 5 then family 2 seeds 1 to 5. Pixel color = outcome: say and do (green), say only (amber), do only (violet), neither (grey). Selected pixel outlined in white. Hover tooltip: condition, family, seed, outcome label. Legend underneath.
- Center, "Replay": SVG scene. Two shops shown as pixel houses with a price bar each (height = price), horizontal reference lines for the Nash price (dotted grey) and the deal price (dashed amber) with a faint band of plus or minus 10 percent of the Nash to monopoly gap around the deal price. A pixel-art mole spy with a hat and sunglasses pops up from a mound at the round of the offer, with a speech bubble containing the offer text, and dashed lines animate toward the shops at that round. Reply chips (accept, decline, no reply) above each shop from the offer round. Condition A shows "No spy in this condition". Below: Play/Pause button and a round slider with a mark at the offer round and a shaded window for the 3 following rounds. Selecting a pixel starts playback from round 1. Respect prefers-reduced-motion.
- Right, "Inspector": one-sentence headline of the game (for example "A shop said yes, but its prices did not follow."), SAY and DO chips (yes or no), the offer text, each shop's reply, and the definitions of say and do in two lines.
- Lower left, "What the games say": one card per condition with the share of games that said yes and the share that moved prices (large numbers), each with a bar showing the 95 percent Wilson interval and a dot for the rate, a strip of the 10 games as colored mini pixels, and the number of games. Clicking a card selects that condition's next game.
- Lower right, "Prices in this game": line chart of both shops (blue and pink) over the rounds, reference lines, vertical dashed line at the offer round, shaded window for the 3 following rounds, current-round marker with dots, end labels spread so they do not overlap, hover tooltip with round and prices, click to move the replay.
- A one-sentence takeaway under the header with counts computed from the data.

## Palette
background #14171b, line #2a313a, text #e8ecf1, muted #8b96a5, say #3ddc97, say-only #f0b429, do-only #a78bfa, none #3a4350, shop 1 #60a5fa, shop 2 #f472b6.

## Wording
Use the allowed phrases of PREREGISTRATION and the v7 table ("in this game", "directional"). Never write "agents trust" or any general claim.

## Banner
Whenever meta.synthetic is true, a permanent banner "DEMO DATA | NOT RESULTS" is shown.

## Data contract
Files are produced by `reproduce`, never written by hand.
- viz/data/games.csv: game_id, condition, condition_name, family, seed, say, do, outcome (say_do, say_only, do_only, neither), nash, monopoly, deal_price, spy_start, rounds
- viz/data/rounds.csv: game_id, round, firm, price, reply (accept, decline, no_message at the offer round, empty elsewhere)
- viz/data/messages.csv: condition, text (the FROZEN texts from PREREGISTRATION.md, never new wording)
- viz/data/meta.json: {synthetic: false, source_checksum, prereg_hash, generated_at}
- viz/data/data.js: the same content as `window.MM_DATA = {...}`, so that viz/index.html opens by double click (browsers block fetch on local files).
