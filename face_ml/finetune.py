"""Fine-tune the last FaceNet blocks so degraded (CCTV-like) faces land near the clean
gallery embedding of the same person.

    python finetune.py --steps 200
    python evaluate.py --weights ft/facenet_ft.pt --out results_ft

Each step: B identities, one CLEAN image (gallery role) + one DIFFERENT image of the same
person, randomly DEGRADED (probe role). In-batch contrastive loss: the matching clean/degraded
pair is the positive, all other identities in the batch are negatives.
Training identities are disjoint from the evaluation identities.
"""
import argparse, os, pickle
import numpy as np
import torch
import torch.nn.functional as F

from dataset import load_lfw_train
from degrade import random_degrade
from embedder import FaceEmbedder


def to_tensor(crops, device):
    arr = np.stack([np.asarray(c.convert("RGB").resize((160, 160))) for c in crops])
    x = torch.from_numpy(arr).permute(0, 3, 1, 2).float()
    return ((x - 127.5) / 128.0).to(device)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-eval-identities", type=int, default=300, help="must match evaluate.py --n-identities")
    ap.add_argument("--n-train-identities", type=int, default=500)
    ap.add_argument("--steps", type=int, default=200)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--temp", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-detect", action="store_true")
    ap.add_argument("--out", default="ft")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    torch.manual_seed(a.seed)

    fe = FaceEmbedder(use_detector=not a.no_detect)
    cache = f"{a.out}/train_crops.pkl"
    if os.path.exists(cache):
        groups = pickle.load(open(cache, "rb"))
    else:
        raw = load_lfw_train(a.n_eval_identities, a.n_train_identities, seed=a.seed)
        print(f"cropping faces for {len(raw)} training identities (cached after this)...")
        groups = [[fe.crop(im) for im in g] for g in raw]
        pickle.dump(groups, open(cache, "wb"))
    groups = [g for g in groups if len(g) >= 2]
    print(f"{len(groups)} training identities")

    model = fe.model
    model.eval()  # keep BatchNorm statistics frozen (small batches)
    for p in model.parameters():
        p.requires_grad = False
    params = []
    for m in (model.repeat_3, model.block8, model.last_linear, model.last_bn):
        for p in m.parameters():
            p.requires_grad = True
            params.append(p)
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=1e-4)
    bsz = min(a.batch, len(groups))

    for step in range(1, a.steps + 1):
        chosen = rng.choice(len(groups), size=bsz, replace=False)
        clean, deg = [], []
        for gi in chosen:
            i, j = rng.choice(len(groups[gi]), 2, replace=False)
            clean.append(groups[gi][i])
            deg.append(random_degrade(groups[gi][j], rng))
        ea = F.normalize(model(to_tensor(clean, fe.device)), dim=1)
        eb = F.normalize(model(to_tensor(deg, fe.device)), dim=1)
        logits = ea @ eb.T / a.temp
        labels = torch.arange(bsz, device=fe.device)
        loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 10 == 0 or step == 1:
            acc = (logits.argmax(1) == labels).float().mean().item()
            print(f"step {step}/{a.steps}  loss {loss.item():.4f}  in-batch acc {acc:.2f}")

    torch.save(model.state_dict(), f"{a.out}/facenet_ft.pt")
    print(f"saved {a.out}/facenet_ft.pt")


if __name__ == "__main__":
    main()
