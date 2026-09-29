"""Gallery of suspect embeddings - this is the piece the backend API will call."""
import numpy as np


class FaceGallery:
    def __init__(self, dim=512):
        self.dim = dim
        self.ids = np.array([], dtype=np.int64)
        self.emb = np.zeros((0, dim), dtype=np.float32)

    def add(self, suspect_id: int, embedding: np.ndarray):
        e = embedding / (np.linalg.norm(embedding) + 1e-12)
        self.ids = np.append(self.ids, suspect_id)
        self.emb = np.vstack([self.emb, e.astype(np.float32)])

    def search(self, query: np.ndarray, top_k=5, threshold=0.6):
        """Ranked candidate aliases. One entry per suspect (best of their stored faces)."""
        if len(self.ids) == 0:
            return []
        q = query / (np.linalg.norm(query) + 1e-12)
        sims = self.emb @ q
        best = {}
        for sid, s in zip(self.ids, sims):
            best[int(sid)] = max(best.get(int(sid), -1.0), float(s))
        ranked = sorted(best.items(), key=lambda kv: -kv[1])[:top_k]
        return [{"suspect_id": sid, "score": round(s, 4), "is_match": s >= threshold}
                for sid, s in ranked]

    def save(self, path):
        np.savez(path, ids=self.ids, emb=self.emb)

    @classmethod
    def load(cls, path):
        d = np.load(path)
        g = cls(dim=d["emb"].shape[1])
        g.ids, g.emb = d["ids"], d["emb"]
        return g
