# CIVIC-AI CI — MVP CIVIC-MVP-001 + seed vérifié CIVIC-DATA-001

Candidat au concours **SPRINT DIGITAL 2026** (Côte d'Ivoire),
rubrique **« Accès à l'information et orientation des usagers »**.

Le citoyen exprime un besoin administratif en langage naturel
(« J'ai perdu ma CNI », « Je veux faire un passeport », …).
Le système identifie la démarche correspondante et présente
une fiche administrative structurée **sans jamais inventer**
d'information officielle.

## Problème traité

L'accès à l'information administrative est fragmenté : le citoyen
ne sait pas toujours quelle démarche correspond à son besoin,
quels documents fournir, quel coût, quel délai, ni quelle autorité saisir.
Ce MVP construit le premier vertical fonctionnel :

```text
requête citoyenne → normalisation → détection déterministe
→ fiche locale → réponse structurée avec statut de vérification
```

Aucun LLM externe, aucune clé API, fonctionnement 100 % local.

## Principe fondamental : UNKNOWN > FAUX

- Une information métier absente ou non vérifiée reste explicitement
  `null`, `[]` ou `UNVERIFIED`.
- Aucun coût, délai, document, adresse, téléphone, URL, texte juridique
  ou autorité n'est fabriqué pour « remplir » les fiches.
- CIVIC-MVP-001 : les 5 fiches étaient volontairement `UNVERIFIED`.
- CIVIC-DATA-001 (seed vérifié le 2026-09-25) : seules les données
  fournies dans la mission sont intégrées, chacune avec sa provenance
  (titre, organisme, URL, `verified_at`). Tout le reste reste `null`/vide.
- Statuts possibles : `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`
  (affichés « Information vérifiée » / « partiellement vérifiée » /
  « non encore vérifiée », jamais masqués).
- Pas de score de confiance numérique arbitraire.
- Détail : voir `docs/DATA_PROVENANCE.md`.

## Architecture

```text
civic_ai_ci/
  app/
    main.py            # FastAPI : montage routes + statiques + page /
    api/routes.py      # GET /health, /api/procedures, POST /api/search (+ variante)
    core/normalize.py  # minuscules, sans accents, ponctuation aplanie
    core/intents.py    # moteur déterministe par sous-chaînes + variantes (sans LLM)
    schemas/models.py  # Pydantic : Source, ProcedureVariant, Procedure, Search*
    services/procedures.py  # chargement JSON locaux (cache lru)
  knowledge/
    procedures/*.json  # 5 fiches vérifiées versionnées (variantes + sources)
    intents/intents.json  # motifs de référence + signaux de variantes
  docs/DATA_PROVENANCE.md  # principe, statuts, provenance, contradictions
  static/css/style.css
  static/js/app.js     # fetch réel vers /api/search, rien en dur
  templates/index.html
  tests/test_mvp.py            # 14 tests d'origine (1 adapté, voir ci-dessous)
  tests/test_civic_data_001.py # 19 tests CIVIC-DATA-001
```

Modèle de connaissance (CIVIC-DATA-001, rétrocompatible) :
`Procedure { id, slug, name, summary, [requirements, cost, delay,
competent_authority génériques], notes, variants[], sources[],
verification_status, verified_at }`, chaque variante portant
`{ id, name, requirements, cost, delay, competent_authority, notes,
sources, verification_status, verified_at }`. Les sources sont des objets
`{ title, organization, url, verified_at }`.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Python 3.12+ requis.

## Lancement

```powershell
uvicorn app.main:app --reload
```

Puis ouvrir <http://127.0.0.1:8000> (interface) et
<http://127.0.0.1:8000/docs> (documentation API auto-générée).

## Tests

```powershell
pytest -v
```

Aucun appel réseau nécessaire : les tests utilisent `TestClient` en mémoire.

## Endpoints

| Méthode | Route | Description |
|---|---|---|
| GET | `/health` | `{"status": "ok", "service": "civic-ai-ci"}` |
| GET | `/api/procedures` | Liste des 5 fiches |
| GET | `/api/procedures/{slug}` | Fiche par slug, 404 si inconnue |
| POST | `/api/search` | `{"query": "..."}` → intention + fiche + vérification |
| GET | `/` | Page d'accueil (HTML/CSS/JS vanilla) |

Exemple :

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/search `
  -ContentType "application/json" -Body '{"query": "J''ai perdu ma CNI"}'
```

Réponse (abrégée, CIVIC-DATA-001) :

```json
{
  "query": "J'ai perdu ma CNI",
  "normalized_query": "j ai perdu ma cni",
  "intent": "cni",
  "match_status": "MATCHED",
  "procedure": { "slug": "cni", "verification_status": "PARTIALLY_VERIFIED", "...": "..." },
  "variant": { "id": "duplicata-perte", "verification_status": "VERIFIED", "...": "..." },
  "needs_clarification": false,
  "verification_status": "VERIFIED",
  "message": "Démarche identifiée : ... — variante : Duplicata / perte."
}
```

L'`intent` reste le slug de la procédure (compatibilité) ; la variante
est retournée séparément. Une demande CNI générique (« je veux une CNI »)
retourne `variant: null`, `needs_clarification: true`,
`match_status: "NEEDS_CLARIFICATION"` et demande une précision au lieu
de choisir arbitrairement. Une requête inconnue retourne
`intent: "UNKNOWN"`, `procedure: null`, sans hallucination.

## État actuel

- [x] MVP CIVIC-MVP-001 (moteur, API, page, 14 tests)
- [x] CIVIC-DATA-001 : modèle à variantes + seed vérifié le 2026-09-25 :
  CNI (première demande / renouvellement / duplicata-perte),
  extrait de naissance (copie d'extrait égaré), passeport
  (40 000 FCFA, délai conditionné PAF), certificat de nationalité
  (2 500 + 500 timbre, 24 h), casier Bulletin n°3 (2 500 FCFA, 24 h)
- [x] Moteur déterministe insensible casse/accents, UNKNOWN propre,
  variantes CNI/extrait, CNI générique → clarification (jamais arbitraire)
- [x] API minimale + validation Pydantic (query 1–500 caractères),
  endpoints existants inchangés + champs `variant` / `needs_clarification`
- [x] Page responsive branchée sur l'API réelle + exemples cliquables,
  statuts en français, sources cliquables, inconnus affichés honnêtement
- [x] 33 tests pytest (14 d'origine dont 1 adapté au seed vérifié
  — voir « Limites / adaptation » — + 19 CIVIC-DATA-001)
- [ ] Recherche floue / synonymes étendus, multi-intentions
- [ ] Persistance base de données, back-office de validation

## Limites / adaptation

- Le test `test_donnees_non_verifiees_ne_deviennent_pas_verified` datait du
  MVP (toutes fiches `UNVERIFIED`, champs nuls). Avec le seed vérifié, son
  corps a été adapté vers un invariant plus strict : aucune procédure /
  variante `VERIFIED` ou `PARTIALLY_VERIFIED` sans sources officielles
  (URL + `verified_at` 2026-09-25), aucun score numérique, aucun statut
  promu artificiellement. Nom conservé, justification dans
  `docs/DATA_PROVENANCE.md`. Aucun autre test supprimé ou affaibli.

## Limites connues

- Correspondance par sous-chaînes uniquement : fautes de frappe
  importantes ou périphrases éloignées → `UNKNOWN` (choix volontaire).
- « perdu ma carte » est rattaché à la CNI par spécification du MVP ;
  une désambiguïsation sera nécessaire si d'autres cartes sont ajoutées.
- « voyager » seul déclenche l'intention passeport (motif demandé).
- Pas d'authentification, pas de persistance, pas d'i18n au-delà du français.

## Prochaines étapes

1. Mission de collecte/validation des données officielles
   (coûts, délais, pièces, autorités, sources datées).
2. Workflow de vérification (`UNVERIFIED` → `PARTIALLY_VERIFIED` → `VERIFIED`).
3. Enrichissement prudent du moteur (synonymes validés, journal des UNKNOWN).
4. Durcissement : rate-limit, journalisation, pages d'erreur dédiées.

## Déploiement Contabo / Docker (CIVIC-DEPLOY-001A)

Architecture : un seul service `web` (FastAPI sur le port conteneur `8000`),
rattaché au réseau externe existant `proxy-net` (alias `civic-ai-ci-web`).
Aucun port hôte n'est publié : seul Caddy (ports 80/443) expose le trafic.

Build / démarrage (depuis la racine du VPS après `git clone` / `git pull`) :

```bash
docker compose -f deploy/contabo/compose.yaml up -d --build
```

Statut :

```bash
docker compose -f deploy/contabo/compose.yaml ps
```

Logs :

```bash
docker compose -f deploy/contabo/compose.yaml logs -f web
```

Vérification santé (depuis le VPS, via le réseau `proxy-net` ou le conteneur) :

```bash
docker exec $(docker compose -f deploy/contabo/compose.yaml ps -q web) python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=5).read().decode())"
# attendu : {"status": "ok", "service": "civic-ai-ci"}
```

Notes :
- Le port `8000` est interne au conteneur et ne doit pas être publié
  publiquement (`compose.yaml` ne publie aucun port hôte).
- La configuration Caddy (reverse proxy) et DNS est effectuée séparément,
  après validation du conteneur. Caddy joindra l'application via le DNS
  Docker `http://civic-ai-ci-web:8000`.
