"""
Acceptable struct:

    struct Payload {
        int   id;
        int   counter;
        char  msg[256];
        float temp;
    }
"""

import socket
from ctypes import Structure, c_int, c_char, c_float, sizeof
from typing import Optional, Set

from src.matching.matchers import build_matcher, MatchResult
from src.utils.tokenizer import tokenize
from src.config import (
    SERVER_HOST,
    SERVER_PORT,
    THRESHOLD_SUGGESTION,
    THRESHOLD_AUTO_CORRECT,
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
    if result.score == 1.0:
        return result.matched_tokens, "pass"
    if result.score >= THRESHOLD_AUTO_CORRECT:
        return result.matched_tokens, "correct"
    if result.score >= THRESHOLD_SUGGESTION:
        return raw_tokens, "suggest"
    return raw_tokens, "pass"


def log(result: MatchResult, status: str) -> None:
    raw = result.original_input
    score = result.score
    if status == "pass" and result.verb_found == result.verb_matched:
        print(f"  [OK]      '{raw}'  (verbo '{result.verb_found}' valido)")
    elif status == "pass":
        print(
            f"  [IGNORA]  '{raw}'  '{result.verb_found}' -> '{result.verb_matched}'"
            f"  score={score:.2f} (abaixo do limiar)"
        )
    elif status == "suggest":
        print(
            f"  [SUGESTAO]  '{raw}'  '{result.verb_found}' -> '{result.verb_matched}'"
            f"  score={score:.2f}"
        )
    else:
        corrected_cmd = " ".join(result.matched_tokens)
        print(
            f"  [CORRECAO] '{raw}'  '{result.verb_found}' -> '{result.verb_matched}'"
            f"  cmd='{corrected_cmd}'  score={score:.2f}"
        )


def run_server(game_words: Set[str], strategy, disable_algorithm: bool = False) -> None:
    print(f"Palavras no dicionario : {len(game_words)}")
    print(f"Limiar sugestao        : {THRESHOLD_SUGGESTION}")
    print(f"Limiar correcao        : {THRESHOLD_AUTO_CORRECT}")

    if disable_algorithm:
        print("\nModo puro: algoritmo desativado")
    else:
        print("\nCarregando matcher...", end=" ", flush=True)
        matcher = build_matcher(game_words, strategy)
        print("pronto!\n")

    payload_size = sizeof(Payload)
    server = _build_server_socket()

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