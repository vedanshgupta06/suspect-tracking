"""FIR case linker for the backend: suggests existing unsolved cases with a similar MO."""
import numpy as np

BASE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class FIRLinker:
    def __init__(self, model_name=BASE_MODEL):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.ids, self.emb = [], np.zeros((0, self.model.get_sentence_embedding_dimension()), np.float32)

    def _enc(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)

    def add(self, case_id, text):
        self.ids.append(case_id)
        self.emb = np.vstack([self.emb, self._enc([text])])

    def link(self, text, top_k=5, threshold=0.5):
        """Ranked similar unsolved cases; is_link says whether the score clears the threshold."""
        if not self.ids:
            return []
        sims = self.emb @ self._enc([text])[0]
        order = np.argsort(-sims)[:top_k]
        return [{"case_id": self.ids[i], "score": round(float(sims[i]), 4),
                 "is_link": bool(sims[i] >= threshold)} for i in order]

    def save(self, path):
        np.savez(path, ids=np.array(self.ids), emb=self.emb)

    def load_embeddings(self, path):
        d = np.load(path, allow_pickle=False)
        self.ids, self.emb = d["ids"].tolist(), d["emb"]
