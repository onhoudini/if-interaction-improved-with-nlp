import sys
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Iterable, Set

from src.matching.matchers import build_matcher
from src.config import THRESHOLD_SUGGESTION, THRESHOLD_AUTO_CORRECT
from src.server.frotz_server import run_server


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_lines(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _log_line(log_path: Path, line: str) -> None:
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _status_from_score(score: float) -> str:
    if score == 1.0:
        return "pass"
    if score >= THRESHOLD_AUTO_CORRECT:
        return "correct"
    if score >= THRESHOLD_SUGGESTION:
        return "suggest"
    return "pass"


def _format_server_line(result, status: str) -> str:
    raw = result.original_input
    score = result.score
    if status == "pass" and result.verb_found == result.verb_matched:
        return f"[SERVER] [OK] '{raw}' verbo='{result.verb_found}' score={score:.2f}"
    if status == "pass":
        return (
            f"[SERVER] [IGNORA] '{raw}' '{result.verb_found}' -> '{result.verb_matched}' "
            f"score={score:.2f}"
        )
    if status == "suggest":
        return (
            f"[SERVER] [SUGESTAO] '{raw}' '{result.verb_found}' -> '{result.verb_matched}' "
            f"score={score:.2f}"
        )
    corrected_cmd = " ".join(result.matched_tokens)
    return (
        f"[SERVER] [CORRECAO] '{raw}' '{result.verb_found}' -> '{result.verb_matched}' "
        f"cmd='{corrected_cmd}' score={score:.2f}"
    )


def _start_reader_thread(proc: subprocess.Popen, log_path: Path) -> threading.Thread:
    def _reader():
        for line in iter(proc.stdout.readline, ""):
            if line == "":
                break
            line = line.rstrip("\n")
            print(line)
            _log_line(log_path, f"[GAME] {line}")

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return t


def _start_server_thread(game_words, strategy) -> threading.Thread:
    t = threading.Thread(
        target=run_server,
        args=(game_words, strategy),
        kwargs={"disable_algorithm": True},  # so pra satisfazer o dfrotz sem corrigir aqui
        daemon=True,
    )
    t.start()
    return t


def run_dfrotz_proxy(
    dfrotz_path: Path,
    game_file: Path,
    game_words: Set[str],
    strategy,
    logs_dir: Path,
) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_ts = _timestamp()
    session_log = logs_dir / f"session_{session_ts}.txt"

    _log_line(session_log, f"[META] dfrotz={dfrotz_path}")
    _log_line(session_log, f"[META] game={game_file}")
    _log_line(session_log, f"[META] started={session_ts}")

    matcher = build_matcher(game_words, strategy)

    _start_server_thread(game_words, strategy)

    proc = subprocess.Popen(
        [str(dfrotz_path), str(game_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    _start_reader_thread(proc, session_log)

    try:
        while True:
            try:
                user_input = input()
            except EOFError:
                break

            raw = user_input.strip()
            if not raw:
                continue

            result = matcher.match(raw)
            status = _status_from_score(result.score)
            server_line = _format_server_line(result, status)

            _log_line(session_log, f"[INPUT] {raw}")
            _log_line(session_log, server_line)
            # print(server_line)

            final_tokens = result.matched_tokens
            if status == "correct" and result.verb_found and result.verb_matched:
                final_tokens = final_tokens.copy()
                try:
                    idx = final_tokens.index(result.verb_found)
                    final_tokens[idx] = result.verb_matched
                except ValueError:
                    pass

            final_cmd = " ".join(final_tokens)
            proc.stdin.write(final_cmd + "\n")
            proc.stdin.flush()

            if status == "suggest" and result.verb_matched:
                suggestion = f"< Perhaps, do you mean '{result.verb_matched}'?"
                print(suggestion)
                _log_line(session_log, f"[GAME] {suggestion}")

    finally:
        try:
            proc.terminate()
        except Exception:
            pass