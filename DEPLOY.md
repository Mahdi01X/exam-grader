# Déploiement — Render (cloud permanent)

Ce guide déploie ExamGrader sur **Render** avec le blueprint [`render.yaml`](./render.yaml) :
**PostgreSQL managé + API (Docker, poppler inclus) + Frontend (static Vite)**, région **Frankfurt (UE)** pour la résidence des données.

> Je ne peux pas créer de compte ni saisir de moyen de paiement à ta place : les étapes
> qui touchent à *ton* compte Render/GitHub sont à faire par toi (elles sont signalées 👤).

---

## Pré-requis
- 👤 Un compte **GitHub** (gratuit)
- 👤 Un compte **Render** (gratuit) — connexion via GitHub recommandée
- 👤 Une **clé API Anthropic** (`console.anthropic.com` → API Keys)

---

## Étape 1 — Pousser le code sur GitHub 👤

Le blueprint attend que le dossier **`exam-grader/` soit la racine du dépôt** (les chemins
`backend/Dockerfile`, `rootDir: frontend`, etc. sont relatifs à cette racine).

Depuis `exam-grader/` :
```bash
cd exam-grader
git init
git add .
git commit -m "ExamGrader — initial"
# crée un dépôt vide sur GitHub puis :
git remote add origin https://github.com/<toi>/exam-grader.git
git branch -M main
git push -u origin main
```
Le `.gitignore` exclut déjà `.env`, la base SQLite locale, `node_modules`, `data_local/`, etc.
> Vérifie qu'aucun fichier `.env` n'est poussé (`git status` ne doit pas le lister).

---

## Étape 2 — Créer le Blueprint sur Render 👤
1. Render → **New** → **Blueprint**
2. Connecte ton dépôt GitHub `exam-grader`
3. Render détecte `render.yaml` et liste **3 ressources** : `examgrader-db`, `examgrader-api`, `examgrader-web`
4. Il te demande les variables marquées `sync: false` — renseigne-les :
   | Variable | Valeur |
   |---|---|
   | `ANTHROPIC_API_KEY` | ta clé `sk-ant-...` |
   | `BOOTSTRAP_ADMIN_EMAIL` | ton email admin (ex. `prof@univ.fr`) |
   | `BOOTSTRAP_ADMIN_PASSWORD` | un mot de passe initial fort |
5. **Apply** → Render provisionne la base, build l'image Docker de l'API (avec poppler) et build le frontend.

`JWT_SECRET` est généré automatiquement. `DATABASE_URL` est injectée depuis la base.

---

## Étape 3 — Vérifier les URLs et le câblage ⚠️
Une fois les services créés, note leurs URLs publiques (dashboard Render) :
- API : `https://examgrader-api.onrender.com`
- Web : `https://examgrader-web.onrender.com`

Si Render a ajouté un suffixe (collision de nom), **mets à jour** :
- service **examgrader-web** → `VITE_API_URL` = l'URL réelle de l'API → **Redeploy**
- service **examgrader-api** → `CORS_ORIGINS` = l'URL réelle du web (ou `*`) → **Redeploy**

`VITE_API_URL` est lue **au build** du frontend : après l'avoir changée, relance un déploiement du service web.

---

## Étape 4 — Se connecter
Ouvre l'URL du frontend → connecte-toi avec `BOOTSTRAP_ADMIN_EMAIL` / `BOOTSTRAP_ADMIN_PASSWORD`.
Crée ensuite tes comptes professeur/assistant depuis l'API (`POST /api/auth/users`, réservé admin).

---

## Limites du palier gratuit (à connaître)
- **Mise en veille** : les services free s'endorment après ~15 min d'inactivité (réveil ~30–60 s au 1er appel).
- **Stockage éphémère** : pas de disque persistant en free → les fichiers de copies (`/data/uploads`) sont
  **perdus à chaque redéploiement/réveil**. Les notes/audit restent en base (Postgres). Pour la persistance
  des fichiers en production : ajouter un **disque payant** monté sur `/data/uploads`, ou brancher **S3**
  (l'abstraction `StorageBackend` est prête — voir `app/storage/`).
- **Postgres free** : expire après ~90 jours ; passer à un plan payant pour la prod.

## Modèle IA
`ANTHROPIC_MODEL` (défaut `claude-opus-4-7`) doit correspondre à un **modèle vision** que ton compte
supporte. Ajuste-le dans le service `examgrader-api` si besoin, puis redéploie.

## Conformité (RGPD)
- Région **Frankfurt (UE)**.
- Suppression d'une copie + ses fichiers : `DELETE /api/exams/{id}/copies/{copyId}`.
- Pas de PII dans les logs applicatifs (filtre `app/core/logging.py`).
- Chiffrement au repos : à activer au niveau du disque/bucket (point d'ancrage dans `app/storage/`).

---

## Alternative — un seul service
Si tu préfères **une seule URL** (frontend servi par l'API, sans CORS), on peut passer à un
Dockerfile multi-stage (build Vite + service FastAPI static). Dis-le-moi et je l'ajoute.
