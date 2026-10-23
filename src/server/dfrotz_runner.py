"""Sobe o dfrotz como subprocesso e conversa com o jogador.

* le a linha digitada, limpa (`src.utils.normalize`) e decide o que enviar ao
  jogo (`src.matching.matchers`);
* escreve a saida do jogo na tela conforme ela chega e so entao mostra o prompt
  da vez (`PROMPT_TEXT`), com a resposta inteira ja visivel;
* registra tudo em `data/logs/session_<timestamp>.txt`.

Do lado do jogador nada e anunciado: quando um sinonimo e trocado pela palavra do
dicionario, a tela nao mostra nada; o unico aviso que aparece e a sugestao
(`Perhaps, do you mean 'X'?`) da camada 3 do matcher.
"""

import codecs
import select
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

from src.config import (
    AUTOCOMPLETE_ENABLED,
    AUTOCOMPLETE_MAX_SUGGESTIONS,
    AUTOCOMPLETE_MIN_PREFIX,
    AUTOCOMPLETE_SIMILAR_SUGGESTIONS,
    GAME_IDLE_FALLBACK,
    GAME_QUIET_SECONDS,
    GAME_REPLY_TIMEOUT,
    PROMPT_TEXT,
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

# Ultimo caractere que o interpretador escreve quando esta esperando um comando
GAME_PROMPT_CHAR = ">"
READ_CHUNK = 65536


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class SessionLog:
    """Log da sessao, escrito por uma unica thread de cada vez.

    O arquivo recebe linhas de duas threads: a principal escreve
    ``[INPUT]``/``[SERVER]`` e a thread leitora escreve ``[GAME]``. Abrir e
    fechar o arquivo a cada linha (``open(path, "a")``) nao e seguro aqui: no WSL
    o projeto vive em ``/mnt/c`` (drvfs/OneDrive), onde o append concorrente pode
    sobrescrever ou perder linhas. Com um unico arquivo aberto e um lock, cada
    linha entra inteira e na ordem.
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


class GameOutput:
    """Saida do jogo na tela e o aviso de "pode digitar" para a thread principal.

    O interpretador escreve a resposta e o proprio ``>`` no fim, sem quebra de
    linha depois dele. Se esse ``>`` fosse escrito na tela, ficaria colado na
    ultima linha da resposta -- e o readline, que redesenha a linha que o jogador
    esta digitando, apagaria ele. Por isso o ``>`` final fica guardado em
    ``_held`` (fora da tela e do log) e quem mostra o prompt e o
    ``input(PROMPT_TEXT)``: o texto e escrito como prompt, ou seja, fora da area
    de digitacao, e continua na tela junto com a linha que o jogador digita.

    ``idle()`` marca o momento em que o jogo parou de escrever: com a resposta
    inteira na tela, a thread principal pode mostrar o prompt.
    """

    def __init__(
        self,
        log: SessionLog,
        interactive: bool = True,
        quiet_seconds: float = GAME_QUIET_SECONDS,
    ) -> None:
        self.quiet_seconds = quiet_seconds
        self._log = log
        self._interactive = interactive
        self._lock = threading.Lock()
        self._held = ""
        self._partial_line = ""
        self._ready = threading.Event()
        self._over = False

    @property
    def game_over(self) -> bool:
        """True quando o dfrotz terminou (nao ha mais para quem enviar comando)."""
        return self._over

    def feed(self, text: str) -> None:
        """Texto que chegou do jogo: vai para a tela e para o log."""
        with self._lock:
            self._ready.clear()
            text = self._held + text
            self._held = ""
            if self._interactive and text.endswith(GAME_PROMPT_CHAR):
                self._held = GAME_PROMPT_CHAR
                text = text[: -len(GAME_PROMPT_CHAR)]
            if text:
                self._write(text)

    def idle(self, quiet_for: float) -> None:
        """O jogo esta ``quiet_for`` segundos sem escrever nada."""
        with self._lock:
            if self._held or quiet_for >= GAME_IDLE_FALLBACK:
                self._ready.set()

    def wait(self, timeout: float) -> bool:
        """Espera a resposta do jogo chegar inteira; False se estourar o timeout."""
        return self._ready.wait(timeout)

    def begin_turn(self) -> None:
        """Um comando foi enviado: descarta o prompt antigo e espera a resposta."""
        with self._lock:
            self._held = ""
            self._ready.clear()

    def finish(self) -> None:
        """O dfrotz terminou: registra a ultima linha e acorda quem espera."""
        with self._lock:
            self._over = True
            self._flush_partial_line()
            self._ready.set()

    def _write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()
        self._partial_line += text
        while "\n" in self._partial_line:
            line, self._partial_line = self._partial_line.split("\n", 1)
            self._log.write(f"[GAME] {line.rstrip(chr(13))}")

    def _flush_partial_line(self) -> None:
        if self._partial_line:
            self._log.write(f"[GAME] {self._partial_line}")
            self._partial_line = ""


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


def _start_reader_thread(proc: subprocess.Popen, output: GameOutput) -> threading.Thread:
    """Thread que escreve a saida do jogo na tela assim que ela chega.

    O dfrotz escreve a resposta inteira de uma vez e da flush, mas a ultima linha
    (o prompt ``>``) nao termina com quebra de linha: ler com ``readline()`` (ou
    ``for line in proc.stdout``) prenderia essa linha no buffer de linha ate o
    jogador digitar o proximo comando. Aqui os bytes crus sao lidos em pedacos e
    repassados na hora.

    ``select`` e usado para perceber o silencio do jogo (o intervalo entre os
    pedacos que chegam): a cada rodada sem nada, ``output.idle()`` e chamado, e e
    isso que avisa a thread principal que a resposta acabou.
    """

    stream = getattr(proc.stdout, "buffer", proc.stdout)
    read_fd = stream.fileno()
    decoder = codecs.getincrementaldecoder("utf-8")("replace")

    def _reader() -> None:
        quiet_rounds = 0
        while True:
            try:
                data_ready, _, _ = select.select(
                    [read_fd], [], [], output.quiet_seconds
                )
            except (OSError, ValueError):
                break

            if not data_ready:
                quiet_rounds += 1
                output.idle(quiet_rounds * output.quiet_seconds)
                continue

            quiet_rounds = 0
            try:
                chunk = stream.read1(READ_CHUNK)
            except (OSError, ValueError):
                break
            if not chunk:
                break

            output.feed(decoder.decode(chunk))

        output.finish()

    thread = threading.Thread(target=_reader, daemon=True)
    thread.start()
    return thread


def _start_server_thread(game_words, strategy) -> threading.Thread:
    """Sobe o servidor TCP que o dfrotz (com o patch) exige no primeiro comando.

    Aqui o servidor apenas devolve o payload recebido: a decisao fica toda no
    matcher deste modulo (`src/matching/matchers.py`).
    """

    thread = threading.Thread(
        target=run_server,
        args=(game_words, strategy),
        kwargs={"disable_algorithm": True},
        daemon=True,
    )
    thread.start()
    return thread


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
    """Liga o TAB nas palavras do lexico + sinonimos (so a primeira palavra)."""
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

    session_log.write(f"[META] dfrotz={dfrotz_path}")
    session_log.write(f"[META] game={game_file}")
    session_log.write(f"[META] started={session_ts}")
    session_log.write(f"[META] modo={mode}")
    session_log.write(
        f"[META] lexico={len(lexicon)} palavras, {len(lexicon.synonyms)} sinonimos"
    )
    for problem in lexicon.problems:
        session_log.write(f"[META] lexico-aviso={problem}")

    matcher = None
    if mode != "0":
        matcher = build_matcher(lexicon, game_words, strategy)

    _start_server_thread(game_words, strategy)

    proc = subprocess.Popen(
        [str(dfrotz_path), "-q", str(game_file)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    interactive = sys.stdin.isatty()
    output = GameOutput(session_log, interactive=interactive)
    reader = _start_reader_thread(proc, output)
    prompt = PROMPT_TEXT if interactive else ""

    autocomplete_on = _enable_verb_autocomplete(autocomplete_entries, strategy)
    session_log.write(
        "[META] autocomplete="
        + ("on" if autocomplete_on else "off")
        + (
            f" entradas={len(tuple(autocomplete_entries or ()))}"
            if autocomplete_on
            else ""
        )
    )

    try:
        while True:
            answered = output.wait(GAME_REPLY_TIMEOUT)
            if output.game_over:
                session_log.write("[AVISO] o dfrotz terminou: sessao encerrada")
                break
            if not answered:
                session_log.write(
                    "[AVISO] o jogo nao respondeu em "
                    f"{GAME_REPLY_TIMEOUT}s: o prompt foi mostrado mesmo assim"
                )

            try:
                user_input = input(prompt)
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

            session_log.write(f"[INPUT] {result.original_input}")
            if result.sanitized_input != result.original_input:
                session_log.write(f"[SANITIZADO] '{result.sanitized_input}'")

            server_line = _format_server_line(result)
            session_log.write(server_line)
            if VERBOSE_SERVER_LINES:
                print(server_line)

            if not final_cmd:
                session_log.write(
                    "[AVISO] comando vazio depois da limpeza: nada foi enviado ao jogo"
                )
                continue

            output.begin_turn()
            proc.stdin.write(final_cmd + "\n")
            proc.stdin.flush()

            if result.status == STATUS_SUGGEST and result.verb_matched:
                suggestion = f"< Perhaps, do you mean '{result.verb_matched}'?"
                print(suggestion)
                session_log.write(f"[GAME] {suggestion}")

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
