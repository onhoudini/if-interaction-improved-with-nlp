"""
Testa quais verbos do verbs.txt são reconhecidos como ações pelo Zork I.
# Roda o dfrotz uma vez por palavra.
Saidas:
- logs.txt (na pasta do script): aceitas, nao aceitas e log completo
- actions.txt (em data/dictionaries): palavras aceitas
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DFROTZ = PROJECT_ROOT / "frotz-master" / "dfrotz"
GAME_FILE = PROJECT_ROOT / "frotz-master" / "games" / "zork1-r88-s840726.z3"
VERBS_FILE = PROJECT_ROOT / "data" / "dictionaries" / "zork1-r119-s880429_dictionary.txt"

ACTIONS_FILE = PROJECT_ROOT / "data" / "dictionaries" / "actions.txt"
NOT_ACTIONS_FILE = PROJECT_ROOT / "data" / "dictionaries" / "not-actions.txt"
LOG_FILE = Path(__file__).resolve().parent / "logs.txt"

UNKNOWN_MARKERS = [
    "i don't know the word", # retira palavras falsas/lixo do dicionário do jogo
    "there was no verb in that sentence!" # verificar verbo utilizável, ação
]


def load_verbs(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {path}")
    words = [
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not words:
        raise ValueError(f"Nenhuma palavra encontrada em: {path}")
    return words


def save_actions(path: Path, recognized: list[str]) -> None:
    path.write_text("\n".join(sorted(recognized)) + "\n", encoding="utf-8")
    print(f"\nAcoes salvas em: {path}")

def save_not_actions(path: Path, unknown: list[str]) -> None:
    path.write_text("\n".join(sorted(unknown)) + "\n", encoding="utf-8")
    print(f"\nNao acoes salvas em: {path}")

def classify_words(words: list[str], game_file: Path) -> tuple[dict[str, str], list[str]]:
    results: dict[str, str] = {}
    raw_lines: list[str] = []

    for i, word in enumerate(words, start=1):
        print(f"[{i}/{len(words)}] Testando: {word}")

        proc = subprocess.run(
            [str(DFROTZ), "-m", str(game_file)],
            input=f"{word}\n",
            capture_output=True,
            text=True,
            timeout=30,
        )

        output = proc.stdout.lower()
        is_unknown = any(marker in output for marker in UNKNOWN_MARKERS)
        results[word] = "unknown" if is_unknown else "recognized"

        raw_lines.append(f"=== {word} ===")
        raw_lines.append(proc.stdout.rstrip())
        raw_lines.append("")

    return results, raw_lines


def main() -> None:
    if not DFROTZ.exists():
        print(f"[ERRO] dfrotz nao encontrado em: {DFROTZ}")
        return

    if not GAME_FILE.exists():
        print(f"[ERRO] Arquivo do jogo nao encontrado: {GAME_FILE}")
        return

    print(f"dfrotz : {DFROTZ}")
    print(f"Jogo   : {GAME_FILE}")
    print(f"Verbos : {VERBS_FILE}")

    verbs = load_verbs(VERBS_FILE)
    print(f"Total de verbos para testar: {len(verbs)}\n")

    print("Executando dfrotz... (pode demorar)")
    results, raw_lines = classify_words(verbs, GAME_FILE)

    recognized = [w for w, s in results.items() if s == "recognized"]
    unknown = [w for w, s in results.items() if s == "unknown"]

    print(f"\n{'='*50}")
    print(f"Reconhecidas pelo jogo : {len(recognized)}")
    print(f"Nao reconhecidas       : {len(unknown)}")
    print(f"{'='*50}")

    log_lines: list[str] = []
    log_lines.append("=== RECONHECIDAS PELO JOGO ===")
    log_lines.extend(sorted(recognized))
    log_lines.append("")
    log_lines.append("=== NAO RECONHECIDAS ===")
    log_lines.extend(sorted(unknown))
    log_lines.append("")
    log_lines.append("=== LOG COMPLETO ===")
    log_lines.extend(raw_lines)

    LOG_FILE.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"\nLog salvo em: {LOG_FILE}")

    save_actions(ACTIONS_FILE, recognized)
    save_not_actions(NOT_ACTIONS_FILE, unknown)


if __name__ == "__main__":
    main()