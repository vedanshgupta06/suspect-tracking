"""Simulate low-quality CCTV / arrest imagery on face crops."""
import io
import numpy as np
from PIL import Image, ImageFilter

CONDITIONS = {
    "clean": [],
    "blur": [("blur", 2.0)],
    "lowres": [("downscale", 32)],
    "jpeg": [("jpeg", 15)],
    "cctv": [("downscale", 32), ("blur", 1.0), ("jpeg", 20), ("noise", 8)],
}


def apply_ops(img: Image.Image, ops, rng: np.random.Generator) -> Image.Image:
    img = img.convert("RGB")
    size = img.size
    for op, val in ops:
        if op == "blur":
            img = img.filter(ImageFilter.GaussianBlur(val))
        elif op == "downscale":
            img = img.resize((val, val), Image.BILINEAR).resize(size, Image.BILINEAR)
        elif op == "jpeg":
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=int(val))
            buf.seek(0)
            img = Image.open(buf).convert("RGB")
        elif op == "noise":
            arr = np.asarray(img).astype(np.float32)
            arr += rng.normal(0, val, arr.shape)
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
        else:
            raise ValueError(op)
    return img


def random_degrade(img: Image.Image, rng: np.random.Generator) -> Image.Image:
    """Random mix/strength of degradations (different from the fixed eval settings on purpose)."""
    ops = []
    if rng.random() < 0.6:
        ops.append(("downscale", int(rng.integers(24, 65))))
    if rng.random() < 0.5:
        ops.append(("blur", float(rng.uniform(0.5, 2.5))))
    if rng.random() < 0.5:
        ops.append(("jpeg", int(rng.integers(10, 60))))
    if rng.random() < 0.4:
        ops.append(("noise", float(rng.uniform(2, 10))))
    if rng.random() < 0.15:
        ops = []  # keep some clean pairs so clean accuracy doesn't drift
    return apply_ops(img, ops, rng)
