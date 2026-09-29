"""Testa quais palavras do dicionario do jogo sao aceitas como ACAO pelo Zork I.

Roda o dfrotz uma vez por palavra e olha a resposta:

* ``There was no verb in that sentence!`` -> a palavra existe, mas nao e acao;
* ``I don't know the word ...``           -> a palavra nao esta no dicionario.

Saidas (em ``tools/output/``): ``actions.txt``, ``not_actions.txt`` e
``check_for_actions_log.txt`` (log completo, com a resposta de cada palavra).

Uso (da raiz do projeto, no WSL/Linux):

    python tools/check_for_actions.py [palavras.txt]

Sem argumento, as palavras sao extraidas do proprio ``.z3``.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.paths import DFROTZ, GAME_FILE, TOOLS_OUTPUT_DIR
from src.server.frotz_server import run_server
from src.utils.normalize import sanitize_line
from tools.zmachine_dictionary import resolve_words

ACTIONS_FILE = TOOLS_OUTPUT_DIR / "actions.txt"
NOT_ACTIONS_FILE = TOOLS_OUTPUT_DIR / "not_actions.txt"
LOG_FILE = TOOLS_OUTPUT_DIR / "check_for_actions_log.txt"

UNKNOWN_MARKERS = tuple(
    sanitize_line(marker)
    for marker in (
        "i don't know the word",                # palavra fora do dicionario do jogo
        "there was no verb in that sentence!",  # palavra existe, mas nao e acao
    )
)


def save_list(path: Path, words: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(sorted(set(words))) + "\n", encoding="utf-8")
    print(f"  -> {path}")


def classify(words: list[str], game_file: Path):
    recognized: list[str] = []
    unknown: list[str] = []
    raw_lines: list[str] = []

    for index, word in enumerate(words, start=1):
        print(f"[{index}/{len(words)}] testando: {word}")

        proc = subprocess.run(
            [str(DFROTZ), str(game_file)],
            input=f"{word}\n",
            capture_output=True,
            text=True,
            timeout=30,
        )

        # saida do jogo (bem maior que uma linha de comando): sem corte de bytes
        output = sanitize_line(proc.stdout + " " + proc.stderr, max_bytes=None)
        if any(marker in output for marker in UNKNOWN_MARKERS):
            unknown.append(word)
        else:
            recognized.append(word)

        raw_lines += [f"=== {word} ===", proc.stdout.rstrip(), ""]

    return recognized, unknown, raw_lines


def _start_server_thread() -> threading.Thread:
    t = threading.Thread(
        target=run_server,
        args=(set(), None),
        kwargs={"disable_algorithm": True},
        daemon=True,
    )
    t.start()
    return t


def main() -> None:
    if not DFROTZ.exists():
        print(f"[ERRO] dfrotz nao encontrado em: {DFROTZ}")
        return

    if not GAME_FILE.exists():
        print(f"[ERRO] arquivo do jogo nao encontrado: {GAME_FILE}")
        return

    source = sys.argv[1] if len(sys.argv) > 1 else None
    words = resolve_words(source)
    print(f"Palavras: {len(words)} (fonte: {source or GAME_FILE})")

    print(f"dfrotz  : {DFROTZ}")
    print(f"Jogo    : {GAME_FILE}")
    print(f"Total   : {len(words)} palavras\n")

    print("Iniciando servidor TCP (o dfrotz com o patch precisa dele)...")
    _start_server_thread()
    time.sleep(0.5)  # aguarda o servidor subir

    recognized, unknown, raw_lines = classify(words, GAME_FILE)

    print(f"\n{'=' * 50}")
    print(f"Aceitas como acao : {len(recognized)}")
    print(f"Nao aceitas       : {len(unknown)}")
    print(f"{'=' * 50}")

    save_list(ACTIONS_FILE, recognized)
    save_list(NOT_ACTIONS_FILE, unknown)

    log_lines = ["=== ACEITAS COMO ACAO ===", *sorted(set(recognized)), ""]
    log_lines += ["=== NAO ACEITAS ===", *sorted(set(unknown)), ""]
    log_lines += ["=== LOG COMPLETO ===", *raw_lines]
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"  -> {LOG_FILE}")


if __name__ == "__main__":
    main()
