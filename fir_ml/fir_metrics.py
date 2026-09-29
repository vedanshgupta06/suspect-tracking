import numpy as np
from fir_data import NOVEL_LABEL


def ranking_metrics(sims, db_labels, q_labels):
    """Only known-MO queries. Hit@k: a same-MO case appears in the top k."""
    known = q_labels != NOVEL_LABEL
    s, ql = sims[known], q_labels[known]
    match = db_labels[np.argsort(-s, axis=1)] == ql[:, None]
    first = match.argmax(axis=1)
    return dict(hit1=match[:, 0].mean(), hit5=match[:, :5].any(1).mean(),
                p5=match[:, :5].mean(), mrr=(1.0 / (first + 1)).mean())


def link_prf(sims, db_labels, q_labels, thr):
    """A link is proposed when the top score >= thr; correct only if its MO is right.
    Novel-MO queries should get no link (any link on them is a false positive)."""
    score = sims.max(1)
    pred = db_labels[sims.argmax(1)]
    accepted = score >= thr
    correct = accepted & (pred == q_labels)
    known = q_labels != NOVEL_LABEL
    tp, fp = int(correct.sum()), int((accepted & ~correct).sum())
    fn = int((known & ~correct).sum())
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def best_threshold(sims, db_labels, q_labels, grid=np.linspace(0, 1, 201)):
    f1s = [link_prf(sims, db_labels, q_labels, t)[2] for t in grid]
    return float(grid[int(np.argmax(f1s))])
