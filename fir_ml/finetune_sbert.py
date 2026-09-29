"""Fine-tune Sentence-BERT so FIRs of the same MO embed close together.
Uses the TRAIN split only (never db or query). One pair per known MO per step, so all
other pairs in the batch are true negatives.

    python finetune_sbert.py --steps 100
    python evaluate_fir.py --methods tfidf,sbert,sbert_ft --ft-model ft_sbert
"""
import argparse, random
import torch
import torch.nn.functional as F
from sentence_transformers import SentenceTransformer

from fir_data import load_split

BASE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def embed(model, texts, device):
    feats = {k: v.to(device) for k, v in model.tokenize(texts).items()}
    return F.normalize(model(feats)["sentence_embedding"], dim=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="firs.json")
    ap.add_argument("--steps", type=int, default=100)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--scale", type=float, default=20.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="ft_sbert")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    torch.manual_seed(a.seed)

    train, _, _ = load_split(a.data, a.seed)
    by_mo = {}
    for d in train:
        by_mo.setdefault(d["label"], []).append(d["text"])
    mos = sorted(by_mo)
    print(f"{len(train)} training FIRs across {len(mos)} MOs")

    model = SentenceTransformer(BASE_MODEL)
    device = next(model.parameters()).device
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)

    for step in range(1, a.steps + 1):
        pairs = [rng.sample(by_mo[mo], 2) for mo in mos]
        ea = embed(model, [p[0] for p in pairs], device)
        eb = embed(model, [p[1] for p in pairs], device)
        logits = a.scale * ea @ eb.T
        labels = torch.arange(len(mos), device=device)
        loss = (F.cross_entropy(logits, labels) + F.cross_entropy(logits.T, labels)) / 2
        opt.zero_grad()
        loss.backward()
        opt.step()
        if step % 10 == 0 or step == 1:
            print(f"step {step}/{a.steps}  loss {loss.item():.4f}")

    model.eval()
    model.save(a.out)
    print(f"saved {a.out}")


if __name__ == "__main__":
    main()
