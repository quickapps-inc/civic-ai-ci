# Provenance des données — CIVIC-AI CI (CIVIC-DATA-001)

Date de vérification du seed : **2026-09-25**.

## 1. Principe UNKNOWN > FAUX

- Toute information non fournie dans la mission reste `null`, `[]`,
  non vérifiée ou explicitement inconnue.
- Aucune recherche Internet autonome, aucun complément par connaissance
  générale, aucune donnée devinée.
- Une valeur inconnue est affichée honnêtement dans l'interface :
  « Information non disponible / non vérifiée », jamais remplacée
  par une supposition.
- Exemples appliqués : délai CNI non encodé en nombre fixe (dépend du lieu
  et de la période), liste exhaustive des pièces du passeport non encodée,
  coûts/délais des variantes CNI renouvellement et duplicata laissés `null`,
  délai de l'extrait égaré laissé `null` (« non déterminé »).

## 2. Statuts de vérification

| Statut technique | Libellé utilisateur | Signification |
|---|---|---|
| `VERIFIED` | Information vérifiée | Chaque information revendiquée est sourcée ; les champs inconnus restent explicitement `null`. |
| `PARTIALLY_VERIFIED` | Information partiellement vérifiée | Une partie seulement est vérifiée (ex. passeport sans liste exhaustive des pièces ; certificat dont la liste du cas général n'est pas universelle ; procédures CNI/extrait dont seule une partie des démarches est couverte). |
| `UNVERIFIED` | Information non encore vérifiée | Aucune donnée administrative vérifiée. |

- Le statut n'est jamais masqué (badge + ligne dédiée dans l'interface).
- Aucun score de confiance numérique arbitraire n'est calculé, à aucun niveau
  (ni procédure, ni variante).

## 3. Provenance des données

Chaque information administrative vérifiée conserve au minimum :

- nom/titre de la source (`title`) ;
- organisme/source institutionnelle (`organization`) ;
- URL (`url`) ;
- date de vérification (`verified_at` = `2026-09-25`).

Une procédure peut avoir plusieurs sources, et chaque variante porte ses
propres sources : le système permet donc de savoir quelles informations
proviennent de quelles sources (sources au niveau procédure ET au niveau
variante, affichées comme liens cliquables avec organisme et date).

### Sources intégrées (2026-09-25)

- **CNI** — ONECI :
  - https://www.oneci.ci/nos-produits/carte-identite/documents-a-fournir
  - https://timbre.oneci.ci/required-documents
  - https://timbre.oneci.ci/help
- **Passeport** — SNEDAI / monpasseport.ci :
  - https://snedai.com/passeport-en-cote-divoire/
  - https://www.monpasseport.ci/faq
- **Extrait de naissance (copie d'extrait égaré)** — Service Public :
  - https://servicepublic.gouv.ci/accueil/detaildemarcheparticulier/gupc/480/
- **Certificat de nationalité** — Service Public :
  - https://servicepublic.gouv.ci/accueil/detaildemarcheparticulier/1/573/
- **Casier judiciaire (Bulletin n°3)** — Service Public :
  - https://servicepublic.gouv.ci/accueil/detaildemarcheparticulier/1/81/61

## 4. Gestion des contradictions

- En cas de contradiction entre sources, aucune n'est privilégiée
  silencieusement : l'information reste `PARTIALLY_VERIFIED` ou `UNVERIFIED`
  le temps d'une clarification, et la contradiction est signalée dans `notes`.
- Les formulations prudentes de la mission sont conservées telles quelles :
  organismes du passeport « à présenter avec prudence », délai passeport
  conditionné à la validation par la Police de l'Air et des Frontières
  (jamais réduit à « 72 heures »), liste du certificat « non universelle »,
  distinctions ne pas fusionner (duplicata ≠ première demande) et ne pas
  confondre (extrait égaré ≠ déclaration/copie intégrale/rectification).

## 5. Nouvelle vérification requise

- Une source ne garantit pas éternellement l'exactitude : coûts, délais,
  pièces et autorités peuvent évoluer.
- Toute évolution administrative impose une nouvelle vérification datée
  (mise à jour de `verified_at` et des sources) ; en attendant, le statut
  doit être dégradé vers `PARTIALLY_VERIFIED` ou `UNVERIFIED` plutôt que
  de conserver un `VERIFIED` périmé.
- Test garde-fou : aucune procédure/variante non sourcée ne doit être
  promue `VERIFIED` (cf. `tests/test_civic_data_001.py`).
