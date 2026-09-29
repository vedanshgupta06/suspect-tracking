# Face ML module

    pip install -r requirements.txt      # if torch conflicts: pip install facenet-pytorch --no-deps
    python evaluate.py --n-identities 300 --no-detect   # quick run
    python evaluate.py --n-identities 500               # full run with MTCNN alignment

First run downloads LFW (~200 MB) and the pretrained weights.
Outputs: results/results.csv, results/pr_curves.png.

Fine-tune (optional):
    python finetune.py --steps 200
    python evaluate.py --weights ft/facenet_ft.pt --out results_ft

`matcher.py` (FaceGallery) is what the backend calls: add(suspect_id, embedding) at arrest, search(embedding) for alias candidates.
