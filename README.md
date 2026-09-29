# IF Interaction Improved with NLP

Este repositório contém uma ferramenta de pesquisa de TCC para melhorar a interação com jogos de Ficção Interativa (FI) clássicos baseados em Z-machine. Ela troca, **em silêncio**, os sinônimos que o jogador digita pela **palavra que o jogo entende**, usando um léxico curado em `data/lexicon/action.csv`; quando a palavra digitada não está nem no dicionário do jogo nem no léxico, a ferramenta pode **sugerir** uma parecida por similaridade semântica (WordNet).

O caso de teste atual da ferramenta é o **Zork I** (`zork1-r88-s840726.z3`), rodando através do interpretador **Frotz** (modo `dfrotz`, sem interface gráfica).

> O estado atual do README descreve a versão que será utilizada nos testes com usuários. Aperfeiçoamentos na organização e modularização estão planejadas como uma etapa futura, para permitir que a ferramenta possa ser modificada para outras estrátegias de similaridade/correção. Nenhuma das mudanças em organização e modularização afetará os resultados para os usuários.

---

## Resumo do Funcionamento

1. O programa extrai o dicionário de palavras do próprio arquivo do jogo (`.z3`) — é a lista do que o jogo conhece.
2. Carrega a tabela de sinônimos de `data/lexicon/action.csv` (formato `palavra,sinonimo1,sinonimo2`) e sobe o `dfrotz` como subprocesso, interceptando cada comando antes de repassá-lo ao jogo.
3. A linha digitada passa por uma limpeza (`src/utils/normalize.py`): tira acento, pontuação e caractere de controle, colapsa espaços e corta no limite de 255 bytes da mensagem trocada com o `dfrotz`.
4. O `VerbMatcher` (`src/matching/matchers.py`) decide em **quatro camadas**: (1) o jogo conhece a palavra → passa intacta; (2) a palavra está no léxico → é trocada pela forma do dicionário, **em silêncio**; (3) nada acima → a estratégia de similaridade (`src/similarity/wordnet_strategy.py`, WordNet + string) pode **sugerir** uma parecida quando a nota for ≥ `SUGGESTION_THRESHOLD` (`0.80`), sem trocar o comando; (4) caso contrário → passa intacta. Detalhes na seção [O léxico de sinônimos](#o-léxico-de-sinônimos-actioncsv).
5. Toda a sessão é registrada em `data/logs/session_<timestamp>.txt` (esses arquivos **não** são versionados no git).

### Adaptações

Como o dicionário sai do próprio arquivo do jogo, adaptar para outro jogo Z-machine é apontar `GAME_FILE` em `src/paths.py` para o outro `.z3` e montar um `action.csv` para ele. Os scripts de `tools/` (extração do dicionário, `check_for_actions.py`, `verb_recognition.py` e `validate_lexicon.py`) existem justamente para isso.

---

## Pré-requisitos

| Requisito | Detalhe |
|---|---|
| **Linux ou Windows com WSL** | Único sistema suportado. O interpretador do jogo (`frotz-master/dfrotz`) é um binário de Linux, então **não existe execução nativa no Windows/macOS** (ver [Limitações](#limitações-conhecidas)). No Windows, tudo roda dentro do WSL. |
| **Python 3.10+** | Testado em 3.12 e 3.14. O ambiente virtual tem de ser criado **dentro do Linux/WSL**: um `.venv` do Windows não executa o `dfrotz`. |
| **Permissão de execução no `dfrotz`** | O binário já vem compilado em `frotz-master/dfrotz`, mas o bit de execução se perde quando o projeto é baixado como `.zip`. O `chmod` da seção [Como rodar](#como-rodar) é **obrigatório**. |
| **Internet na primeira execução** | Para o download automático dos dados do WordNet (NLTK) e para as dependências do `pip`. |

---

## Como rodar

- **[A) Windows (com WSL)](#a-windows-com-wsl)** — recomendado se você está no Windows.
- **[B) Linux](#b-linux)** — se você já está num Linux (nativo, VM ou o próprio WSL aberto).

Os passos de cada caminho são **obrigatórios** e devem ser executados na ordem. Rode sempre pelo `./run.sh` (ou pelo `run.bat`, no Windows): é ele que garante que as dependências e a permissão de execução do `dfrotz` estão corretas a cada execução.

> Em projetos baixados como `.zip`, o bit de execução do `run.sh` também se perde. Se aparecer `Permission denied` ao rodar `./run.sh`, use `bash run.sh` (não depende da permissão) ou rode uma única vez:

```bash
chmod u+rwx run.sh
chmod u+rwx frotz-master/dfrotz
```

### A) Windows (com WSL)

**1. Instalar o WSL (uma única vez no computador)**

No PowerShell **como administrador**:

```powershell
wsl --install -d Ubuntu
```

Reinicie o computador se for pedido, abra o aplicativo **Ubuntu** e crie o usuário/senha do Linux.

**2. Chegar até a pasta do projeto, dentro do WSL**

Abra o **Ubuntu** e entre na pasta do projeto. Se ele está em `C:\Users\<seu-usuario>\Documents\if-interaction-with-pln`, o caminho dentro do WSL é o mesmo com o prefixo `/mnt/c` e barras normais:

```bash
cd /mnt/c/Users/<seu-usuario>/Documents/if-interaction-with-pln
```

> Atalho: no PowerShell/CMD, dentro da pasta do projeto, você pode rodar `wsl bash run.sh` — o WSL abre já nessa pasta (é o que o `run.bat` faz).

**3. Criar o ambiente virtual (Python do Linux)**

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

> Se aparecer erro de `python3-venv`/`ensurepip`, instale antes: `sudo apt update && sudo apt install -y python3 python3-venv python3-pip`.

> **Importante:** o `.venv` precisa ser criado **dentro do WSL**. Um `.venv\Scripts\python.exe` criado no Windows não serve, porque quem inicia o jogo é um binário de Linux.

**4. Dar permissão de execução ao `dfrotz` (obrigatório)**

```bash
chmod u+rwx frotz-master/dfrotz
```

O `git clone` preserva essa permissão, mas o download do GitHub pelo botão **"Download ZIP"** não — e o programa então para com:

```
PermissionError: [Errno 13] Permission denied: 'if-interaction-improved-with-nlp-main/frotz-master/dfrotz'
```

Se essa mensagem aparecer, rode o `chmod` acima e execute de novo. O `run.sh` também faz esse `chmod` automaticamente quando percebe que a permissão está faltando.

**5. Rodar**

```bash
./run.sh
```

> No Windows também funciona dar duplo-clique em `run.bat`: ele detecta o WSL, entra na pasta do projeto e executa `./run.sh` lá dentro (com as mesmas mensagens de erro, se algo estiver faltando).

**Resumo do caminho Windows:**

```bash
wsl --install -d Ubuntu            # PowerShell como administrador (uma vez)
# abra o Ubuntu e depois:
cd /mnt/c/<caminho>/if-interaction-with-pln
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
chmod u+rwx frotz-master/dfrotz
./run.sh
```


### B) Linux

**1. Clonar o repositório e entrar na pasta**

```bash
git clone https://github.com/onhoudini/if-interaction-improved-with-nlp
cd if-interaction-with-pln
```

**2. Criar o ambiente virtual**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

> Os scripts `run.sh`/`run.bat` procuram automaticamente por uma pasta `.venv` (ou `venv`) na raiz do projeto — use um desses dois nomes para que a execução automática funcione.

**3. Instalar as dependências**

```bash
pip install -r requirements.txt
```

**4. Dar permissão de execução ao `dfrotz` (obrigatório)**

```bash
chmod u+rwx frotz-master/dfrotz
```

O binário já vem compilado no repositório, mas o bit de execução **se perde quando o projeto é baixado como `.zip`**. Sem esse comando, o programa para com:

```
PermissionError: [Errno 13] Permission denied: '.../frotz-master/dfrotz'
```

Se isso acontecer, rode o `chmod` acima e execute novamente. O `run.sh` também faz esse `chmod` automaticamente quando percebe que a permissão está faltando.

Se, em vez de reusar o binário, você quiser recompilar do zero (não é necessário), é preciso ter `gcc`/`make` instalados:

```bash
cd frotz-master
make dumb
cd ..
```

**5. Rodar**

Usando o script pronto (recomendado, porque ele confere ambiente virtual e permissões antes de iniciar):

```bash
./run.sh          # modo com o léxico de sinônimos + sugestões (padrão)
./run.sh 0        # modo "frotz puro": nada é processado (grupo de controle)
```

Ou diretamente pelo Python:

```bash
python src/main.py 1   # modo com o léxico de sinônimos (padrão)
python src/main.py 0   # modo "frotz puro": a linha do jogador só passa pela limpeza e vai direto ao jogo
```

> **Modo `0` (grupo de controle).** No modo `0` o léxico não é carregado, a estratégia de similaridade não é instanciada e nenhuma linha `[SERVER]` é produzida: cada comando só passa pela limpeza de entrada e vai direto para o jogo (comportamento de `frotz` puro). É a referência para o teste A/B.

> Ao rodar `python src/main.py` diretamente você não passa pelo `run.sh`: nesse caso a criação do `.venv`, a instalação de `requirements.txt` e o `chmod u+rwx frotz-master/dfrotz` precisam ter sido feitos por você antes (passos 2, 3 e 4).

Na primeira execução, o NLTK vai baixar automaticamente os pacotes `wordnet` e `omw-1.4` (mostra uma barra de progresso silenciosa; não requer nenhuma ação manual).

## Jogando

O jogo (Zork I) roda normalmente no terminal. Digitar o comando é tudo o que o jogador precisa fazer: quando o verbo digitado é um sinônimo cadastrado no léxico, o programa envia a palavra do dicionário no lugar dele **sem avisar ninguém** (nenhuma mensagem, nenhum atraso). A única mensagem que pode aparecer é a sugestão da camada 3 — `Perhaps, do you mean 'X'?` — e ela **não** altera o comando enviado.

### O prompt `>`

O `>` no começo da linha é o prompt que a ferramenta mostra quando o jogo terminou de responder e está esperando um comando. Digite o comando logo depois dele e pressione **Enter**:

```
>open mailbox
Opening the small mailbox reveals a leaflet.

>
```

> Quem escreve esse `> ` é o `input()` do `src/server/dfrotz_runner.py` (o texto está em `PROMPT_TEXT`, em `src/config.py`), e ele é escrito **como prompt**: não faz parte da linha digitada, então não entra no comando enviado ao jogo nem no autocomplete do TAB.
>
> O próprio `dfrotz` também escreve um `>` no fim da resposta, mas **sem quebra de linha** depois dele. Esse `>` nunca aparece na tela: a saída do jogo é lida em blocos crus e o `>` final fica guardado no `GameOutput` (ele não vai para a tela nem para o log), para o prompt do jogador não aparecer duplicado nem colado no fim da resposta. O prompt só é mostrado depois que a resposta inteira chegou (a thread que lê a saída avisa quando o jogo para de escrever).

Pressione **TAB** enquanto digita para completar automaticamente o **verbo** (primeira palavra do comando): um TAB já lista todas as opções que começam com o que você digitou. Depois do primeiro espaço o TAB não faz nada. Detalhes na seção [Autocomplete de verbos](#autocomplete-de-verbos-tab).

Ao encerrar a sessão, o histórico fica em `data/logs/session_<timestamp>.txt` (uma linha `[INPUT]` e uma `[SERVER]` por comando, mais a saída do jogo em `[GAME]`) e as palavras do léxico usadas naquela execução são salvas em `data/logs/actions_used.txt` (com cópia para `actions_used_<timestamp>.txt`). O `data/logs/` está no `.gitignore`.

---

## Estrutura do projeto

```
if-interaction-with-pln/
├── frotz-master/              # Interpretador Frotz (terceiros, GPL) + binário dfrotz compilado
│   └── games/                 # Arquivos .z3 dos jogos (Zork I, II e III)
├── data/
│   ├── lexicon/
│   │   └── action.csv          # LÉXICO curado: palavra,sinonimo1,sinonimo2
│   └── logs/                   # Sessões de jogo e relatórios (não versionado)
├── src/
│   ├── main.py                 # Ponto de entrada (python src/main.py [0|1])
│   ├── config.py               # Limiar de sugestão, autocomplete, host/porta do servidor
│   ├── paths.py                # Caminhos do projeto em um lugar só (dfrotz, jogo, dados, logs)
│   ├── lexicon/
│   │   └── action_lexicon.py   # Lê o action.csv: sinonimo -> palavra e palavra -> sinonimos
│   ├── matching/
│   │   └── matchers.py         # As quatro camadas de decisão (ver Resumo do Funcionamento)
│   ├── similarity/
│   │   ├── base.py             # Interface da estratégia de similaridade
│   │   └── wordnet_strategy.py # WordNet + string: usada só para SUGERIR
│   ├── server/
│   │   ├── dfrotz_runner.py    # Sobe o dfrotz, limpa a entrada, troca sinônimos, escreve a saída na tela e registra o log
│   │   └── frotz_server.py     # Servidor TCP que o dfrotz (com patch) exige (porta 2300)
│   └── utils/
│   │   ├── normalize.py        # Limpeza da entrada (a única normalização do projeto)
│   │   ├── tokenizer.py        # Tokenização (usa o normalize)
│   │   └── verb_completer.py   # Autocomplete no TAB (readline)
├── tools/                      # Scripts OFFLINE (não rodam durante o jogo)
│   ├── zmachine_dictionary.py  # Decodifica o dicionário embutido no .z3 (também usado pelo runtime)
│   ├── check_for_actions.py    # Testa cada palavra no dfrotz e separa o que é ação
│   ├── verb_recognition.py     # Classifica palavras como verbo via WordNet (sem dfrotz)
│   └── validate_lexicon.py     # Confere o action.csv contra o dicionário real do jogo
├── run.sh / run.bat            # Execução: run.sh roda no Linux/WSL (confere .venv e o chmod do dfrotz); run.bat abre o run.sh dentro do WSL
└── requirements.txt
```

---

## Configuração

Edite `src/config.py` para ajustar:

| Variável | Descrição |
|---|---|
| `SIMILARITY_STRATEGY` | Classe de estratégia de similaridade — usada **apenas para sugerir** (hoje, `WordNetVerbSimilarityStrategy`) |
| `SERVER_HOST`, `SERVER_PORT` | Endereço do servidor TCP que o `dfrotz` (com patch) exige (padrão `localhost:2300`) |
| `SUGGESTION_THRESHOLD` | **Único limiar do projeto** (0–1): nota mínima para a camada 3 sugerir uma palavra parecida. Padrão `0.80` |
| `VERBOSE_SERVER_LINES` | `True` também imprime as linhas `[SERVER]` na tela do jogador (útil para depurar). Padrão `False` |
| `PROMPT_TEXT` | Texto do prompt mostrado antes de cada comando (escrito fora da área digitada). Padrão `"> "` |
| `GAME_QUIET_SECONDS`, `GAME_IDLE_FALLBACK`, `GAME_REPLY_TIMEOUT` | Tempos (segundos) usados para decidir quando a resposta do jogo terminou e o prompt pode aparecer |
| `AUTOCOMPLETE_ENABLED` | Liga/desliga o autocomplete via TAB (ver seção [Autocomplete de verbos](#autocomplete-de-verbos-tab)) |
| `AUTOCOMPLETE_MIN_PREFIX` | Mínimo de letras digitadas para o TAB responder |
| `AUTOCOMPLETE_SIMILAR_SUGGESTIONS` | Sugere palavras parecidas (via estratégia de similaridade) quando nenhuma começa com o prefixo digitado |
| `AUTOCOMPLETE_MAX_SUGGESTIONS` | Número máximo de sugestões parecidas exibidas |

> Os **caminhos** do projeto (jogo, `dfrotz`, pasta de dados, léxico e logs) ficam em `src/paths.py` — não em `config.py`.

---

## O léxico de sinônimos (`action.csv`)

Arquivo: **`data/lexicon/action.csv`** (o caminho está em `src/paths.py`).

```
palavra,sinonimo1,sinonimo2
catch,seize,nab
read,peruse,study
```

* **`palavra`** é a forma que o **jogo** entende. O dicionário do Zork I trunca as palavras em 6 caracteres (`inventory` vira `invent`, `mailbox` vira `mailbo`), então essa coluna precisa ser a forma do dicionário — é ela que vai ser enviada ao jogo.
* **`sinonimoN`** são as formas que o jogador pode digitar. Quando ele digita uma delas, o programa envia a `palavra` da mesma linha, **sem avisar** e sem trocar o que aparece na tela.

O cabeçalho é opcional (a primeira célula pode ser `palavra`), linhas em branco e células vazias são ignoradas e palavras sem sinônimo são permitidas (elas apenas não geram troca).

### Regras (conferidas por `tools/validate_lexicon.py`)

| Situação | O que acontece |
|---|---|
| `palavra` que não existe no dicionário do jogo | **ERRO** — a troca enviaria ao jogo algo que ele não conhece |
| mesmo sinônimo em duas linhas (ex.: `grab` em `take` e em `hold`) | **ERRO** de ambiguidade: o runtime fica com o **primeiro** dono e avisa no começo da sessão |
| sinônimo com espaço (`cast off`) | **ERRO** — a troca é palavra por palavra; o sinônimo é ignorado e o aviso vai para o log |
| sinônimo que o jogo já conhece (ex.: `wrench`) | **AVISO** — a linha não faz efeito, porque "o jogo conhece a palavra" vem antes no pipeline |
| palavra repetida em duas linhas | **AVISO** — os sinônimos das duas linhas são somados |

Rode antes de jogar (ou depois de editar o CSV):

```bash
python tools/validate_lexicon.py
```

O resultado (`OK`/`REPROVADO`, com a lista de erros e avisos) também é gravado em `tools/output/lexicon_report.txt`.

> A troca acontece só na **primeira** palavra que o pipeline considera verbo (palavra que o jogo conhece, sinônimo do léxico ou candidata detectada pelo WordNet); os outros tokens vão como o jogador digitou. Por isso a coluna `palavra` precisa estar na forma do dicionário.

---

## Autocomplete de verbos (TAB)

Durante o jogo (modo `1`), pressionar **TAB** completa a **primeira palavra** do comando com os candidatos do léxico: as `palavra` e os `sinonimoN` de `data/lexicon/action.csv`. O recurso é intencionalmente restrito:

- **Só o verbo.** O TAB só age enquanto o jogador ainda está digitando a primeira palavra; depois do primeiro espaço ele não faz nada, ou seja, objetos/substantivos nunca são completados.
- **Só o que está no léxico.** Os candidatos são exatamente as palavras e os sinônimos do `action.csv`; o que não estiver lá não aparece na lista.
- **Nada é enviado ao jogo.** Comportamento padrão do `readline`: o TAB lista os candidatos e, quando só existe um, completa a palavra; o comando só vai para o `dfrotz` quando o jogador aperta Enter. Por padrão o `readline` só listaria na **segunda** vez que o TAB fosse apertado — a lista sai no primeiro TAB porque o `verb_completer.py` liga a opção `show-all-if-ambiguous`.

Exemplos: `ta` + TAB → lista `tail`, `take`, `talk`, `tally`, `tan`, `tap`, `taste`, `taunt`; `tak` + TAB → completa `take`.

Implementação: `src/utils/verb_completer.py` (classe `VerbCompleter`) é ligada ao loop de entrada em `src/server/dfrotz_runner.py` (funções `_enable_verb_autocomplete` e `_build_verb_recommender`). No modo `0` (frotz puro / grupo de controle) o autocomplete fica **desligado**, para não interferir na comparação A/B.

Ajustes em `src/config.py`:

| Variável | Descrição | Padrão |
|---|---|---|
| `AUTOCOMPLETE_ENABLED` | Liga/desliga o TAB (apenas no modo `1`) | `True` |
| `AUTOCOMPLETE_MIN_PREFIX` | Mínimo de letras digitadas para o TAB responder | `1` |
| `AUTOCOMPLETE_SIMILAR_SUGGESTIONS` | Se nada começar com o prefixo digitado, sugere uma palavra parecida usando a mesma estratégia de similaridade (respeita `SUGGESTION_THRESHOLD`; mais lento) | `False` |
| `AUTOCOMPLETE_MAX_SUGGESTIONS` | Número máximo de sugestões parecidas exibidas | `5` |

> O autocomplete usa o módulo `readline` (nativo no Linux/macOS). Se `readline` não estiver disponível — ou se a entrada não for um terminal (pipes, execuções automatizadas) — o recurso é apenas desativado, sem afetar o restante do programa. No Windows nativo seria necessário `pip install pyreadline3`.

---

## Solução de problemas

Mensagens conhecidas e o que fazer em cada caso.

### `Nao encontrei um ambiente virtual do Windows.`

Mensagem do `run.bat` (Windows). Ela indica que existe um ambiente virtual **do Windows** (`.venv\Scripts\python.exe`) e nenhum ambiente virtual de Linux.

**Causa:** o projeto não roda no Windows nativo — o interpretador do jogo (`frotz-master/dfrotz`) é um binário de Linux.

**Solução:** rodar dentro do WSL, criando o ambiente virtual lá (passos da seção [A) Windows (com WSL)](#a-windows-com-wsl)):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./run.sh
```

### `bash: ./run.sh: Permission denied`

O bit de execução do `run.sh` se perde quando o projeto é baixado como `.zip`. Rode com `bash` (não depende da permissão) ou dê a permissão uma vez:

```bash
bash run.sh
# ou
chmod u+rwx run.sh
```

### `PermissionError: [Errno 13] Permission denied: '.../frotz-master/dfrotz'`

O binário do `dfrotz` está sem permissão de execução — o que acontece quando o projeto é obtido como `.zip` (o "Download ZIP" do GitHub não preserva o bit de execução).

**Solução:**

```bash
chmod u+rwx frotz-master/dfrotz
```

Depois disso, rode novamente. O `run.sh`/`run.bat` já fazem esse `chmod` automaticamente quando percebem que a permissão está faltando.

### `[Errno 98] Address already in use` / `ERROR: Unable to connect to server`

O programa conversa com o `dfrotz` pela porta TCP `2300` (`SERVER_PORT`, em `src/config.py`). Se já existe outra sessão do jogo aberta — ou um processo antigo ficou preso — a porta está ocupada.

**Solução:** feche a outra sessão (outra janela do Ubuntu/WSL) ou encerre os processos antigos e rode de novo:

```bash
pkill -f "src/main.py"   # encerra sessoes da ferramenta
pkill -f dfrotz          # encerra interpretadores que ficaram presos
```

Sem o servidor no ar, o `dfrotz` encerra o jogo no primeiro comando enviado, com `ERROR: Unable to connect to server`.

### O jogo parece estar esperando um comando, mas não aparece nenhum sinal na tela

O sinal de que é a sua vez é o `> ` (ver [O prompt](#o-prompt)). Ele é escrito pela própria ferramenta, sempre depois que a resposta do jogo terminou de aparecer — não depende do que o `dfrotz` manda.

---

## Limitações conhecidas

- **Não há suporte nativo ao Windows (nem a macOS).** O patch que permite a comunicação entre o `dfrotz` e o restante do sistema usa sockets POSIX (`sys/socket.h`, `arpa/inet.h`), que não existem nativamente no Windows, e não há binário do `dfrotz` compilado para Windows/macOS. No Windows a ferramenta roda via **WSL** (é o que o `run.bat` faz).
- **Modo `0` (grupo de controle).** O modo `0` não carrega o léxico, não instancia a estratégia de similaridade e não imprime linhas `[SERVER]`: o comando só passa pela limpeza de entrada e vai direto ao jogo (é a referência para o teste A/B).
- **Testado apenas com a família Zork** Outros jogos podem precisar de ajustes para extração de dicionário e categorização de verbos.

---

## Possibilidades Futuras

- **Parametrização**: Melhoria de parametrização para permitir que outras configurações e algoritmos sejam utilizados. 
- **Dados**: Utilização dos dados gerados pelos jogadores que utilizam a ferramenta para mapear entradas e saídas dos jogos, o que possivelmente permitiria uma melhora expressiva da ferramenta.

---

## Créditos

- Interpretador base: [Frotz](https://gitlab.com/DavidGriffith/frotz) (GPL).
- Arquivo do jogo: [the-infocom-files/zork1](https://github.com/the-infocom-files/zork1).
