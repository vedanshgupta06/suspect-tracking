"""Distillation fine-tune (safer than finetune.py): the student sees a DEGRADED face and must
reproduce the frozen original model's embedding of the CLEAN version of the same image.
Clean inputs are also anchored to the teacher, so the embedding space doesn't drift.

    python finetune_distill.py --steps 300
    python evaluate.py --weights ft_distill/facenet_ft.pt --out results_distill

Reuses the cropped training faces cached by finetune.py (ft/train_crops.pkl).
"""
import argparse, copy, os, pickle
import numpy as np
import torch
import torch.nn.functional as F

from degrade import random_degrade
from embedder import FaceEmbedder
from finetune import to_tensor


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--crops", default="ft/train_crops.pkl")
    ap.add_argument("--steps", type=int, default=300)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="ft_distill")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    torch.manual_seed(a.seed)

    imgs = [im for g in pickle.load(open(a.crops, "rb")) for im in g]
    print(f"{len(imgs)} training faces")

    fe = FaceEmbedder(use_detector=False)
    student = fe.model.eval()
    teacher = copy.deepcopy(student).eval()
    for p in teacher.parameters():
        p.requires_grad = False
    for p in student.parameters():
        p.requires_grad = False
    params = []
    for m in (student.block8, student.last_linear, student.last_bn):
        for p in m.parameters():
            p.requires_grad = True
            params.append(p)
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=1e-4)

    for step in range(1, a.steps + 1):
        idx = rng.choice(len(imgs), size=min(a.batch, len(imgs)), replace=False)
        clean = [imgs[i] for i in idx]
        deg = [random_degrade(im, rng) for im in clean]
        with torch.no_grad():
            t = F.normalize(teacher(to_tensor(clean, fe.device)), dim=1)
        s_deg = F.normalize(student(to_tensor(deg, fe.device)), dim=1)
        s_cln = F.normalize(student(to_tensor(clean, fe.device)), dim=1)
        loss = (1 - (s_deg * t).sum(1)).mean() + (1 - (s_cln * t).sum(1)).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 10 == 0 or step == 1:
            print(f"step {step}/{a.steps}  loss {loss.item():.4f}  "
                  f"cos(deg,teacher) {(s_deg * t).sum(1).mean().item():.3f}")

    torch.save(student.state_dict(), f"{a.out}/facenet_ft.pt")
    print(f"saved {a.out}/facenet_ft.pt")


if __name__ == "__main__":
    main()
