import os
import sys
from pathlib import Path

# Ajoute backend/ au sys.path pour que `import app.*` fonctionne.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Évite la dépendance à une vraie DB pour les tests unitaires du moteur de notation
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://test:test@localhost:5432/test"
)
