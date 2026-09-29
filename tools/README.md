# tools/ — scripts offline

Nada aqui roda durante o jogo: são as ferramentas para **olhar o arquivo do
jogo** e **montar/conferir** o léxico de sinônimos (`data/lexicon/action.csv`).

| Arquivo | Para que serve | Saída |
|---|---|---|
| `zmachine_dictionary.py` | Decodifica o dicionário embutido no `.z3` (as palavras que o jogo conhece). Também é usado pelo runtime (`src/main.py`) e, rodando direto, salva a lista em arquivo. | `tools/output/<jogo>_dictionary.txt` |
| `check_for_actions.py` | Testa palavra por palavra no `dfrotz` e separa as que o jogo aceita como **ação** (pergunta ao próprio jogo). | `tools/output/actions.txt`, `output/not_actions.txt`, `output/check_for_actions_log.txt` |
| `verb_recognition.py` | Classifica as palavras como verbo com WordNet + âncoras de ação, **sem** rodar o jogo. | `tools/output/verbs.txt`, `output/others.txt`, `output/unknown.txt` |
| `validate_lexicon.py` | Confere o `data/lexicon/action.csv` contra o dicionário real do jogo (palavra inexistente, sinônimo ambíguo, linha inútil). | relatório no terminal + `tools/output/lexicon_report.txt` |

## Como rodar

Sempre da raiz do projeto, dentro do WSL/Linux:

```bash
python tools/zmachine_dictionary.py
python tools/check_for_actions.py
python tools/verb_recognition.py
python tools/validate_lexicon.py
```

### De onde vêm as palavras

Os três primeiros aceitam uma lista pronta **ou** extraem as palavras do `.z3`
sozinhos (função `resolve_words()` em `zmachine_dictionary.py`):

```bash
python tools/check_for_actions.py                     # extrai de frotz-master/games/*.z3
python tools/check_for_actions.py /tmp/palavras.txt   # usa o arquivo (uma palavra por linha)
```

### Por que os scripts são separados (e não um só)

Cada um responde uma pergunta diferente:

| Pergunta | Quem responde | Custo |
|---|---|---|
| *quais palavras o jogo conhece?* | `zmachine_dictionary.py` | rápido, sem abrir o jogo |
| *quais dessas o jogo aceita como ação?* | `check_for_actions.py` | lento: roda o `dfrotz` 1× por palavra |
| *quais dessas são verbos (linguística)?* | `verb_recognition.py` | médio: WordNet, sem `dfrotz` |
| *meu `action.csv` está consistente?* | `validate_lexicon.py` | rápido |

Juntar tudo num arquivo só misturaria a decodificação (pura, sem efeitos) com a
execução do jogo (subprocessos + servidor TCP) e com a checagem de dados
curados. O que **é** compartilhado ficou compartilhado: a decodificação e a
leitura da lista de palavras estão em `zmachine_dictionary.py`, usado pelos
outros três e pelo runtime.

## Observações

* `check_for_actions.py` roda o `dfrotz` **uma vez por palavra** (688 no Zork I),
  então demora vários minutos;
* ele também sobe o servidor TCP da porta `2300` (`SERVER_PORT`), portanto não
  pode rodar ao mesmo tempo que uma sessão de jogo aberta — ou rode dentro de um
  namespace de rede isolado (`unshare -rn`);
* a pasta `tools/output/` é gerada automaticamente e está no `.gitignore`.

## Método usado para montar `actions.txt` (histórico)

O `actions.txt` que existia em `data/dictionaries/` foi produzido assim, e é este
o método que `check_for_actions.py` automatiza:

1. extrair as palavras do `.z3` (`zmachine_dictionary.py`);
2. enviar cada palavra ao `dfrotz` como um comando;
3. considerar **ação** a palavra cuja resposta não trouxe
   `There was no verb in that sentence!` nem `I don't know the word ...`;
4. separar a lista final em ações / não-ações.

Com o léxico curado, essa lista não é mais usada em tempo de execução: o runtime
só precisa do `action.csv` e do dicionário extraído do `.z3` na hora de rodar.

