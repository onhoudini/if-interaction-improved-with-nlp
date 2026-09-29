"""Tabela de sinonimos curada em CSV.

Arquivo: ``data/lexicon/action.csv`` (caminho em ``src.paths.LEXICON_FILE``)::

    palavra,sinonimo1,sinonimo2

* ``palavra``   -> forma que o **jogo** entende. O dicionario do .z3 trunca em
  6 caracteres (``inventory`` -> ``invent``, ``mailbox`` -> ``mailbo``), entao a
  coluna tem que ser a forma do dicionario.
* ``sinonimoN`` -> formas que o jogador pode digitar e que devem ser trocadas
  pela ``palavra`` da propria linha antes de chegar ao jogo.

Regras de leitura (o objetivo e nunca decidir em silencio):

* o cabecalho e opcional (a primeira celula pode ser ``palavra``);
* linhas em branco e celulas vazias sao ignoradas;
* se o mesmo sinonimo aparecer em linhas diferentes, ele fica com o **primeiro**
  dono e o conflito vai para :attr:`problems` (o programa avisa no comeco da
  sessao);
* se um token tambem for a ``palavra`` de alguma linha, ele **nunca** e tratado
  como sinonimo: a forma do dicionario tem prioridade.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from src.utils.normalize import normalize_token

HEADER = ("palavra", "sinonimo1", "sinonimo2")


@dataclass(frozen=True)
class LexiconEntry:
    """Uma linha do CSV: a palavra do jogo e os sinonimos que apontam para ela."""

    canonical: str
    synonyms: tuple[str, ...]


class ActionLexicon:
    """Leitura e consulta da tabela (``sinonimo -> palavra`` e o inverso)."""

    def __init__(
        self,
        entries: Iterable[LexiconEntry] = (),
        problems: Iterable[str] = (),
    ) -> None:
        self._entries: tuple[LexiconEntry, ...] = tuple(entries)
        self._problems: list[str] = list(problems)

        canonicals: list[str] = []
        synonyms_by_canonical: dict[str, list[str]] = {}

        for entry in self._entries:
            if not entry.canonical:
                continue
            if entry.canonical in synonyms_by_canonical:
                self._problems.append(
                    f"a palavra '{entry.canonical}' aparece em mais de uma linha"
                    " (os sinonimos foram somados)"
                )
            else:
                canonicals.append(entry.canonical)
            bucket = synonyms_by_canonical.setdefault(entry.canonical, [])
            for synonym in entry.synonyms:
                if synonym and synonym not in bucket:
                    bucket.append(synonym)

        canonical_set = set(canonicals)
        owner: dict[str, str] = {}

        for canonical in canonicals:
            for synonym in synonyms_by_canonical[canonical]:
                if synonym in canonical_set:
                    self._problems.append(
                        f"'{synonym}' e palavra do dicionario do jogo e tambem"
                        f" aparece como sinonimo em '{canonical}': sera tratado"
                        " como palavra do dicionario (a linha nao faz efeito)"
                    )
                    continue
                first = owner.get(synonym)
                if first is None:
                    owner[synonym] = canonical
                elif first != canonical:
                    self._problems.append(
                        f"sinonimo '{synonym}' aparece em '{first}' e em"
                        f" '{canonical}': mantido apenas em '{first}'"
                    )

        self._canonicals: tuple[str, ...] = tuple(canonicals)
        self._canonical_of: dict[str, str] = owner
        self._synonyms_of: dict[str, tuple[str, ...]] = {
            canonical: tuple(
                synonym
                for synonym in synonyms_by_canonical[canonical]
                if owner.get(synonym) == canonical
            )
            for canonical in canonicals
        }

    # ------------------------------------------------------------------ #
    # Construcao
    # ------------------------------------------------------------------ #
    @classmethod
    def from_csv(cls, path: str | Path) -> "ActionLexicon":
        """Carrega o CSV. Arquivo ausente ou so com cabecalho devolve lexico vazio."""
        file_path = Path(path)
        if not file_path.exists():
            return cls(problems=(f"arquivo do lexico nao encontrado: {file_path}",))

        entries: list[LexiconEntry] = []
        problems: list[str] = []
        header_checked = False

        with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
            for line_number, row in enumerate(csv.reader(handle), start=1):
                raw_cells = [cell.strip() for cell in row]
                if not any(raw_cells):
                    continue

                cells = [normalize_token(cell) for cell in raw_cells]

                # o cabecalho e a primeira linha com conteudo (nao precisa ser a 1)
                if not header_checked:
                    header_checked = True
                    if cells[0] == normalize_token(HEADER[0]):
                        continue

                canonical = cells[0]
                if not canonical:
                    problems.append(
                        f"linha {line_number}: sem a coluna '{HEADER[0]}'"
                        f" (linha ignorada: {','.join(raw_cells)})"
                    )
                    continue

                synonyms: list[str] = []
                for raw_cell, cell in zip(raw_cells[1:], cells[1:]):
                    if not cell or cell == canonical:
                        continue
                    if " " in raw_cell:
                        # a troca acontece token a token: sinonimo composto nao
                        # teria como ser reconhecido, entao fica de fora
                        problems.append(
                            f"linha {line_number}: sinonimo com espaco"
                            f" '{raw_cell}' ignorado (precisa ser uma unica"
                            " palavra)"
                        )
                        continue
                    synonyms.append(cell)

                entries.append(LexiconEntry(canonical, tuple(synonyms)))

        return cls(entries, problems)

    # ------------------------------------------------------------------ #
    # Consulta
    # ------------------------------------------------------------------ #
    def canonical_for(self, token: str) -> str | None:
        """Palavra do jogo correspondente ao token digitado (ou None)."""
        return self._canonical_of.get(normalize_token(token))

    def synonyms_of(self, canonical: str) -> tuple[str, ...]:
        """Sinonimos cadastrados para uma palavra do jogo."""
        return self._synonyms_of.get(normalize_token(canonical), ())

    @property
    def canonicals(self) -> tuple[str, ...]:
        """Palavras do jogo (primeira coluna do CSV)."""
        return self._canonicals

    @property
    def synonyms(self) -> tuple[str, ...]:
        """Todos os sinonimos, na ordem de cadastro."""
        return tuple(self._canonical_of.keys())

    @property
    def entries(self) -> tuple[str, ...]:
        """Palavras + sinonimos: candidatos do autocomplete (TAB)."""
        return self._canonicals + self.synonyms

    @property
    def problems(self) -> tuple[str, ...]:
        """Conflitos encontrados no CSV (ambiguidade, palavra repetida etc.)."""
        return tuple(self._problems)

    @property
    def is_empty(self) -> bool:
        return not self._canonicals

    def __len__(self) -> int:
        return len(self._canonicals)

    def __bool__(self) -> bool:
        return bool(self._canonicals)

    def __repr__(self) -> str:
        return (
            f"ActionLexicon(palavras={len(self._canonicals)},"
            f" sinonimos={len(self._canonical_of)}, problemas={len(self._problems)})"
        )
