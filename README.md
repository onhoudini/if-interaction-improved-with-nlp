# IF Interaction Improved with NLP

Este repositório contém uma ferramenta de pesquisa de TCC para melhorar a interação com jogos de Ficção Interativa (FI) clássicos baseados em Z-machine, corrigindo automaticamente comandos de verbo digitados pelo jogador que o interpretador não reconheceria, usando similaridade semântica via WordNet combinada com similaridade de string.

O caso de teste atual da ferramenta é o **Zork I** (`zork1-r88-s840726.z3`), rodando através do interpretador **Frotz** (modo `dfrotz`, sem interface gráfica).

> O estado atual do README descreve a versão que será utilizada nos testes com usuários. Aperfeiçoamentos na organização e modularização estão planejadas como uma etapa futura, para permitir que a ferramenta possa ser modificada para outras estrátegias de similaridade/correção. Nenhuma das mudanças em organização e modularização afetará os resultados para os usuários.

---

## Resumo do Funcionamento

1. O programa extrai o dicionário de palavras do próprio arquivo do jogo (`.z3`) e carrega uma lista de verbos válidos, previamente colocada em `data/dictionaries/actions.txt`.
2. Ele sobe o `dfrotz` como um subprocesso e intercepta cada comando digitado antes de repassá-lo ao jogo.
3. Cada comando passa pelo `VerbMatcher` (`src/matching/matchers.py`), que usa a estratégia de similaridade configurada (`src/similarity/first_strategy.py`, baseada em WordNet) para comparar o verbo digitado com os verbos válidos do jogo.
4. Dependendo do quão parecido for o verbo, o comando é: (a) deixado como está, (b) corrigido automaticamente, ou (c) uma sugestão é exibida — de acordo com os limiares definidos em `src/config.py`.
5. Toda a sessão é registrada em `data/logs/`.

### Adaptações

Embora não testado amplamente, outros jogos zmachine podem ser adaptados utilizando o script `src/zmachine/zmachine_dictionary.py` e adaptando o `src/tools/check-for-actions.py`. A adaptação necessitará de mudanças dentro do código e de uma avaliação de respostas padrão de outros jogos.

---

## Pré-requisitos

