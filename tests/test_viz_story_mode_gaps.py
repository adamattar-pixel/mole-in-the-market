"""Gap test for tests/test_viz_story_mode.py (locked 7f3d534): a key string such as " " also appears elsewhere
in the story code, so check that the keydown handler itself compares e.key with each demo key."""
import re
from pathlib import Path

JS = (Path(__file__).resolve().parent.parent / "viz" / "app.js").read_text(encoding="utf-8")
STORY = JS[JS.index("// ===== STORY MODE"):]


def test_story_keydown_handler_maps_each_key():
    handler = STORY[STORY.index('addEventListener("keydown"'):]
    handler = handler[:handler.index("});") + 3]
    for key in (" ", "ArrowLeft", "ArrowRight", "r"):
        assert re.search(r'e\.key === "' + re.escape(key) + '"', handler), key
