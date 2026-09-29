"""Payload trocado com o dfrotz (mesmo layout do struct do lado C):

    struct Payload {
        int   id;
        int   counter;
        char  msg[256];
        float temp;
    }

`_process_payload` so reescreve ``msg`` -- e por ele que passa a linha que o
jogador digitou. Com ``disable_algorithm=True`` o servidor apenas devolve o
payload recebido: nesse caso quem decide e o `dfrotz_runner`.
"""

import socket
from ctypes import Structure, c_int, c_char, c_float, sizeof
from typing import Optional, Set

from src.lexicon.action_lexicon import ActionLexicon
from src.matching.matchers import build_matcher, MatchResult
from src.paths import LEXICON_FILE
from src.utils.tokenizer import tokenize
from src.config import (
    SERVER_HOST,
    SERVER_PORT,
    SUGGESTION_THRESHOLD,
)


class Payload(Structure):
    _fields_ = [
        ("id", c_int),
        ("counter", c_int),
        ("msg", c_char * 256),
        ("temp", c_float),
    ]


def _build_server_socket() -> socket.socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((SERVER_HOST, SERVER_PORT))
    server.listen(3)
    return server


def _recv_exact(client: socket.socket, expected_size: int) -> bytes:
    data = b""
    while len(data) < expected_size:
        chunk = client.recv(expected_size - len(data))
        if not chunk:
            break
        data += chunk
    return data


def _decode_input(payload: Payload) -> str:
    return payload.msg.decode("utf-8").rstrip("\x00").strip()


def _set_payload_message(payload: Payload, command_tokens: list[str]) -> None:
    command = (" ".join(command_tokens) + "\n").encode("utf-8")[:255]
    padded = command.ljust(256, b"\x00")
    payload.msg = padded


def _process_payload(
    payload_bytes: bytes,
    matcher,
    payload_size: int,
    disable_algorithm: bool,
) -> Optional[Payload]:
    if len(payload_bytes) < payload_size:
        return None

    payload = Payload.from_buffer_copy(payload_bytes)

    if disable_algorithm:
        return payload

    raw_input = _decode_input(payload)
    if not raw_input:
        return payload

    raw_tokens = tokenize(raw_input)
    result = matcher.match(raw_input)
    final_tokens, status = interpret(result, raw_tokens)
    log(result, status)
    _set_payload_message(payload, final_tokens)
    return payload


def interpret(result: MatchResult, raw_tokens: list[str]) -> tuple[list[str], str]:
    """O que deve ser enviado ao jogo e o status da decisao.

    Espelha as camadas de `src/matching/matchers.py`: so a tabela de sinonimos
    troca o comando (e o faz em silencio); sugestao nao troca nada.
    """
    if result.status in {"ok", "sinonimo"}:
        return result.matched_tokens, result.status
    return raw_tokens, result.status


def log(result: MatchResult, status: str) -> None:
    """Linha de log da decisao tomada (usada so quando o servidor decide)."""
    raw = result.original_input
    score = result.score

    if status == "ok":
        print(f"  [OK]       '{raw}'  (palavra '{result.verb_found}' que o jogo conhece)")
    elif status == "sinonimo":
        corrected_cmd = " ".join(result.matched_tokens)
        print(
            f"  [SINONIMO] '{raw}'  '{result.verb_found}' -> '{result.verb_matched}'"
            f"  cmd='{corrected_cmd}'"
        )
    elif status == "sugestao":
        print(
            f"  [SUGESTAO] '{raw}'  '{result.verb_found}' -> '{result.verb_matched}'"
            f"  score={score:.2f}"
        )
    else:
        print(f"  [PASSA]    '{raw}'")


def run_server(game_words: Set[str], strategy, disable_algorithm: bool = False) -> None:
    print(f"Palavras no dicionario : {len(game_words)}")
    print(f"Limiar de sugestao     : {SUGGESTION_THRESHOLD}")

    if disable_algorithm:
        print("\nServidor em passthrough (a decisao fica no dfrotz_runner)")
    else:
        print("\nCarregando matcher...", end=" ", flush=True)
        matcher = build_matcher(
            ActionLexicon.from_csv(LEXICON_FILE), game_words, strategy
        )
        print("pronto!\n")

    payload_size = sizeof(Payload)
    try:
        server = _build_server_socket()
    except OSError as exc:
        print(
            f"\n[ERRO] Nao consegui abrir o servidor em {SERVER_HOST}:{SERVER_PORT}"
            f" ({exc})."
        )
        print(
            "       Ja existe outra sessao do jogo rodando (ou um processo antigo"
            " ficou preso)."
        )
        print(
            "       Feche a outra sessao (ou encerre o processo antigo) e rode"
            " novamente."
        )
        print(
            "       Sem o servidor o dfrotz encerra no primeiro comando enviado"
            ' ("ERROR: Unable to connect to server").'
        )
        return

    try:
        print(f"Aguardando conexoes em {SERVER_HOST}:{SERVER_PORT}")
        print("=" * 60)

        while True:
            client, _ = server.accept()
            try:
                payload_bytes = _recv_exact(client, payload_size)
                response_payload = _process_payload(
                    payload_bytes,
                    matcher if not disable_algorithm else None,
                    payload_size,
                    disable_algorithm,
                )

                if response_payload is None:
                    continue

                client.sendall(bytes(response_payload))

            except Exception as exc:
                print(f"  [ERRO] {exc}")
            finally:
                client.close()

    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
    finally:
        server.close()