"""Ponto de entrada da ferramenta.

    python src/main.py 1   # tabela de sinonimos + sugestoes (padrao)
    python src/main.py 0   # frotz puro: nada e trocado nem sugerido (controle)

Fluxo da sessao:

1. o dicionario de palavras e extraido do proprio arquivo do jogo (.z3);
2. a tabela de sinonimos (`data/lexicon/action.csv`) e carregada;
3. o `dfrotz` sobe como subprocesso e o `src/server/dfrotz_runner.py` cuida da
   conversa com o jogador.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import SIMILARITY_STRATEGY
from src.lexicon.action_lexicon import ActionLexicon
from src.paths import DFROTZ, GAME_FILE, LEXICON_FILE, LOGS_DIR
from src.server.dfrotz_runner import run_dfrotz_proxy
# o decodificador do dicionario do .z3 mora em tools/ (e compartilhado com os
# scripts offline de la)
from tools.zmachine_dictionary import extract_dictionary


def parse_mode() -> str:
    if len(sys.argv) > 1 and sys.argv[1] in {"0", "1"}:
        return sys.argv[1]
    return "1"


def load_game_dictionary(game_file: Path) -> set[str]:
    """Palavras que o jogo conhece (extraidas do .z3 em tempo de execucao)."""
    print("Extraindo dicionario do jogo...", end=" ", flush=True)
    words, separators = extract_dictionary(str(game_file))
    print(f"{len(words)} palavras (separadores: {separators})")
    return set(words)


def load_lexicon(mode: str) -> ActionLexicon:
    """Tabela de sinonimos. No modo 0 volta vazia (nada e processado)."""
    if mode == "0":
        return ActionLexicon()

    lexicon = ActionLexicon.from_csv(LEXICON_FILE)
    print(f"Lexico     : {LEXICON_FILE}")
    print(
        f"             {len(lexicon)} palavras do jogo,"
        f" {len(lexicon.synonyms)} sinonimos"
    )
    if lexicon.is_empty:
        print(
            "[AVISO] o lexico esta vazio (so o cabecalho): nenhum sinonimo vai"
            " ser trocado."
        )
    for problem in lexicon.problems:
        print(f"[AVISO] lexico: {problem}")
    return lexicon


def save_actions_used(canonicals: Iterable[str]) -> None:
    """Guarda as palavras carregadas na sessao (copia com e sem timestamp)."""
    canonicals = sorted(canonicals)
    if not canonicals:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    actions_used = LOGS_DIR / "actions_used.txt"
    timestamped = (
        LOGS_DIR / f"actions_used_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    )
    content = "\n".join(canonicals) + "\n"
    actions_used.write_text(content, encoding="utf-8")
    timestamped.write_text(content, encoding="utf-8")


def main() -> None:
    mode = parse_mode()
    label = (
        "frotz puro (sem processamento)"
        if mode == "0"
        else "com tabela de sinonimos"
    )

    print(f"\nJogo : {GAME_FILE}")
    print(f"Modo : {label}")

    if not GAME_FILE.exists():
        print(f"[ERROR] Archive '{GAME_FILE}' not found.")
        sys.exit(1)

    if not DFROTZ.exists():
        print(f"[ERROR] dfrotz not found: {DFROTZ}")
        sys.exit(1)

    game_words = load_game_dictionary(GAME_FILE)
    lexicon = load_lexicon(mode)

    strategy = None
    if mode != "0":
        strategy = SIMILARITY_STRATEGY()
        print(f"Similaridade: {strategy.__class__.__name__} (apenas sugestoes)\n")
        save_actions_used(lexicon.canonicals)

    run_dfrotz_proxy(
        DFROTZ,
        GAME_FILE,
        game_words,
        strategy,
        LOGS_DIR,
        lexicon=lexicon,
        autocomplete_entries=lexicon.entries if mode != "0" else None,
        mode=mode,
    )


if __name__ == "__main__":
    main()
