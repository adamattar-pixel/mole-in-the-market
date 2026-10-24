"""R19: submission checks on the report source (Markdown or LaTeX). Page count is MANUAL."""

APPENDIX_TITLE = "Limitations and Dual-Use / Ethical Considerations"


def count_words(text):
    raise NotImplementedError


def extract_urls(text):
    raise NotImplementedError


def check_text(text, expected_title=None, fetch=None, repo_root=None):
    raise NotImplementedError


def overall(result):
    raise NotImplementedError


def main(argv=None):
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
