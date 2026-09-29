"""Open-set alias-detection split built from LFW.

known identities   -> one clean image goes in the gallery ("database"),
                      their other images are probes that SHOULD match (repeat offenders/aliases)
unknown identities -> all images are probes that should NOT match (new suspects)
"""
from dataclasses import dataclass
import numpy as np
from PIL import Image


@dataclass
class Split:
    gallery_images: list
    gallery_ids: np.ndarray
    probe_images: list
    probe_ids: np.ndarray  # -1 = unknown person (no match expected)


def load_lfw(n_identities=300, max_per_id=6, known_frac=0.7, seed=0) -> Split:
    from sklearn.datasets import fetch_lfw_people

    lfw = fetch_lfw_people(
        min_faces_per_person=2, color=True, resize=1.0,
        slice_=(slice(0, 250), slice(0, 250)),
    )
    imgs, targets = lfw.images, lfw.target
    if imgs.max() <= 1.0:
        imgs = imgs * 255.0
    imgs = imgs.astype(np.uint8)

    rng = np.random.default_rng(seed)
    ids = rng.permutation(np.unique(targets))[:n_identities]
    n_known = int(len(ids) * known_frac)
    known, unknown = set(ids[:n_known]), set(ids[n_known:])

    g_imgs, g_ids, p_imgs, p_ids = [], [], [], []
    for pid in ids:
        idx = rng.permutation(np.where(targets == pid)[0])[:max_per_id]
        if pid in known:
            g_imgs.append(Image.fromarray(imgs[idx[0]]))
            g_ids.append(int(pid))
            for j in idx[1:]:
                p_imgs.append(Image.fromarray(imgs[j]))
                p_ids.append(int(pid))
        else:
            for j in idx:
                p_imgs.append(Image.fromarray(imgs[j]))
                p_ids.append(-1)
    return Split(g_imgs, np.array(g_ids), p_imgs, np.array(p_ids))


def load_lfw_train(n_eval_identities=300, n_train_identities=500, max_per_id=4, seed=0):
    """Groups of images per identity, DISJOINT from the identities used by load_lfw.
    n_eval_identities and seed must match the values used in evaluate.py."""
    from sklearn.datasets import fetch_lfw_people

    lfw = fetch_lfw_people(
        min_faces_per_person=2, color=True, resize=1.0,
        slice_=(slice(0, 250), slice(0, 250)),
    )
    imgs, targets = lfw.images, lfw.target
    if imgs.max() <= 1.0:
        imgs = imgs * 255.0
    imgs = imgs.astype(np.uint8)

    rng = np.random.default_rng(seed)
    ids = rng.permutation(np.unique(targets))  # same permutation as load_lfw
    train_ids = ids[n_eval_identities:n_eval_identities + n_train_identities]
    groups = []
    for pid in train_ids:
        idx = rng.permutation(np.where(targets == pid)[0])[:max_per_id]
        groups.append([Image.fromarray(imgs[j]) for j in idx])
    return groups
