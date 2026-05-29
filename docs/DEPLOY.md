# Déploiement

## Mode développement (Docker Compose)
```bash
cp .env.example .env
# renseigner OPENAI_API_KEY + un JWT_SECRET fort
docker compose up --build
```
- API : http://localhost:8000 (docs auto : http://localhost:8000/docs)
- Front : http://localhost:5173
- Postgres : localhost:5432

## Production

### Backend
Image construite via `backend/Dockerfile` (slim Python 3.11 + poppler-utils).
- Servir derrière un reverse proxy (nginx/Caddy) qui termine le TLS.
- `uvicorn` peut tourner avec `--workers 4` ; pour la vision, attention à la concurrence vs limite OpenAI.
- DB managée (RDS, Cloud SQL). Migrations : `alembic upgrade head` au déploiement.

### Front
- Build : `npm run build` produit `dist/` statique.
- Servir avec un CDN ou Caddy. La variable `VITE_API_URL` doit pointer sur le domaine API public.

### Variables d'environnement requises
| Variable | Description |
|----------|-------------|
| `JWT_SECRET` | Clé symétrique (≥ 64 caractères aléatoires). |
| `DATABASE_URL` | URL Postgres complète. |
| `OPENAI_API_KEY` | Clé API OpenAI. |
| `OPENAI_MODEL` | Modèle figé (ex. `gpt-4o`). |
| `STORAGE_BACKEND` | `local` ou `s3` (interface). |
| `STORAGE_LOCAL_ROOT` | Si local. |
| `MAX_UPLOAD_MB` | Limite d'upload. |

### Sauvegardes
- DB : snapshots quotidiens minimum.
- `audit_logs` : exporter vers stockage immuable.
- Copies étudiantes : sauvegarde chiffrée, rétention conforme à la politique de l'établissement.

### Observabilité
- Logs JSON via `app/core/logging.py` (filtre PII).
- Métriques applicatives : à brancher (Prometheus). Endpoints sensibles à monitorer :
  - latence `/rubric/extract` et `/copies/{id}/grade` (appels vision),
  - taux d'erreur 5xx,
  - taille de la file de revue (`needs_human_review`).

### Mise à l'échelle
- API : stateless, scaler horizontalement.
- Pipeline vision : possibles long calls (manuscrits longs). Mettre en queue (Celery + Redis) si > quelques secondes en synchrone.
- Postgres : indexes déjà posés sur les clés étrangères ; surveiller les requêtes du dashboard sur très grosses classes.
