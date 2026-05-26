from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_CURATED_DIR = PROJECT_ROOT / "data" / "curated"

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
KNOWLEDGE_DIR = ARTIFACTS_DIR / "knowledge"

# Local default ChromaDB persistence directory
CHROMA_LOCAL_DIR = KNOWLEDGE_DIR / "chroma_db"

for path in [
    DATA_RAW_DIR,
    DATA_PROCESSED_DIR,
    DATA_CURATED_DIR,
    ARTIFACTS_DIR,
    MODELS_DIR,
    KNOWLEDGE_DIR,
    CHROMA_LOCAL_DIR,
]:
    path.mkdir(parents=True, exist_ok=True)