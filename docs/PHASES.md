# Phases de livraison

Chaque phase produit une démo lançable. À chaque étape, la commande de test est explicite.

## Phase 0 — Scaffold
**Livré :** structure backend (FastAPI + SQLAlchemy + Alembic), structure frontend (React + TS + Vite + Tailwind), `docker-compose.yml`, `.env.example`, README.

**Test :**
```bash
cp .env.example .env       # renseigner OPENAI_API_KEY et JWT_SECRET
docker compose up --build
```
- API health : `curl http://localhost:8000/api/health` → `{"status":"ok"}`
- Front : ouvrir `http://localhost:5173`, on doit voir l'écran de login.

---

## Phase 1 — Modèle de données + auth + CRUD
**Livré :**
- Tables : `users`, `exams`, `rubric_items`, `grading_policies`, `student_copies`, `question_grades`, `audit_logs`.
- Migrations Alembic.
- JWT auth, rôles `admin` / `professeur` / `assistant`.
- CRUD examens, items de barème, règles de notation (avec les 5 règles par défaut créées à la création d'un examen).
- Bootstrap : compte admin auto-créé si table vide, mot de passe imprimé une fois sur stderr (à changer immédiatement).

**Test :**
1. Récupérer le mot de passe admin imprimé par le conteneur `api` au premier démarrage : `docker compose logs api | grep "one-time password"`
2. Login depuis l'UI (`admin@local` + mot de passe). On atteint la liste vide.
3. Créer un examen → il apparaît avec statut `draft`.
4. Cliquer dessus → on voit barème vide + les 5 règles par défaut éditables.

---

## Phase 2 — Ingestion de documents
**Livré :**
- Upload PDF / PNG / JPG avec limite de taille (`MAX_UPLOAD_MB`).
- Conversion PDF → PNG à 300 DPI (`pdf2image` + `poppler-utils`).
- Stockage abstrait (`StorageBackend` ; impl locale, hook S3 prêt).
- Endpoint upload copie : `POST /api/exams/{id}/copies` (`student_identifier` + `file`).

**Test :**
1. Sur la page d'un examen, déposer une copie PDF avec un identifiant étudiant.
2. Vérifier dans `data/uploads/exam-{id}/copies/{ident}/pages/page-001.png` qu'on a bien des rendus.

---

## Phase 3 — Extraction du barème par vision
**Livré :**
- `POST /api/exams/{id}/rubric/extract` (upload du corrigé).
- Vision OpenAI appelée avec prompt système JSON strict, sortie parsée défensivement.
- L'UI affiche la proposition dans un éditeur, le prof valide via `PUT /api/exams/{id}/rubric/bulk`.
- L'examen passe en `rubric_pending` à l'extraction, `rubric_ready` à la validation.

**Test :**
1. Renseigner `OPENAI_API_KEY` dans `.env`.
2. Sur la page d'un examen, "Importer un corrigé".
3. Une proposition de barème apparaît dans le tableau (questions, réponses attendues, points).
4. Corriger ce qui doit l'être, cliquer "Enregistrer le barème".
5. Statut passe à `rubric_ready`.

---

## Phase 4 — Extraction de la copie + transcription
**Livré :**
- `POST /api/exams/{id}/copies/{copy_id}/grade` lance le pipeline.
- Pour chaque question du barème, la vision transcrit la réponse, suggère une règle, justifie, et retourne un niveau de confiance.
- Toute confiance < `CONFIDENCE_REVIEW_THRESHOLD` (défaut 0.80) marque la note `needs_human_review=True`.

**Test :**
1. Déposer une copie, cliquer "Noter".
2. Une fois la requête terminée, la copie a un statut `graded`.

---

## Phase 5 — Moteur de notation Python (MVP fonctionnel)
**Livré :**
- `app/grading/scorer.py` : le calcul final est en Python, jamais par le LLM.
- Si la règle suggérée par le LLM n'existe pas → fallback policy 0, revue forcée.
- Tous les choix sont audités dans `audit_logs`.

**Test (unit) :**
```bash
docker compose exec api pytest tests/
```
On doit voir `test_scorer.py`, `test_vision_parsing.py`, `test_rubric_parsing.py` au vert.

**Test (end-to-end MVP) :**
1. Créer un examen.
2. Importer un corrigé → valider le barème.
3. Déposer 1 copie.
4. Cliquer "Noter".
5. Cliquer "Réviser" → on voit la copie à gauche, les questions à droite, chacune avec note proposée + justification + confiance.

---

## Phase 6 — Revue humaine
**Livré :**
- Écran côte à côte : image de page (paginée) | liste des questions avec :
  - transcription extraite,
  - règle appliquée (modifiable),
  - note proposée (modifiable),
  - justification (modifiable),
  - confiance,
  - badge "À réviser" si confiance basse.
- `POST .../grades/{id}/override` valide la note et journalise.
- `POST .../copies/{id}/finalize` ferme la copie : les questions non touchées sont auto-validées à la note proposée.

**Test :**
1. Sur une copie notée, modifier la règle d'une question → la note est recalculée côté UI (la modif réelle est gardée à l'envoi).
2. Valider → ligne devient "Validée".
3. Cliquer "Finaliser" → statut copie passe à `reviewed`.
4. Tout l'historique est dans `audit_logs`.

---

## Phase 7 — Exports + tableau de bord
**Livré :**
- `GET /api/exams/{id}/export/class.xlsx` : tableau des notes (une ligne par étudiant, une colonne par question, total).
- `GET /api/exams/{id}/export/copy/{copy_id}.pdf` : PDF par copie (table notes + justifications + transcriptions).
- `GET /api/exams/{id}/export/dashboard` : JSON dashboard (moyenne, médiane, distribution, count en revue).

**Test :**
1. Cliquer "Tableur classe" sur la page examen → un .xlsx est téléchargé.
2. Cliquer "Export PDF" sur la page revue → un PDF est téléchargé.
3. `curl -H "Authorization: Bearer …" .../export/dashboard` retourne le JSON.

---

## Phase 8 — Tests, sécurité, déploiement
**Livré :**
- Tests unitaires pour le scorer, le parsing JSON, le parsing du barème.
- Voir `docs/SECURITY.md` pour : RGPD, chiffrement, secrets, PII dans les logs.
- Voir `docs/DEPLOY.md` pour le déploiement de production.

**Test :**
```bash
docker compose exec api pytest
docker compose exec frontend npm run test
```
