import re
from pathlib import Path

CYRILLIC = re.compile(r"[\u0400-\u04ff]")
ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".html", ".css", ".js", ".md", ".json", ".toml", ".yml"}


def test_public_project_is_english_only() -> None:
    violations: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
            continue
        if any(part in {".git", ".venv", ".pytest_cache", ".ruff_cache"} for part in path.parts):
            continue
        if CYRILLIC.search(path.read_text(encoding="utf-8")):
            violations.append(str(path.relative_to(ROOT)))
    assert violations == []
