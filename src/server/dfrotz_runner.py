"""Sobe o dfrotz como subprocesso e conversa com o jogador.

Responsabilidades:

* le a linha digitada pelo jogador, limpa (`src.utils.normalize`) e decide o que
  enviar ao jogo (`src.matching.matchers`);
* repassa a saida do jogo para o terminal **no momento em que ela e escrita**
  (inclusive o prompt ``>``, que vem sem quebra de linha);
* registra tudo em ``data/logs/session_<timestamp>.txt``.

Do lado do jogador nada e anunciado: quando um sinonimo e trocado pela palavra
do dicionario, a tela nao mostra nada; o unico aviso que aparece e a sugestao
(`Perhaps, do you mean 'X'?`) da camada 3 do matcher.
"""

import codecs
import sys
import threading
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Iterable, Optional

from src.config import (
    AUTOCOMPLETE_ENABLED,
    AUTOCOMPLETE_MIN_PREFIX,
    AUTOCOMPLETE_MAX_SUGGESTIONS,
    AUTOCOMPLETE_SIMILAR_SUGGESTIONS,
    SUGGESTION_THRESHOLD,
    VERBOSE_SERVER_LINES,
)
from src.lexicon.action_lexicon import ActionLexicon
from src.matching.matchers import (
    STATUS_OK,
    STATUS_PASS,
    STATUS_RAW,
    STATUS_SUGGEST,
    STATUS_SYNONYM,
    MatchResult,
    build_matcher,
)
from src.server.frotz_server import run_server
from src.utils.normalize import sanitize_line
from src.utils.verb_completer import enable_verb_autocomplete


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class SessionLog:
    """Log da sessao, escrito por uma unica thread de cada vez.

    O arquivo recebe linhas de duas threads: a principal escreve
    ``[INPUT]``/``[SERVER]`` e a thread leitora escreve ``[GAME]``. Abrir e
    fechar o arquivo a cada linha (``open(path, "a")``) nao e seguro aqui: no
    WSL o projeto vive em ``/mnt/c`` (drvfs/OneDrive), onde o append concorrente
    pode sobrescrever ou perder linhas -- foi exatamente o que apareceu num
    teste (uma linha truncada e um ``[INPUT]`` que sumiu do log). Com um unico
    arquivo aberto e um lock, cada linha entra inteira e na ordem.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = path.open("a", encoding="utf-8")
        self._lock = threading.Lock()
        self._closed = False

    def write(self, line: str) -> None:
        with self._lock:
            if self._closed:
                return
            self._handle.write(line + "\n")
            self._handle.flush()

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                self._handle.close()
            except Exception:
                pass


def _log_line(log: SessionLog, line: str) -> None:
    """Escreve uma linha no log da sessao."""
    log.write(line)


def _format_server_line(result: MatchResult) -> str:
    """Linha de log da decisao tomada para o comando."""
    raw = result.original_input
    score = result.score

    if result.status == STATUS_RAW:
        return f"[SERVER] [PURO] '{raw}' (modo 0: sem processamento)"

    if result.status == STATUS_OK:
        return (
            f"[SERVER] [OK] '{raw}' palavra='{result.verb_found}'"
            " (o jogo conhece a palavra)"
        )

    if result.status == STATUS_SYNONYM:
        corrected = " ".join(result.matched_tokens)
        return (
            f"[SERVER] [SINONIMO] '{raw}' '{result.verb_found}' ->"
            f" '{result.verb_matched}' cmd='{corrected}' (trocado em silencio)"
        )

    if result.status == STATUS_SUGGEST:
        return (
            f"[SERVER] [SUGESTAO] '{raw}' '{result.verb_found}' ->"
            f" '{result.verb_matched}' score={score:.2f}"
        )

    if result.verb_matched:
        return (
            f"[SERVER] [PASSA] '{raw}' '{result.verb_found}'"
            f" (melhor: '{result.verb_matched}' score={score:.2f})"
        )
    return f"[SERVER] [PASSA] '{raw}'"


def _start_reader_thread(proc: subprocess.Popen, log: SessionLog) -> threading.Thread:
    """Repassa a saida do jogo para o terminal assim que o dfrotz a escreve.

    O dfrotz (interface *dumb*) imprime o prompt ``>`` e da ``fflush`` ANTES de
    ler o comando do jogador, mas esse prompt NAO termina com ``\\n``. Ler o
    subprocesso com ``readline()`` (ou ``for line in proc.stdout``) deixa o
    prompt preso no buffer de linha ate o proximo ``\\n`` chegar -- e esse
    proximo ``\\n`` so chega depois que o jogador digita algo. Efeito visivel:
    o ``>`` (a "seta" que avisa que e a vez do jogador) nunca aparece; o jogo
    parece estar esperando entrada sem indicar nada.

    Alem disso, o dfrotz escreve em blocos (buffer de stdio + flush a cada
    prompt), entao aqui lemos os bytes crus em pedacos e escrevemos no stdout
    imediatamente, inclusive linhas parciais como o prompt.
    """

    binary_stream = getattr(proc.stdout, "buffer", None)
    decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def _reader():
        pending = ""
        while True:
            try:
                if binary_stream is not None:
                    chunk = binary_stream.read1(4096)
                else:  # pragma: no cover - stream text-only (sem buffer binario)
                    chunk = proc.stdout.read(1)
            except (OSError, ValueError):
                break

            if not chunk:
                break

            text = decoder.decode(chunk) if binary_stream is not None else chunk
            if not text:
                continue

            # 1) terminal: escreve e da flush na hora (inclusive o '>')
            sys.stdout.write(text)
            sys.stdout.flush()

            # 2) log: continua registrando linha a linha, como antes
            pending += text
            while "\n" in pending:
                line, pending = pending.split("\n", 1)
                _log_line(log, f"[GAME] {line.rstrip(chr(13))}")

        if pending:  # ultima linha sem '\n' (ex.: jogo encerrado no prompt)
            _log_line(log, f"[GAME] {pending}")

    t = threading.Thread(target=_reader, daemon=True)
    t.start()
    return t


def _start_server_thread(game_words, strategy) -> threading.Thread:
    """Sobe o servidor TCP que o dfrotz (com o patch) exige no primeiro comando.

    Aqui o servidor apenas devolve o payload recebido: a decisao fica toda no
    matcher deste modulo (`src/matching/matchers.py`).
    """
    t = threading.Thread(
        target=run_server,
        args=(game_words, strategy),
        kwargs={"disable_algorithm": True},
        daemon=True,
    )
    t.start()
    return t


def _build_verb_recommender(strategy, candidates: Iterable[str]):
    """Fallback do TAB: sugere uma parecida quando nada comeca com o prefixo."""

    candidates = tuple(candidates)

    def recommend(prefix: str) -> list[str]:
        if not candidates or strategy is None:
            return []
        best, score = strategy.find_best(prefix, candidates)
        if best and score >= SUGGESTION_THRESHOLD:
            return [best]
        return []

    return recommend


def _enable_verb_autocomplete(entries: Optional[Iterable[str]], strategy) -> bool:
    """Liga o TAB na lista de palavras + sinonimos do lexico (so a 1a palavra)."""
    entries = tuple(entries or ())
    if not entries or not AUTOCOMPLETE_ENABLED:
        return False

    recommend = (
        _build_verb_recommender(strategy, entries)
        if AUTOCOMPLETE_SIMILAR_SUGGESTIONS
        else None
    )
    enabled = enable_verb_autocomplete(
        entries,
        min_prefix=AUTOCOMPLETE_MIN_PREFIX,
        recommend=recommend,
        max_recommendations=AUTOCOMPLETE_MAX_SUGGESTIONS,
    )
    if enabled:
        print(
            "[AUTOCOMPLETE] TAB completa apenas o verbo (primeira palavra); "
            f"{len(entries)} entradas carregadas (lexico + sinonimos)."
        )
    return enabled


def run_dfrotz_proxy(
    dfrotz_path: Path,
    game_file: Path,
    game_words: set[str],
    strategy,
    logs_dir: Path,
    lexicon: Optional[ActionLexicon] = None,
    autocomplete_entries: Optional[Iterable[str]] = None,
    mode: str = "1",
) -> None:
    """Roda uma sessao de jogo.

    ``mode="0"`` desliga todo o processamento: a linha do jogador so passa pela
    limpeza de entrada e vai direto para o jogo (grupo de controle).
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    session_ts = _timestamp()
    session_log = SessionLog(logs_dir / f"session_{session_ts}.txt")
    lexicon = lexicon or ActionLexicon()

    _log_line(session_log, f"[META] dfrotz={dfrotz_path}")
    _log_line(session_log, f"[META] game={game_file}")
    _log_line(session_log, f"[META] started={session_ts}")
    _log_line(session_log, f"[META] modo={mode}")
    _log_line(
        session_log,
        f"[META] lexico={len(lexicon)} palavras, {len(lexicon.synonyms)} sinonimos",
    )
    for problem in lexicon.problems:
        _log_line(session_log, f"[META] lexico-aviso={problem}")

    matcher = None
    if mode != "0":
        matcher = build_matcher(lexicon, game_words, strategy)

    _start_server_thread(game_words, strategy)

    proc = subprocess.Popen(
        [str(dfrotz_path), str(game_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    reader = _start_reader_thread(proc, session_log)
    autocomplete_on = _enable_verb_autocomplete(autocomplete_entries, strategy)
    _log_line(
        session_log,
        "[META] autocomplete="
        + ("on" if autocomplete_on else "off")
        + (
            f" entradas={len(tuple(autocomplete_entries or ()))}"
            if autocomplete_on
            else ""
        ),
    )

    try:
        while True:
            try:
                user_input = input()
            except EOFError:
                break

            if not user_input.strip():
                continue

            if matcher is None:
                sanitized = sanitize_line(user_input)
                result = MatchResult(
                    user_input, sanitized, sanitized.split(), STATUS_RAW
                )
            else:
                result = matcher.match(user_input)

            final_cmd = " ".join(result.matched_tokens).strip()

            _log_line(session_log, f"[INPUT] {result.original_input}")
            if result.sanitized_input != result.original_input:
                _log_line(session_log, f"[SANITIZADO] '{result.sanitized_input}'")

            server_line = _format_server_line(result)
            _log_line(session_log, server_line)
            if VERBOSE_SERVER_LINES:
                print(server_line)

            if not final_cmd:
                _log_line(
                    session_log,
                    "[AVISO] comando vazio depois da limpeza: nada foi enviado ao jogo",
                )
                continue

            proc.stdin.write(final_cmd + "\n")
            proc.stdin.flush()

            if result.status == STATUS_SUGGEST and result.verb_matched:
                suggestion = f"< Perhaps, do you mean '{result.verb_matched}'?"
                print(suggestion)
                _log_line(session_log, f"[GAME] {suggestion}")

    finally:
        try:
            proc.terminate()
        except Exception:
            pass
        # espera a thread leitora terminar de escoar a saida do jogo antes de
        # fechar o log (senao as ultimas linhas [GAME] se perdem)
        try:
            reader.join(timeout=2)
        except Exception:
            pass
        session_log.close()
