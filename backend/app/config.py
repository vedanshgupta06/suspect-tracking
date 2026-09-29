import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./suspect_tracking.db")
FACE_ML_PATH = os.getenv("FACE_ML_PATH", "../face_ml")
FIR_ML_PATH = os.getenv("FIR_ML_PATH", "../fir_ml")
FIR_MODEL_PATH = os.getenv("FIR_MODEL_PATH", "../fir_ml/ft_sbert")
FACE_MATCH_THRESHOLD = float(os.getenv("FACE_MATCH_THRESHOLD", "0.60"))
FIR_LINK_THRESHOLD = float(os.getenv("FIR_LINK_THRESHOLD", "0.60"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "12"))
