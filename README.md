# Exam Grader — AI-Assisted Exam Correction Platform

Plateforme d'aide à la correction d'examens pour universités. Le professeur dépose le corrigé et les copies, le système propose une note justifiée par question avec un niveau de confiance, et le professeur valide ou modifie. Chaque décision est tracée.

## Principe non négociable
Le professeur reste décideur final. Le système ne valide jamais une note en silence. Toute notation est accompagnée d'une justification et d'un niveau de confiance ; en dessous d'un seuil, la note part en file de revue humaine.

## Stack
- **Backend** : Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL 16
- **Moteur IA** : OpenAI GPT-4o (vision + raisonnement) via `OPENAI_API_KEY`
- **Documents** : `pypdf`, `pdf2image`, `Pillow` (rendu PDF→images à 300 DPI)
- **Frontend** : React 18 + TypeScript + Vite + Tailwind CSS
- **Stockage** : abstraction `StorageBackend` (local par défaut, interface S3-ready)
- **Auth** : JWT, rôles `admin` / `professeur` / `assistant`
- **Tests** : pytest (back), vitest (front)

## Démarrage rapide

### 1. Pré-requis
- Docker + Docker Compose
- `poppler-utils` installé dans l'image backend (pour `pdf2image`)
- Une clé API OpenAI

### 2. Configuration
```bash
cp .env.example .env
# Édite .env et renseigne OPENAI_API_KEY + JWT_SECRET
```

### 3. Lancement
```bash
docker compose up --build
```

Services disponibles :
- API : http://localhost:8000 (docs : http://localhost:8000/docs)
- Frontend : http://localhost:5173
- Postgres : localhost:5432 (DB `examgrader`, user `examgrader`)

### 4. Premier compte
À la première migration, un utilisateur admin est créé (voir logs API) :
- email : `admin@local`
- mot de passe : généré et affiché en console une seule fois

## Architecture
```
exam-grader/
├── backend/
│   ├── app/
│   │   ├── api/          # Routes FastAPI
│   │   ├── core/         # Config, sécurité, dépendances
│   │   ├── models/       # SQLAlchemy
│   │   ├── schemas/      # Pydantic
│   │   ├── services/     # Logique métier
│   │   ├── storage/      # Abstraction fichiers (local / S3)
│   │   └── grading/      # Pipeline vision + scoring engine
│   ├── alembic/          # Migrations
│   └── tests/
├── frontend/
│   └── src/              # React + TS
├── data/uploads/         # Stockage local par défaut
└── docker-compose.yml
```

## Phases de livraison
Voir `docs/PHASES.md` pour le détail des étapes et comment tester chacune.

## Sécurité & conformité
- `OPENAI_API_KEY` et `JWT_SECRET` sont en variables d'environnement, jamais commités
- Pas de PII dans les logs applicatifs (voir `app/core/logging.py`)
- Suppression / anonymisation des copies disponible via endpoint admin
- Chiffrement au repos : à brancher au niveau du `StorageBackend` (voir `storage/local.py`)
- Audit log immuable de toute décision de notation
