"""Limpeza e normalizacao da entrada do jogador.

Ha dois papeis diferentes (antes havia tres normalizacoes espalhadas pelo
projeto, cada uma fazendo uma coisa diferente):

* ``sanitize_line``  -> o texto que vai ser ENVIADO ao dfrotz. A entrada vem do
  terminal, entao pode ter acento, emoji, caractere de controle, sequencia
  ANSI, tabulacao e linha longa demais.
* ``normalize_token`` -> o texto usado para COMPARAR (lexico/matching).

Por que limpar: o jogo (Zork I, Z-machine v3) so conhece as palavras do
dicionario dele -- ASCII, sem acento e sem pontuacao -- e a mensagem trocada
com o dfrotz pela socket e um ``char msg[256]`` (o lado C faz ``strncpy`` de
255 bytes), entao linha maior que isso e descartada silenciosamente.
"""

from __future__ import annotations

import re
import unicodedata

MAX_LINE_BYTES = 255

# Sequencias de escape ANSI (cor, posicionamento de cursor) coladas na linha
_ANSI_ESCAPES = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
# Caracteres de controle (inclui \t, \x00 e \x7f)
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
# Mantem letras, numeros, espaco, apostrofo e hifen; todo o resto vira espaco.
# Apostrofo e hifen so valem no MEIO da palavra (o dicionario do Zork tem
# entradas como "air-p" e "don't"); nas pontas eles sao removidos.
_KEEP_CHARS = re.compile(r"[^a-z0-9\s'\-]")
_EDGE_PUNCTUATION = re.compile(r"^['\-]+|['\-]+$")


def strip_accents(text: str) -> str:
    """Troca caracteres acentuados pela letra base (café -> cafe)."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def _truncate_bytes(text: str, max_bytes: int | None) -> str:
    if not max_bytes:
        return text
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", "ignore").strip()


def sanitize_line(raw: str, max_bytes: int | None = MAX_LINE_BYTES) -> str:
    """Devolve a linha pronta para ser enviada ao jogo.

    - remove escapes ANSI e caracteres de controle;
    - remove acentos e passa para minusculas;
    - troca pontuacao por espaco (o Zork usa ``.``, ``,`` e ``"`` como
      separadores, entao a pontuacao nao agrega informacao para o parser);
    - colapsa espacos repetidos e corta a linha em ``max_bytes``.

    Passe ``max_bytes=None`` quando o texto **nao** for ir para o jogo (por
    exemplo, para analisar a saida dele, que e bem maior que uma linha de
    comando).
    """
    text = _ANSI_ESCAPES.sub(" ", raw)
    text = _CONTROL_CHARS.sub(" ", text)
    text = strip_accents(text).lower()
    text = _KEEP_CHARS.sub(" ", text)
    text = " ".join(text.split())
    return _truncate_bytes(text, max_bytes)


def normalize_token(token: str) -> str:
    """Devolve a forma canonica de UM token, para comparacao com o lexico.

    A diferenca para ``sanitize_line`` e que aqui nao ha limite de tamanho e o
    resultado nunca tem espaco: e o que se compara com o dicionario do jogo e
    com a tabela de sinonimos.
    """
    text = strip_accents(token).lower()
    text = _KEEP_CHARS.sub("", text)
    text = _EDGE_PUNCTUATION.sub("", text)
    return text
