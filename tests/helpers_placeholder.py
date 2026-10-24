"""Test helper: copies of repo configs with the model ids put back to `tbd` placeholders (test code only).

The H2 guards (a real run refuses `tbd` ids) are tested on these copies, so the tests keep their intent
whatever model ids the repo configs carry (QUESTIONS.md #21).
"""
from pathlib import Path

import yaml


def placeholder_families(n):
    return [{"family": f"family{i + 1}-tbd",
             "models": {"0": f"family{i + 1}-tbd/model-tbd", "1": f"family{i + 1}-tbd/model-tbd"}}
            for i in range(n)]


def placeholder_copy(src, dst_dir):
    """Copy of the config file `src` into `dst_dir`, same content except `tbd` model ids. Returns the path."""
    src = Path(src)
    cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
    cfg["families"] = placeholder_families(len(cfg["families"]))
    dst = Path(dst_dir) / src.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    return dst
