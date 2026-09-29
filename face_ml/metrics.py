import numpy as np


def search(gal_emb, gal_ids, probe_emb, k=5):
    sims = probe_emb @ gal_emb.T
    order = np.argsort(-sims, axis=1)[:, :k]
    top1_ids = gal_ids[order[:, 0]]
    top1_scores = sims[np.arange(len(sims)), order[:, 0]]
    topk_ids = gal_ids[order]
    return top1_ids, top1_scores, topk_ids


def prf_at(thr, top1_ids, scores, probe_ids):
    """Alias-match precision/recall: a flag is correct only if score>=thr AND the id is right."""
    accepted = scores >= thr
    correct = accepted & (top1_ids == probe_ids)
    tp = int(correct.sum())
    fp = int((accepted & ~correct).sum())
    fn = int(((probe_ids != -1) & ~correct).sum())
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f1


def best_threshold(thresholds, top1_ids, scores, probe_ids):
    f1s = [prf_at(t, top1_ids, scores, probe_ids)[2] for t in thresholds]
    return float(thresholds[int(np.argmax(f1s))])


def rank_acc(topk_ids, probe_ids, k):
    known = probe_ids != -1
    if known.sum() == 0:
        return 0.0
    hits = (topk_ids[known, :k] == probe_ids[known, None]).any(axis=1)
    return float(hits.mean())
