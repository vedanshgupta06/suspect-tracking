"""Run: python evaluate.py --n-identities 300
Threshold is tuned on a validation half of the probes and reported on a held-out test half."""
import argparse, os, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from dataset import load_lfw
from degrade import CONDITIONS, apply_ops
from embedder import FaceEmbedder
from metrics import search, prf_at, best_threshold, rank_acc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-identities", type=int, default=300)
    ap.add_argument("--max-per-id", type=int, default=6)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-detect", action="store_true", help="skip MTCNN (faster, LFW is pre-centred)")
    ap.add_argument("--weights", default=None, help="fine-tuned checkpoint (facenet_ft.pt)")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)

    ds = load_lfw(a.n_identities, a.max_per_id, seed=a.seed)
    print(f"gallery={len(ds.gallery_images)}  probes={len(ds.probe_images)} "
          f"(unknown-person probes={(ds.probe_ids == -1).sum()})")

    fe = FaceEmbedder(use_detector=not a.no_detect, weights=a.weights)
    print("cropping faces...")
    gal_crops = [fe.crop(im) for im in ds.gallery_images]
    probe_crops = [fe.crop(im) for im in ds.probe_images]
    gal_emb = fe.embed_crops(gal_crops)

    perm = rng.permutation(len(probe_crops))
    val, test = perm[: len(perm) // 2], perm[len(perm) // 2:]
    thresholds = np.linspace(0.2, 0.95, 76)

    rows, curves, clean_thr = [], {}, None
    for name, ops in CONDITIONS.items():
        print(f"condition: {name}")
        deg = [apply_ops(c, ops, rng) for c in probe_crops]
        p_emb = fe.embed_crops(deg)
        t0 = time.perf_counter()
        top1, sc, topk = search(gal_emb, ds.gallery_ids, p_emb)
        ms = (time.perf_counter() - t0) / len(p_emb) * 1000

        own_thr = best_threshold(thresholds, top1[val], sc[val], ds.probe_ids[val])
        if name == "clean":
            clean_thr = own_thr
        for tag, thr in (("clean-tuned", clean_thr), ("own-tuned", own_thr)):
            p, r, f1 = prf_at(thr, top1[test], sc[test], ds.probe_ids[test])
            rows.append(dict(condition=name, threshold_from=tag, threshold=round(thr, 3),
                             precision=round(p, 3), recall=round(r, 3), f1=round(f1, 3),
                             rank1=round(rank_acc(topk[test], ds.probe_ids[test], 1), 3),
                             rank5=round(rank_acc(topk[test], ds.probe_ids[test], 5), 3),
                             ms_per_search=round(ms, 4)))
        pr = [prf_at(t, top1[test], sc[test], ds.probe_ids[test])[:2] for t in thresholds]
        curves[name] = ([x[1] for x in pr], [x[0] for x in pr])

    df = pd.DataFrame(rows)
    df.to_csv(f"{a.out}/results.csv", index=False)
    print("\n", df.to_string(index=False))

    plt.figure(figsize=(6, 5))
    for name, (r, p) in curves.items():
        plt.plot(r, p, label=name)
    plt.xlabel("Recall"); plt.ylabel("Precision"); plt.title("Alias detection (test split)")
    plt.legend(); plt.grid(alpha=.3); plt.savefig(f"{a.out}/pr_curves.png", dpi=150, bbox_inches="tight")
    print(f"\nsaved {a.out}/results.csv and pr_curves.png (clean-tuned threshold = {clean_thr:.3f})")


if __name__ == "__main__":
    main()
