import sys
from pathlib import Path
from datetime import datetime

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import GAME_FILE, SIMILARITY_STRATEGY
from src.utils.load_verbs import load_words_file
from src.zmachine.zmachine_dictionary import extract_dictionary, _print_summary
from src.server.dfrotz_runner import run_dfrotz_proxy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACTIONS_FILE = PROJECT_ROOT / "data" / "dictionaries" / "actions.txt"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
DFROTZ_PATH = PROJECT_ROOT / "frotz-master" / "dfrotz"


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

    verbs_file = ACTIONS_FILE
    print(f"Loading verbs from: {verbs_file}")
    return load_words_file(verbs_file)


def save_actions_used(words: set[str]) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    actions_used = LOGS_DIR / "actions_used.txt"
    timestamped = LOGS_DIR / f"actions_used_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    content = "\n".join(sorted(words)) + "\n"
    actions_used.write_text(content, encoding="utf-8")
    timestamped.write_text(content, encoding="utf-8")


def main() -> None:
    mode = parse_mode()
    game_file = GAME_FILE

    print(f"\nJogo: {game_file}")
    print(f"Modo: {'frotz puro' if mode == '0' else 'com algoritmo'}")

    if not Path(game_file).exists():
        print(f"[ERROR] Archive '{game_file}' not found.")
        sys.exit(1)

    if not DFROTZ_PATH.exists():
        print(f"[ERROR] dfrotz not found: {DFROTZ_PATH}")
        sys.exit(1)

    game_words = load_game_dictionary(game_file)
    candidate_verbs = load_candidate_verbs(mode)

    if mode != "0":
        save_actions_used(candidate_verbs)

    strategy = SIMILARITY_STRATEGY()
    print(f"Similarity strategy: {strategy.__class__.__name__}\n")

    if mode == "0":
        words = game_words
    else:
        words = candidate_verbs

    run_dfrotz_proxy(
        DFROTZ_PATH,
        game_file,
        words,
        strategy,
        LOGS_DIR,
    )


if __name__ == "__main__":
    main()