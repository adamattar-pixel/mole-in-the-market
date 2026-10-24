"""Check the ops/ process docs (see ops/README.md).

Usage: python -m tools.check_ops [--root DIR]   (exit 0 when no problem)
"""


def ops_refs(root):
    raise NotImplementedError


def claim_errors(text):
    raise NotImplementedError


def check(root):
    raise NotImplementedError


def main(argv=None):
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
