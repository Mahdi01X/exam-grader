# Sécurité & conformité

## Secrets
- `OPENAI_API_KEY` et `JWT_SECRET` sont injectés par variables d'environnement, jamais commités.
- `.env` est dans `.gitignore`. En production, utiliser un gestionnaire de secrets (AWS Secrets Manager, GCP Secret Manager, Vault).
- Le mot de passe admin de bootstrap est généré aléatoirement et imprimé une seule fois sur stderr. **Il doit être changé immédiatement.**

## Authentification
- JWT signé HS256 (clé symétrique). Expiration : `JWT_EXPIRE_MINUTES` (8h par défaut).
- Trois rôles : `admin`, `professeur`, `assistant`. Pas de compte étudiant dans le MVP.
- Toutes les routes (sauf `/api/health` et `/api/auth/login`) exigent un token valide.

## RGPD / données étudiantes
- **Suppression** : `DELETE /api/exams/{exam_id}/copies/{copy_id}` supprime la copie et tous ses rendus disque + grades + audit lié.
- **Anonymisation** : le `student_identifier` est libre. Recommandation : utiliser un numéro anonyme (matricule) plutôt qu'un nom.
- **Rétention** : configurable (à brancher dans une tâche cron). Par défaut, rien n'est supprimé automatiquement — le prof décide.
- **Logs** : `app/core/logging.py` filtre les emails du log via regex. Auditer périodiquement.

## Chiffrement au repos
- Le `StorageBackend` est l'endroit où brancher du chiffrement. Pour le MVP, les fichiers sont écrits en clair sur disque.
- Recommandation prod :
  - Option A : chiffrer au niveau filesystem (LUKS, ZFS native encryption).
  - Option B : envelope encryption AES-GCM dans `LocalStorage.save` avec clé KMS.

## Chiffrement en transit
- TLS terminé devant l'API (nginx, Caddy, ALB). Pas de TLS gérée par l'app elle-même.
- HSTS recommandé.

## Audit trail
- `audit_logs` enregistre : `entity` + `entity_id` + `action` + `old_value` + `new_value` + `user_id` + `timestamp`.
- Toutes les actions sensibles passent par `app/services/audit.py:log_action`.
- Recommandation : copier `audit_logs` vers un stockage immuable (S3 Object Lock, append-only DB) en prod.

## Reproductibilité
- Température LLM forcée à 0 (`OPENAI_TEMPERATURE=0.0`).
- Modèle figé via `OPENAI_MODEL` (épingler une version précise en prod).
- Le scoring final est en Python pur à partir des `GradingPolicy` — pas de variance LLM dans le calcul des points.

## Limites connues / à venir
- Pas de rate limiting applicatif (à mettre devant un reverse proxy).
- Pas de 2FA (à ajouter si déploiement multi-tenant).
- Pas de revocation list pour les JWT (utiliser une expiration courte + refresh tokens en prod).
- Le download d'exports utilise le token dans le `localStorage` ; pour des liens partagés, prévoir des tokens signés à courte durée.
