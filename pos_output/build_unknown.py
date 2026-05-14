from pathlib import Path
from wordfreq import top_n_list


# CONFIG
UNKNOWN_FILE = Path("unknown.txt")
OUTPUT_DIR = Path("")

RESTORED_FILE = OUTPUT_DIR / "restored.txt"
STILL_UNKNOWN_FILE = OUTPUT_DIR / "still_unknown.txt"


# VOCAB
def build_english_vocab(n: int = 100000) -> set[str]:
    words = top_n_list("en", n)
    return {w.lower() for w in words if w.isalpha()}


def restore_with_high_confidence(
    token: str,
    vocab: set[str],
    min_prefix: int = 5,
    max_extra: int = 4,
):
    token = token.lower().strip()

    if len(token) < min_prefix:
        return None

    candidates = [
        w for w in vocab
        if w.startswith(token) and 0 < len(w) - len(token) <= max_extra
    ]

    if len(candidates) == 1:
        return candidates[0]

    return None


def restore_list(tokens: list[str], vocab: set[str]):
    restored = {}
    unresolved = []

    for token in tokens:
        result = restore_with_high_confidence(token, vocab)
        if result is not None:
            restored[token] = result
        else:
            unresolved.append(token)

    return restored, unresolved


# IO
def load_unknown_tokens(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return [
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_restored(path: Path, restored: dict[str, str]) -> None:
    lines = [f"{k} -> {v}" for k, v in sorted(restored.items())]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def save_list(path: Path, items: list[str]) -> None:
    unique_sorted = sorted(set(items))
    path.write_text("\n".join(unique_sorted) + ("\n" if unique_sorted else ""), encoding="utf-8")


# MAIN
def main():
    print(f"Loading unknown tokens from: {UNKNOWN_FILE}")

    tokens = load_unknown_tokens(UNKNOWN_FILE)
    print(f"Total unknown tokens: {len(tokens)}")

    print("Building vocabulary...")
    vocab = build_english_vocab()

    restored, unresolved = restore_list(tokens, vocab)

    save_restored(RESTORED_FILE, restored)
    save_list(STILL_UNKNOWN_FILE, unresolved)

    print("\nResults:")
    print(f"Restored: {len(restored)}")
    print(f"Still unknown: {len(unresolved)}")

    print("\nFiles generated:")
    print(f"- {RESTORED_FILE}")
    print(f"- {STILL_UNKNOWN_FILE}")


if __name__ == "__main__":
    main()