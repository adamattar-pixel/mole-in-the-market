"""R18: every result number in a document must come from the reproduce outputs."""


def extract_numbers(text, include_code=False):
    raise NotImplementedError


def collect_sources(paths):
    raise NotImplementedError


def check_text(text, sources, allow=None, include_code=False):
    raise NotImplementedError


def main(argv=None):
    raise NotImplementedError


if __name__ == "__main__":
    raise SystemExit(main())
