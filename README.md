# IF Interaction Improved with NLP
(Explicação feita automaticamente pela IA do Github. Verifiquei e está correta.)

## Uso

Uso com ambiente virtual do python.

```bash
pip install -r requirements.txt
```

```bash
# Modo com algoritmo (padrão)
python main.py 1

# Modo puro (sem processamento)
python main.py 0
```

Um sistema de processamento de linguagem natural para interação aprimorada com ficção interativa (Interactive Fiction). O projeto melhora a compreensão e o tratamento de comandos de usuário através de estratégias de similaridade semântica e matching de verbos.

## Características

- **Extração de Dicionário**: Decodifica e extrai vocabulário de arquivos Z-machine (formato `.z3`)
- **Classificação de Verbos**: Identifica e classifica verbos usando WordNet e análise de âncoras semânticas
- **Matching Inteligente**: Realiza correspondência de verbos do usuário com verbos disponíveis no jogo
- **Servidor de Comunicação**: Socket TCP que processa comandos de usuário com sugestões e correções automáticas
- **Estratégias Configuráveis**: Suporte a diferentes estratégias de similaridade (semântica + string-based)

## Componentes Principais

- `main.py` - Ponto de entrada da aplicação
- `frotz_server.py` - Servidor socket para comunicação com o cliente
- `matchers.py` - Lógica de matching de verbos
- `similarity_strategy.py` - Estratégias de cálculo de similaridade
- `recon.py` - Classificação e reconhecimento de verbos usando WordNet
- `zmachine_dict.py` - Decodificação de dicionários Z-machine
- `tokenizer.py` - Processamento e tokenização de texto

## Configuração

Edite `config.py` para ajustar:

- Host e porta do servidor
- Limiares de sugestão e correção automática
- Caminho do arquivo do jogo
- Estratégia de similaridade

## Requisitos

- Python 3.10+
- NLTK com WordNet
- Arquivo de jogo Z3 compatível

## Créditos
Arquivo do jogo 
https://github.com/the-infocom-files/zork1