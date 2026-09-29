"""Valida a tabela de sinonimos (`data/lexicon/action.csv`) contra o jogo.

Uso (da raiz do projeto):

    python tools/validate_lexicon.py [arquivo.csv]

Checagens:

* ``[ERRO]`` a ``palavra`` nao existe no dicionario do ``.z3`` -> a troca
  enviaria ao jogo algo que ele nao conhece;
* ``[ERRO]`` sinonimo repetido em linhas diferentes (ambiguidade de destino);
* ``[ERRO]`` sinonimo com espaco, ou igual a propria ``palavra``;
* ``[ERRO]`` linha com numero de colunas diferente do cabecalho;
* ``[AVISO]`` sinonimo que o jogo **ja** conhece -> a linha nao faz efeito
  (quando o jogador digita, a camada "o jogo conhece a palavra" deixa passar);
* ``[AVISO]`` ``palavra`` repetida em mais de uma linha;
* ``[AVISO]`` sinonimo igual a ``palavra`` de outra linha (conflito de
  prioridade: o runtime trata como palavra do jogo).

O relatorio tambem e salvo em ``tools/output/lexicon_report.txt``.
"""

import csv
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.lexicon.action_lexicon import HEADER, ActionLexicon
from src.paths import GAME_FILE, LEXICON_FILE, TOOLS_OUTPUT_DIR
from src.utils.normalize import normalize_token
from tools.zmachine_dictionary import extract_dictionary

REPORT_FILE = TOOLS_OUTPUT_DIR / "lexicon_report.txt"


def load_rows(path: Path) -> tuple[list[list[str]], list[str]]:
    """Linhas cruas do CSV (sem normalizar), preenchidas ate o tamanho do cabecalho.

    Guardar as celulas originais permite detectar sinonimos compostos
    ("cast off"), que perdem o espaco ao serem normalizados.
    """
    rows: list[list[str]] = []
    issues: list[str] = []
    header_checked = False

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for line_number, row in enumerate(csv.reader(handle), start=1):
            raw_cells = [cell.strip() for cell in row]
            if not any(raw_cells):
                continue

            if len(raw_cells) > len(HEADER):
                issues.append(
                    f"[ERRO] linha {line_number}: {len(raw_cells)} colunas (esperado"
                    f" {len(HEADER)}) -> {'|'.join(raw_cells)}"
                )

            # o cabecalho e a primeira linha com conteudo (nao precisa ser a 1)
            if not header_checked:
                header_checked = True
                if normalize_token(raw_cells[0]) == normalize_token(HEADER[0]):
                    if len(raw_cells) != len(HEADER):
                        issues.append(
                            f"[ERRO] linha {line_number}: cabecalho com"
                            f" {len(raw_cells)} colunas (esperado {len(HEADER)}:"
                            f" {','.join(HEADER)})"
                        )
                    continue

            rows.append(raw_cells + [""] * (len(HEADER) - len(raw_cells)))

    return rows, issues


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else LEXICON_FILE

    lines: list[str] = []

    def emit(message: str = "") -> None:
        print(message)
        lines.append(message)

    emit(f"Arquivo    : {csv_path}")
    if not csv_path.exists():
        emit("[ERRO] arquivo nao encontrado")
        return

    game_words = set(extract_dictionary(str(GAME_FILE))[0])
    emit(f"Jogo       : {GAME_FILE} ({len(game_words)} palavras no dicionario)")
    emit()

    rows, issues = load_rows(csv_path)
    errors = [issue for issue in issues if issue.startswith("[ERRO]")]
    warnings = [issue for issue in issues if issue.startswith("[AVISO]")]

    owner_of: dict[str, str] = {}
    canonicals: list[str] = []
    synonyms_seen = 0
    dead_entries = 0

    for index, raw_cells in enumerate(rows, start=2):  # a linha 1 e o cabecalho
        canonical = normalize_token(raw_cells[0])
        synonyms_raw = raw_cells[1:]
        line_label = f"linha {index}"

        if not canonical:
            errors.append(f"[ERRO] {line_label}: sem a coluna 'palavra'")
            continue

        if canonical in canonicals:
            warnings.append(
                f"[AVISO] {line_label}: palavra '{canonical}' repetida em outra linha"
            )
        canonicals.append(canonical)

        if canonical not in game_words:
            errors.append(
                f"[ERRO] {line_label}: palavra '{canonical}' nao existe no"
                " dicionario do jogo"
            )

        if len(canonical) > 6:
            warnings.append(
                f"[AVISO] {line_label}: palavra '{canonical}' tem mais de 6"
                " caracteres (o dicionario do Zork I trunca em 6)"
            )

        filled = 0
        for raw_synonym in synonyms_raw:
            if not raw_synonym:
                continue
            filled += 1

            if " " in raw_synonym:
                errors.append(
                    f"[ERRO] {line_label}: sinonimo '{raw_synonym}' tem espaco"
                    " (a troca acontece palavra por palavra: use uma unica palavra"
                    " ou ajuste a tabela)"
                )
                continue

            synonym = normalize_token(raw_synonym)

            if synonym == canonical:
                errors.append(
                    f"[ERRO] {line_label}: sinonimo '{synonym}' igual a propria"
                    " palavra"
                )
                continue

            synonyms_seen += 1

            previous = owner_of.get(synonym)
            if previous is None:
                owner_of[synonym] = canonical
            elif previous != canonical:
                errors.append(
                    f"[ERRO] {line_label}: sinonimo '{synonym}' ja aponta para"
                    f" '{previous}' (ambiguidade: escolha apenas uma palavra)"
                )
                continue

            if synonym in canonicals and synonym != canonical:
                warnings.append(
                    f"[AVISO] {line_label}: sinonimo '{synonym}' e palavra do"
                    " dicionario em outra linha (essa linha nao faz efeito)"
                )

            if synonym in game_words:
                dead_entries += 1
                warnings.append(
                    f"[AVISO] {line_label}: sinonimo '{synonym}' ja e conhecido"
                    " pelo jogo (a linha nao faz efeito; serve como documentacao)"
                )

        if filled == 0:
            warnings.append(
                f"[AVISO] {line_label}: palavra '{canonical}' sem nenhum sinonimo"
            )

    emit(f"Linhas     : {len(rows)}")
    emit(f"Palavras   : {len(canonicals)}")
    emit(f"Sinonimos  : {synonyms_seen} ({dead_entries} ja conhecidos pelo jogo)")
    emit()

    if errors:
        emit(f"=== {len(errors)} ERRO(S) ===")
        for error in errors:
            emit(error)
        emit()

    if warnings:
        emit(f"=== {len(warnings)} AVISO(S) ===")
        for warning in warnings:
            emit(warning)
        emit()

    lexicon = ActionLexicon.from_csv(csv_path)
    if lexicon.problems:
        emit("=== avisos do proprio runtime (ActionLexicon) ===")
        for problem in lexicon.problems:
            emit(f"  {problem}")
        emit()

    emit(f"Resultado  : {'REPROVADO' if errors else 'OK'}")
    emit("(erros impedem a troca silenciosa funcionar; avisos sao informativos)")

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nRelatorio salvo em: {REPORT_FILE}")


if __name__ == "__main__":
    main()
