from typing import List

from src.utils.normalize import normalize_token, sanitize_line


def tokenize(text: str) -> List[str]:
    """Divide a entrada do jogador em tokens normalizados.

    A limpeza fica toda em `src.utils.normalize`, para o texto comparado e o
    texto enviado ao jogo serem sempre o mesmo.
    """
    cleaned = sanitize_line(text)
    tokens = (normalize_token(part) for part in cleaned.split())
    return [token for token in tokens if token]