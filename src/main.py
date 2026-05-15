import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import GAME_FILE, SIMILARITY_STRATEGY
from src.server.frotz_server import run_server
from src.utils.load_verbs import load_words_file
from src.zmachine.zmachine_dictionary import extract_dictionary, _print_summary


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERBS_FILE = PROJECT_ROOT / "data" / "pos_output" / "verbs.txt"
REVIEW_VERBS_FILE = PROJECT_ROOT / "data" / "dictionaries" / "actions.txt"


def parse_mode() -> str:
    if len(sys.argv) > 1 and sys.argv[1] in {"0", "1"}:
        return sys.argv[1]
    return "1"


def load_game_dictionary(game_file: str) -> set[str]:
    print("Extracting dictionary...", end=" ", flush=True)
    words, separators = extract_dictionary(game_file)
    _print_summary(words, separators, game_file)
    print(f"{len(words)} words (seperator: {separators})")
    return set(words)


def load_candidate_verbs(mode: str) -> set[str]:
    if mode == "0":
        return set()

    verbs_file = REVIEW_VERBS_FILE if mode == "1" else VERBS_FILE
    print(f"Loading verbs from: {verbs_file}")
    return load_words_file(verbs_file)


def main() -> None:
    mode = parse_mode()
    game_file = GAME_FILE

    print(f"\nJogo: {game_file}")
    print(f"Modo: {'frotz puro' if mode == '0' else 'com algoritmo'}")

    if not Path(game_file).exists():
        print(f"[ERROR] Archive '{game_file}' not found.")
        sys.exit(1)

    game_words = load_game_dictionary(game_file)
    candidate_verbs = load_candidate_verbs(mode)

    strategy = SIMILARITY_STRATEGY()
    print(f"Similarity strategy: {strategy.__class__.__name__}\n")

    run_server(
        candidate_verbs if mode != "0" else game_words,
        strategy,
        disable_algorithm=(mode == "0"),
    )


if __name__ == "__main__":
    main()