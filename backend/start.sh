#!/usr/bin/env sh
# Démarrage du conteneur API : migrations -> bootstrap admin -> serveur.
# Utilisé par le CMD du Dockerfile (et donc par Render, sans dockerCommand).
set -e

echo "[start] alembic upgrade head"
alembic upgrade head

echo "[start] bootstrap admin"
python -m app.bootstrap

echo "[start] launching uvicorn on port ${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
