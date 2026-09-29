"""Bridges the backend to the face_ml and fir_ml modules (sibling folders), and to the DB.

Embeddings are stored as float32 bytes in the DB (Suspect.face_embedding, Case.fir_embedding)
and loaded straight into the in-memory FaceGallery / FIRLinker on startup, so the heavy models
only need to run once per new photo / new FIR, not on every app restart.
"""
import sys
from pathlib import Path

import numpy as np
from sqlalchemy.orm import Session

from . import config

sys.path.insert(0, str(Path(config.FACE_ML_PATH).resolve()))
sys.path.insert(0, str(Path(config.FIR_ML_PATH).resolve()))

_face_embedder = None
_face_gallery = None
_fir_linker = None


def to_bytes(vec: np.ndarray) -> bytes:
    return vec.astype(np.float32).tobytes()


def from_bytes(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)


# ---------------------------------------------------------------- face ----
def get_face_embedder():
    global _face_embedder
    if _face_embedder is None:
        from embedder import FaceEmbedder  # face_ml/embedder.py
        _face_embedder = FaceEmbedder()
    return _face_embedder


def get_face_gallery():
    global _face_gallery
    if _face_gallery is None:
        from matcher import FaceGallery  # face_ml/matcher.py
        _face_gallery = FaceGallery()
    return _face_gallery


def load_face_gallery_from_db(db: Session):
    from .models import Suspect
    gallery = get_face_gallery()
    ids, vecs = [], []
    for s in db.query(Suspect).filter(Suspect.face_embedding.isnot(None)).all():
        ids.append(s.id)
        vecs.append(from_bytes(s.face_embedding))
    if vecs:
        gallery.ids = np.array(ids, dtype=np.int64)
        gallery.emb = np.vstack(vecs).astype(np.float32)
    print(f"[ml_services] loaded {len(ids)} face embeddings into gallery")


def embed_face_image(image_bytes: bytes) -> np.ndarray:
    from PIL import Image
    import io
    img = Image.open(io.BytesIO(image_bytes))
    return get_face_embedder().embed(img)


def search_face(embedding: np.ndarray, top_k=5, threshold=None):
    threshold = config.FACE_MATCH_THRESHOLD if threshold is None else threshold
    return get_face_gallery().search(embedding, top_k=top_k, threshold=threshold)


def add_face_to_gallery(suspect_id: int, embedding: np.ndarray):
    get_face_gallery().add(suspect_id, embedding)


# ----------------------------------------------------------------- fir ----
def get_fir_linker():
    global _fir_linker
    if _fir_linker is None:
        from linker import FIRLinker  # fir_ml/linker.py
        model_path = config.FIR_MODEL_PATH
        _fir_linker = FIRLinker(model_path) if Path(model_path).exists() else FIRLinker()
    return _fir_linker


def load_fir_linker_from_db(db: Session):
    from .models import Case
    linker = get_fir_linker()
    ids, vecs = [], []
    for c in db.query(Case).filter(Case.fir_embedding.isnot(None)).all():
        ids.append(c.id)
        vecs.append(from_bytes(c.fir_embedding))
    if vecs:
        linker.ids = ids
        linker.emb = np.vstack(vecs).astype(np.float32)
    print(f"[ml_services] loaded {len(ids)} FIR embeddings into linker")


def embed_fir_text(text: str) -> np.ndarray:
    return get_fir_linker()._enc([text])[0]


def link_fir(text_embedding: np.ndarray, top_k=5, threshold=None):
    threshold = config.FIR_LINK_THRESHOLD if threshold is None else threshold
    linker = get_fir_linker()
    if not linker.ids:
        return []
    sims = linker.emb @ text_embedding
    order = np.argsort(-sims)[:top_k]
    return [{"case_id": linker.ids[i], "score": round(float(sims[i]), 4),
             "is_link": bool(sims[i] >= threshold)} for i in order]


def add_fir_to_linker(case_id: int, embedding: np.ndarray):
    linker = get_fir_linker()
    linker.ids.append(case_id)
    linker.emb = np.vstack([linker.emb, embedding.astype(np.float32)])