- **Python 3.10+** (testado em 3.12)
- **Linux** — hoje é o único sistema operacional suportado. O interpretador `dfrotz` já vem compilado em `frotz-master/dfrotz`; não há build nativo para Windows/macOS neste momento (ver seção [Limitações](#limitações-conhecidas)).
- Acesso à internet na primeira execução, para o download automático dos dados do WordNet (NLTK) e de outras dependências.

---

## Como reproduzir (Linux)

### 1. Clonar o repositório e entrar na pasta

```bash
git clone https://github.com/onhoudini/if-interaction-improved-with-nlp
cd if-interaction-with-pln
```

### 2. Criar e ativar um ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Os scripts `run.sh`/`run.bat` procuram automaticamente por uma pasta `.venv` (ou `venv`) na raiz do projeto — use um desses dois nomes para que a execução automática funcione.

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Confirmar que o `dfrotz` tem permissão de execução

O binário já vem compilado no repositório, mas dependendo de como os arquivos foram transferidos (zip, etc.), a permissão de execução pode se perder:

```bash
chmod +x frotz-master/dfrotz
```

Se preferir recompilar do zero, é necessário `gcc`/`make` instalados:

```bash
cd frotz-master
make dumb
cd ..
```

### 5. Rodar

Usando o script pronto:

```bash
chmod +x run.sh # Somente na primeira vez
./run.sh
```

Ou diretamente:

```bash
python src/main.py 1   # modo com o algoritmo de correção (padrão)
python src/main.py 0   # modo "frotz puro" - (Ainda não funcional)
```

Na primeira execução, o NLTK vai baixar automaticamente os pacotes `wordnet` e `omw-1.4` (mostra uma barra de progresso silenciosa; não requer nenhuma ação manual).

## Dados

Ao encerrar a sessão, os arquivos de log ficam em `data/logs/` (histórico da sessão com timestamp) e a lista de ações efetivamente disponíveis naquela execução é salva em `data/logs/actions_used.txt`.

---

## Estrutura do projeto

```
if-interaction-with-pln/
├── frotz-master/              # Interpretador Frotz (código de terceiros, licença GPL) + binário dfrotz já compilado
│   └── games/                 # Arquivos .z3 dos jogos (Zork I e II incluídos)
├── data/
│   ├── dictionaries/          # actions.txt — lista de verbos curada, usada em tempo real
│   └── logs/                  # Logs de sessão gerados a cada execução
├── src/
│   ├── main.py                 # Ponto de entrada (python src/main.py [0|1])
│   ├── config.py               # Host/porta do servidor, limiares de decisão, estratégia ativa, caminho do jogo
│   ├── zmachine/
│   │   └── zmachine_dictionary.py   # Decodifica o dicionário embutido no arquivo .z3
│   ├── similarity/
│   │   └── first_strategy.py        # Estratégia de similaridade (WordNet + string matching)
│   ├── matching/
│   │   └── matchers.py              # Orquestra a comparação verbo digitado × verbos válidos
│   ├── server/
│   │   ├── dfrotz_runner.py         # Sobe o dfrotz como subprocesso e aplica a correção em tempo real
│   │   └── frotz_server.py          # Servidor TCP (porta configurável em config.py) — ver observação abaixo
│   ├── tools/
│   │   ├── check-for-actions.py     # Script offline: testa cada palavra do dicionário contra o dfrotz para gerar actions.txt
│   │   └── verb-recognition.py      # Script offline alternativo: classifica verbos usando WordNet (sem depender do dfrotz)
│   └── utils/
│       ├── tokenizer.py             # Tokenização simples de texto
│       └── load_verbs.py            # Carrega arquivos de lista de palavras (um por linha)
├── run.sh / run.bat            # Scripts de execução (procuram .venv/venv automaticamente)
└── requirements.txt
```


---

## Configuração

Edite `src/config.py` para ajustar:

| Variável | Descrição |
|---|---|
| `SIMILARITY_STRATEGY` | Classe de estratégia de similaridade ativa (hoje, `WordNetVerbSimilarityStrategy`) |
| `SERVER_HOST`, `SERVER_PORT` | Endereço do servidor TCP interno (ver observação acima) |
| `THRESHOLD_SUGGESTION` | Nota mínima de similaridade (0–1) para o sistema *sugerir* uma correção |
| `THRESHOLD_AUTO_CORRECT` | Nota mínima de similaridade (0–1) para o sistema corrigir automaticamente, sem perguntar |
| `GAME_FILE` | Caminho do arquivo `.z3` usado (padrão: `frotz-master/games/zork1-r88-s840726.z3`) |



---

## Limitações conhecidas

- **Só Linux, por enquanto.** O patch que permite a comunicação entre o `dfrotz` e o restante do sistema usa sockets POSIX (`sys/socket.h`, `arpa/inet.h`), que não existem nativamente no Windows. Suporte nativo ao Windows **ainda** não foi implementado, mas é possível utilizar a ferramenta via WSL.
- **Testado apenas com a família Zork** Outros jogos podem precisar de ajustes para extração de dicionário e categorização de verbos.

---

## Possibilidades Futuras

- **Parametrização**: Melhoria de parametrização para permitir que outras configurações e algoritmos sejam utilizados. 
- **Dados**: Utilização dos dados gerados pelos jogadores que utilizam a ferramenta para mapear entradas e saídas dos jogos, o que possivelmente permitiria uma melhora expressiva da ferramenta.

---

## Créditos

- Interpretador base: [Frotz](https://gitlab.com/DavidGriffith/frotz) (GPL).
- Arquivo do jogo: [the-infocom-files/zork1](https://github.com/the-infocom-files/zork1).
