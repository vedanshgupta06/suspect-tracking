"""python evaluate_fir.py --methods tfidf,sbert[,sbert_ft --ft-model ft_sbert]"""
import argparse, os, time
from collections import Counter
import numpy as np
import pandas as pd

from fir_data import load_split, NOVEL_LABEL
from fir_metrics import ranking_metrics, link_prf, best_threshold

BASE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def sims_tfidf(db_texts, q_texts):
    from sklearn.feature_extraction.text import TfidfVectorizer
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english")
    X = vec.fit_transform(db_texts)  # fitted on the existing cases only
    return (vec.transform(q_texts) @ X.T).toarray()


def sims_sbert(model_name, db_texts, q_texts):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(model_name)
    enc = lambda t: m.encode(t, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return enc(q_texts) @ enc(db_texts).T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="firs.json")
    ap.add_argument("--methods", default="tfidf,sbert")
    ap.add_argument("--ft-model", default="ft_sbert")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results_fir")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    _, db, query = load_split(a.data, a.seed)
    db_texts, q_texts = [d["text"] for d in db], [q["text"] for q in query]
    db_labels, q_labels = np.array([d["label"] for d in db]), np.array([q["label"] for q in query])
    print(f"db={len(db)} cases  queries={len(query)} (novel-MO queries={(q_labels == NOVEL_LABEL).sum()})")

    perm = np.random.default_rng(a.seed).permutation(len(query))
    val, test = perm[: len(perm) // 2], perm[len(perm) // 2:]

    rows = []
    for m in a.methods.split(","):
        t0 = time.perf_counter()
        if m == "tfidf":
            S = sims_tfidf(db_texts, q_texts)
        elif m == "sbert":
            S = sims_sbert(BASE_MODEL, db_texts, q_texts)
        elif m == "sbert_ft":
            S = sims_sbert(a.ft_model, db_texts, q_texts)
        else:
            raise SystemExit(f"unknown method {m}")
        ms = (time.perf_counter() - t0) / len(q_texts) * 1000

        thr = best_threshold(S[val], db_labels, q_labels[val])
        rk = ranking_metrics(S[test], db_labels, q_labels[test])
        p, r, f1 = link_prf(S[test], db_labels, q_labels[test], thr)
        rows.append(dict(method=m, hit1=round(rk["hit1"], 3), hit5=round(rk["hit5"], 3),
                         p5=round(rk["p5"], 3), mrr=round(rk["mrr"], 3), threshold=round(thr, 3),
                         precision=round(p, 3), recall=round(r, 3), f1=round(f1, 3),
                         ms_per_query_incl_encoding=round(ms, 2)))

        # most common wrong top-1 links (known-MO test queries)
        kt = [i for i in test if q_labels[i] != NOVEL_LABEL]
        wrong = Counter((q_labels[i], db_labels[S[i].argmax()]) for i in kt
                        if db_labels[S[i].argmax()] != q_labels[i])
        print(f"\n[{m}] most confused (true -> predicted):", wrong.most_common(4))

    df = pd.DataFrame(rows)
    df.to_csv(f"{a.out}/results.csv", index=False)
    print("\n", df.to_string(index=False))
    print(f"\nsaved {a.out}/results.csv")


if __name__ == "__main__":
    main()
