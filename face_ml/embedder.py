"""Face detection + embedding (FaceNet / InceptionResnetV1, pretrained on VGGFace2)."""
import numpy as np
import torch
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1


class FaceEmbedder:
    def __init__(self, device=None, use_detector=True, weights=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.mtcnn = (
            MTCNN(image_size=160, margin=20, post_process=False, device=self.device)
            if use_detector else None
        )
        self.model = InceptionResnetV1(pretrained="vggface2")
        if weights:  # fine-tuned checkpoint from finetune.py
            self.model.load_state_dict(torch.load(weights, map_location="cpu"))
        self.model = self.model.eval().to(self.device)

    def crop(self, img: Image.Image) -> Image.Image:
        """Return an aligned 160x160 face crop (falls back to center crop)."""
        img = img.convert("RGB")
        if self.mtcnn is not None:
            face = self.mtcnn(img)
            if face is not None:
                arr = face.permute(1, 2, 0).clamp(0, 255).byte().cpu().numpy()
                return Image.fromarray(arr)
        w, h = img.size
        s = min(w, h)
        l, t = (w - s) // 2, (h - s) // 2
        return img.crop((l, t, l + s, t + s)).resize((160, 160), Image.BILINEAR)

    @torch.no_grad()
    def embed_crops(self, crops, batch_size=64) -> np.ndarray:
        """L2-normalised 512-d embeddings, shape (N, 512)."""
        out = []
        for i in range(0, len(crops), batch_size):
            batch = np.stack(
                [np.asarray(c.convert("RGB").resize((160, 160))) for c in crops[i:i + batch_size]]
            )
            x = torch.from_numpy(batch).permute(0, 3, 1, 2).float()
            x = (x - 127.5) / 128.0  # facenet standardisation
            e = torch.nn.functional.normalize(self.model(x.to(self.device)), dim=1)
            out.append(e.cpu().numpy())
        return np.concatenate(out) if out else np.zeros((0, 512), dtype=np.float32)

    def embed(self, img: Image.Image) -> np.ndarray:
        return self.embed_crops([self.crop(img)])[0]
