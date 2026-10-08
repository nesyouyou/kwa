---
name: kwa-deploy
description: Pré-vol, déploiement et vérification avec preuve d'un environnement (recette, production…), pilotés par `environments` dans .claude/kwa.policy.json. À lancer seulement sur demande explicite de déployer ("déploie", "mets en prod", "/kwa-deploy").
disable-model-invocation: true
allowed-tools: Bash(gh *) Bash(git *) Bash(curl *)
---

# Déployer un environnement

Lire `.claude/kwa.policy.json` → `environments.<nom>`. Si l'environnement demandé n'y figure pas, **s'arrêter** et
proposer de le décrire d'abord (voir « Format » en bas) : ne pas improviser un déploiement.

## La loi

```
UN DÉPLOIEMENT NON VÉRIFIÉ N'EST PAS UN DÉPLOIEMENT.
AUCUN DÉPLOIEMENT D'UN ENVIRONNEMENT À RISQUE SANS SON PRÉ-VOL COCHÉ, POINT PAR POINT, AVEC PREUVE.
```

Un workflow vert dit que *quelque chose* répond, pas que **ta** révision est servie ni que le parcours touché marche.

## 1. Cadrer

- Quel environnement, quelle révision (`git rev-parse --short HEAD`, ou le tag) ? Si `trigger` vaut
  `auto_on_merge`, « déployer » = **fusionner, puis surveiller et vérifier** : rien à lancer à la main (sauf lot
  qui ne déclenche pas le workflow, ex. doc seule : dans ce cas dire qu'il n'y a **pas eu** de déploiement).
- La PR du lot est-elle fusionnable (CI verte : `gh pr checks <n>`) ? Le lot est-il déjà passé dans l'environnement
  précédent (`requires`) ? Sinon : stop.

## 2. Pré-vol

Dérouler `preflight` **dans l'ordre**, un point à la fois. Pour chaque point : exécuter sa vérification (`how`),
citer la sortie, conclure OK / bloquant. Un point que tu ne peux pas vérifier est un point **non coché** : le dire,
ne pas le présumer. Un seul point bloquant = pas de déploiement ; l'expliquer et attendre l'utilisateur.

## 3. Déployer

- Confirmer à l'utilisateur ce qui part : environnement, révision, applications, risques relevés au pré-vol.
  **Attendre son accord explicite** (le garde-fou demandera aussi une validation : c'est voulu, ne pas le contourner).
- Lancer exactement le `deploy.command` de l'environnement (workflow `gh workflow run …`, ou fusion de PR).
  Si `deploy.confirm_phrase` existe, c'est la saisie qui sert de garde-fou : l'utilisateur la valide, pas toi.
- Surveiller : `gh run watch <id>` ; lire la sortie des jobs, pas seulement le vert global.

## 4. Vérifier (obligatoire, avec preuve)

Exécuter chaque commande de `verify` (`{health}` remplacé par l'URL de l'environnement), puis **le parcours réellement
touché par le lot**, avec une capture. En production : **lecture seule**, aucune écriture de test.
Rendre compte avec la sortie des commandes, pas avec « c'est déployé ».

## Rationalisations courantes

Celles de l'environnement (`rationalisations` dans la politique) s'appliquent en plus de celles-ci :

| Excuse | Réalité |
|---|---|
| « Le workflow est vert, c'est déployé » | Vert = le conteneur répond. Ouvre l'écran touché. |
| « Ça a marché ailleurs » | Autre volume, autres données, autres migrations. Le pré-vol est propre à l'environnement. |
| « Je contourne le pipeline, c'est plus rapide » | L'artefact ne correspond plus à un commit tracé. Le garde-fou demandera, et il a raison. |
| « Je vérifierai après » | Après, c'est déjà arrivé. Le pré-vol passe avant. |
| « Lot doc-only, rien à faire » | Alors il n'y a pas eu de déploiement. Ne l'annonce pas comme déployé. |

## Format de `environments` dans la politique

```json
"environments": {
  "recette": {
    "trigger": "auto_on_merge",
    "health": "https://recette.example.org",
    "preflight": [ { "id": "jobs", "check": "Un job long tourne-t-il ?", "how": "vérifier la file de jobs avant de fusionner" } ],
    "deploy": { "command": "gh pr merge <n> --squash --delete-branch" },
    "verify": ["curl -fsS {health}/health"]
  },
  "prod": {
    "trigger": "manual", "requires": "recette", "health": "https://app.example.org",
    "preflight": [ { "id": "recette", "check": "Le lot est-il passé en recette ?", "how": "oui/non, avec la date" } ],
    "deploy": { "command": "gh workflow run deploy.yml -f target=prod", "confirm_phrase": "deploy-prod" },
    "verify": ["curl -fsS {health}/health"],
    "rationalisations": [ { "excuse": "…", "reality": "…" } ]
  }
}
```
