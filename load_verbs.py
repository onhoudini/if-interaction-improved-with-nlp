from pathlib import Path


def load_words_file(path: str | Path) -> set[str]:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    words = {
        line.strip().lower()
        for line in file_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }

    if not words:
        raise ValueError(f"No words found in: {file_path}")

    return words