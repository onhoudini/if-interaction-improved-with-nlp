import re
import time
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sentence_transformers import SentenceTransformer, util
from data.commands import COMANDOS_ESPERADOS, ENTRADAS_DE_TESTE

LIMIAR_SIMILARIDADE = 0.70
LIMIAR_SIMILARIDADE_EXTREMO = 0.85

def normalizar(texto: str)->str:
    tokens = re.findall(r"[a-z0-9]+", texto.lower())
    return " ".join(t for t in tokens if t and t not in ENGLISH_STOP_WORDS)

class SBERTMatcher:
    def __init__(self, comandos, modelo="all-MiniLM-L6-v2"):
        self.comandos = list(comandos)
        self.modelo = SentenceTransformer(modelo)
        self.comandos_normalizados = [normalizar(c) for c in self.comandos]
        self.comandos_embeddings = self.modelo.encode(
            self.comandos_normalizados, convert_to_tensor=True, normalize_embeddings=True
        )

    def interpretacao(self, entrada_jogador: str):
        qnorm = normalizar(entrada_jogador)
        q_emb = self.modelo.encode([qnorm], convert_to_tensor=True, normalize_embeddings=True)
        similaridades = util.cos_sim(q_emb, self.comandos_embeddings)[0]
        melhor_idx = int(similaridades.argmax().item())
        melhor_score = float(similaridades[melhor_idx].item())
        return self.comandos[melhor_idx], melhor_score, qnorm
    
if __name__ == "__main__":
    start = time.perf_counter()
    matcher = SBERTMatcher(COMANDOS_ESPERADOS)
    print("=== Protótipo 2: SBERT ===")
    
    sugeridos, corrigidos, total = 0, 0, 0
    for entrada, esperado in ENTRADAS_DE_TESTE.items():
        melhor_comando, score, qnorm = matcher.interpretacao(entrada)
        total += 1
        similar = (melhor_comando == esperado) and (score > LIMIAR_SIMILARIDADE)
        if similar:
            sugeridos += 1
            print(f"{total}> {entrada:30s} -> {melhor_comando or 'None':20s} (esperado: {esperado}) [score={score:.3f}]")
        
        extremamente_similar = (melhor_comando == esperado) and (score > LIMIAR_SIMILARIDADE_EXTREMO)
        if extremamente_similar:
            corrigidos +=1
            print(f"{total}> {entrada:30s} -> {melhor_comando or 'None':20s} (esperado: {esperado}) [score={score:.3f}]")
        
    tempo_gasto = time.perf_counter() - start
    print(f"\nAcurácia (sugere se score > {LIMIAR_SIMILARIDADE:.2f} ou aceita se score > {LIMIAR_SIMILARIDADE_EXTREMO:.2f}")
    print(f"Sugeridos: {sugeridos}/{total} = {sugeridos/total:.2%}")
    print(f"Corrigidos: {corrigidos}/{total} = {corrigidos/total:.2%}")
    print(f"Tempo total: {tempo_gasto:.3f}s")