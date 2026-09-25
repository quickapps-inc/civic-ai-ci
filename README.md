# CIVIC-AI CI — MVP CIVIC-MVP-001

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
- Les 5 fiches du MVP sont volontairement `UNVERIFIED` : elles servent
  à tester le moteur. La collecte/validation réelle fera l'objet
  d'une mission distincte.
- Statuts possibles : `VERIFIED`, `PARTIALLY_VERIFIED`, `UNVERIFIED`.
- Pas de score de confiance numérique arbitraire.

## Architecture

```text
civic_ai_ci/
  app/
    main.py            # FastAPI : montage routes + statiques + page /
    api/routes.py      # GET /health, /api/procedures, POST /api/search
    core/normalize.py  # minuscules, sans accents, ponctuation aplanie
    core/intents.py    # moteur déterministe par sous-chaînes (sans LLM)
    schemas/models.py  # Pydantic : Procedure, SearchRequest/Response
    services/procedures.py  # chargement JSON locaux (cache lru)
  knowledge/
    procedures/*.json  # 5 fiches UNVERIFIED versionnées
    intents/intents.json  # motifs de référence (doc du moteur)
  static/css/style.css
  static/js/app.js     # fetch réel vers /api/search, rien en dur
  templates/index.html
  tests/test_mvp.py
```

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

Réponse (abrégée) :

```json
{
  "query": "J'ai perdu ma CNI",
  "normalized_query": "j ai perdu ma cni",
  "intent": "cni",
  "match_status": "MATCHED",
  "procedure": { "slug": "cni", "verification_status": "UNVERIFIED", "...": "..." },
  "verification_status": "UNVERIFIED",
  "message": "Démarche identifiée : ..."
}
```

Une requête inconnue retourne `intent: "UNKNOWN"`, `procedure: null`,
sans hallucination.

## État actuel du MVP

- [x] 5 fiches locales `UNVERIFIED` (CNI, passeport, extrait de naissance,
  certificat de nationalité, casier judiciaire)
- [x] Moteur déterministe insensible casse/accents, UNKNOWN propre
- [x] API minimale + validation Pydantic (query 1–500 caractères)
- [x] Page responsive branchée sur l'API réelle + exemples cliquables
- [x] 14 tests pytest
- [ ] Données administratives réelles (mission de collecte distincte)
- [ ] Recherche floue / synonymes étendus, multi-intentions
- [ ] Persistance base de données, back-office de validation

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
