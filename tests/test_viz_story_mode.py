"""Replay page story mode (owner request 2026-10-26, docs/viz/DEMO.md). Structural checks; the browser
behaviour is checked with headless screenshots (docs/viz/DEMO.md, "Verification").

- index.html opens in STORY MODE: a #story section with a "Play the story" button and an "Explore all games"
  button; the full page (#app, the 6-row grid, the 6 cards) is unchanged and shown in full mode or with #full.
- The story headline and the final comparison are computed in app.js from window.MM_DATA: no result number is
  typed in the story code.
- Keyboard: Space, ArrowLeft, ArrowRight, R. prefers-reduced-motion is respected.
- demo.html (invented data) has no story section, and story mode never links to demo.html.
- The failed-family banner is one line with a details toggle; footer keeps "directional, 2 firms, 5 seeds".
- Captions use plain words: no "Say"/"Do"/"Nash" in the story captions.
"""
import re
from pathlib import Path

from tools import check_viz

ROOT = Path(__file__).resolve().parent.parent
VIZ = ROOT / "viz"


def read(name):
    return (VIZ / name).read_text(encoding="utf-8")


def story_js():
    js = read("app.js")
    start = js.index("// ===== STORY MODE")
    return js[start:]


def test_story_section_and_buttons_in_index():
    idx = read("index.html")
    assert 'id="story"' in idx
    assert 'id="story-play"' in idx and "Play the story" in idx
    assert 'id="story-explore"' in idx and "Explore all games" in idx
    assert 'id="app"' in idx  # full page kept
    for title in ("Pick a game", "Replay", "Inspector", "What the games say", "Prices in this game"):
        assert title in idx


def test_full_mode_hash_and_modes():
    js = story_js()
    assert '"#full"' in js
    assert "mode-story" in js and "mode-full" in js
    css = read("style.css")
    assert "mode-story" in css and "mode-full" in css


def test_story_numbers_are_computed_not_typed():
    js = story_js()
    assert "MM_DATA" in js or "D.games" in js
    # no hand-typed result: no k/n counts, no percentages, no prices with 2 decimals in the story code
    assert not re.search(r"\b\d+\s*/\s*\d+\b", re.sub(r"//[^\n]*", "", js))
    assert not re.search(r"\b\d+%", js)
    assert not re.search(r"\b[0-9]\.[0-9]{2}\b", js)


def test_story_keyboard_and_reduced_motion():
    js = story_js()
    for key in ('" "', '"ArrowLeft"', '"ArrowRight"', '"r"'):
        assert key in js, key
    assert "reduced" in js or "prefers-reduced-motion" in js


def test_story_captions_use_plain_words():
    js = story_js()
    captions = " ".join(re.findall(r'"([^"]*)"', js))
    assert "said yes" in captions and "changed their prices" in captions
    for word in ("Say ", "Say:", "Do:", "SAY", "Nash"):
        assert word not in captions, word


def test_demo_page_unreachable_from_story():
    assert 'id="story"' not in read("demo.html")
    assert "demo.html" not in story_js()
    assert "demo.html" not in read("index.html")


def test_banner_one_line_with_details_and_footer():
    js = read("app.js")
    assert "<details" in js and "<summary" in js
    assert "directional" in read("index.html") and "2 firms" in read("index.html") and "5 seeds" in read("index.html")


def test_check_viz_still_passes():
    assert check_viz.check_repo(VIZ) == []
