# Protótipo 1 (PT-BR no código) processando texto em INGLÊS:
# TF-IDF + expansão dinâmica (WordNet: sinônimos)
# WordNet conflito com pré-lematização do jeito que está implementado, tirei lematização
# Mudança de estruturas para não precisar de python hash seed. Ordem dos candidatos agora é ordenada.

import re
import time
import nltk
from typing import List, Tuple, Dict, Set
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data.commands import COMANDOS_ESPERADOS, ENTRADAS_DE_TESTE


nltk.download('punkt_tab', quiet=True)
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)


from nltk.corpus import stopwords, wordnet as wn

# Parâmetros
LIMIAR_SIMILARIDADE = 0.70
LIMIAR_SIMILARIDADE_EXTREMO = 0.85
USAR_EXPANSAO_WN = True
# INCLUIR_ANTONIMOS = False # Diminui o resultado, talvez seja possível implementar, mas com algumas modificações no cerne dos métodos

# Stopwords
EN_STOPWORDS: Set[str] = set()
try:
    EN_STOPWORDS = set(stopwords.words("english"))
except LookupError:
    print("lookuperror")
    EN_STOPWORDS = set()

# Tokenização. Possibilidades: colocar stemming ou *lematization* junto da tokenização
def tokenizacao_en(texto: str) -> List[str]:
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    tokens = nltk.word_tokenize(texto, language="english")
    tokens = [t for t in tokens if t.isalnum() and t not in EN_STOPWORDS]
    return tokens

# Expansão WordNet
class ExpansorWordNet:
    def __init__(self, vocab: Set[str]):
        self.vocab = vocab
        self._cache: Dict[str, List[str]] = {}

    def candidatos(self, token: str) -> List[str]:
        if token in self._cache:
            return self._cache[token]
        cands = set()
        try:
            synsets = wn.synsets(token)
        except LookupError:
            synsets = []
        for s in synsets:
            for lemma in s.lemmas():
                nome = lemma.name().lower().replace("_", " ")
                for subtok in tokenizacao_en(nome):
                    if subtok in self.vocab:
                        cands.add(subtok)
        ordenado = sorted(cands)
        self._cache[token] = ordenado
        return ordenado

    def aplicar(self, tokens: List[str]) -> List[str]:
        resultado = []
        for t in tokens:
            if t in self.vocab:
                resultado.append(t)
            else:
                cands = self.candidatos(t)
                if cands:
                    resultado.append(cands[0])  # escolha determinística
                else:
                    resultado.append(t)
        # deduplicação preservando ordem
        seen = set()
        return [x for x in resultado if not (x in seen or seen.add(x))]

# Matcher principal
class MatcherTFIDFWordNet:
    def __init__(self, comandos):
        self.comandos_orig = list(comandos)
        self.comandos_proc_tokens = [tokenizacao_en(c) for c in self.comandos_orig]
        self.comandos_proc = [" ".join(tks) for tks in self.comandos_proc_tokens]

        self.vectorizer = TfidfVectorizer(
            tokenizer=lambda s: s.split(), # Evitra tokenização dupla pelo sklearn
            preprocessor=lambda s: s,
            lowercase=False
        )
        self.matriz_cmds = self.vectorizer.fit_transform(self.comandos_proc)
        self.vocab = set(self.vectorizer.get_feature_names_out())
        self.expansor = ExpansorWordNet(self.vocab) if USAR_EXPANSAO_WN else None

    def interpretar(self, entrada: str) -> Tuple[str, float, str]:
        tokens = tokenizacao_en(entrada)
        if self.expansor:
            tokens_expandidos = self.expansor.aplicar(tokens)
        else:
            tokens_expandidos = tokens

        # Deduplicação final
        seen = set()
        tokens_finais = [t for t in tokens_expandidos if not (t in seen or seen.add(t))]
        representacao = " ".join(tokens_finais) if tokens_finais else ""
        if not representacao:
            return "", 0.0, representacao

        q_vec = self.vectorizer.transform([representacao])
        sims = cosine_similarity(q_vec, self.matriz_cmds).flatten()
        idx = int(sims.argmax())
        return self.comandos_orig[idx], float(sims[idx]), representacao

if __name__ == "__main__":
    inicio = time.perf_counter()
    matcher = MatcherTFIDFWordNet(COMANDOS_ESPERADOS)

    print("=== Protótipo: TF-IDF + WordNet===")
    
    sugeridos, corrigidos, total = 0, 0, 0
    for entrada, esperado in ENTRADAS_DE_TESTE.items():
        melhor_comando, score, proc = matcher.interpretar(entrada)
        total += 1
        similar = (melhor_comando == esperado) and (score > LIMIAR_SIMILARIDADE)
        if similar:
            sugeridos += 1
            print(f"{total:3d}> {entrada:35s} -> {melhor_comando:20s} (esp: {esperado}) [score={score:.3f}] proc='{proc}'")
        
        extremamente_similar = (melhor_comando == esperado) and (score > LIMIAR_SIMILARIDADE_EXTREMO)
        if extremamente_similar:
            corrigidos +=1
            print(f"{total}> {entrada:30s} -> {melhor_comando or 'None':20s} (esperado: {esperado}) [score={score:.3f}]")

    tempo_gasto = time.perf_counter() - inicio
    print(f"\nAcurácia (sugere se score > {LIMIAR_SIMILARIDADE:.2f} ou aceita se score > {LIMIAR_SIMILARIDADE_EXTREMO:.2f}")
    print(f"Sugeridos: {sugeridos}/{total} = {sugeridos/total:.2%}")
    print(f"Corrigidos: {corrigidos}/{total} = {corrigidos/total:.2%}")
    print(f"Tempo total: {tempo_gasto:.3f}s")