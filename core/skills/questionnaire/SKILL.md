---
name: kwa-questionnaire
description: Transformer une décision qu'on ne peut pas trancher seul en questionnaire pour quelqu'un d'autre. À utiliser quand une réponse dépend du client ou d'un tiers (périmètre, données, droits d'accès, contraintes, intégrations), quand l'utilisateur dit « il faut que je demande au client », « prépare des questions pour... », « /kwa-questionnaire ».
allowed-tools: Read Grep Glob Write
---

# Questionnaire pour un tiers

Le destinataire détient une information que l'utilisateur n'a pas. Le document sert à la lui extraire en un seul
passage, avec le moins d'effort possible de sa part. **L'agent ne l'envoie jamais** : il livre un Markdown prêt à
envoyer, l'envoi reste à l'humain.

## 1. Interroger l'envoi, pas le sujet

L'utilisateur sait toujours répondre à deux choses, à poser en un seul message :

- **À qui** : rôle, niveau technique, relation avec lui. Cela fixe le ton et la quantité de contexte.
- **Ce qu'il faut en retour** : les décisions ou faits précis qui bloquent aujourd'hui.

Le reste, chercher soi-même : lire le code, la spec, les issues, l'historique avant de poser une question qui
y trouve réponse. Ne jamais redemander au tiers ce que le dépôt dit déjà.

## 2. Écrire les questions

- **Fermées d'abord.** Oui/non, choix unique, choix multiple, nombre. Une question ouverte seulement quand les
  options ne peuvent pas être listées.
- **Options chiffrées.** Proposer des valeurs concrètes (« 50, 500, 5 000 utilisateurs ? », « A : importer
  l'existant ; B : repartir de zéro ») plutôt qu'un « combien ? » nu.
- **Une idée par question.** Jamais de question double.
- **Contexte minimal.** Une phrase de « pourquoi on demande » quand la question peut être mal lue. Pas de jargon
  que le destinataire ne partage pas.
- **Ce que ça débloque.** Pour chaque question ou groupe : la décision qui dépend de la réponse. Le destinataire
  répond mieux quand il voit l'enjeu.
- **Valeur par défaut.** Quand l'équipe a une hypothèse, la donner : « Sans réponse, nous partons sur A. »
- **Ordre** : le plus bloquant d'abord, car on n'obtient souvent qu'un seul passage. Regrouper par thème.

## 3. Gabarit

Écrire dans `questionnaire-<sujet>.md` dans le dossier de travail (ou un dossier hors dépôt si le contenu ne doit
pas y entrer), puis donner le chemin.

```markdown
# <Titre : le sujet en quelques mots>

**Objet** : pourquoi ce questionnaire et quelle décision il permet.
**Réponse souhaitée avant le** : AAAA-MM-JJ · **Durée estimée** : N minutes

## Contexte
Un paragraphe pour quelqu'un qui n'était pas dans la conversation.

## Comment répondre
Cocher ou compléter sous chaque question. « Je ne sais pas » est une réponse utile : l'indiquer plutôt que
laisser vide.

## <Thème>
### 1. <Question>
_Pourquoi nous la posons : ..._
- [ ] Option A
- [ ] Option B
- [ ] Autre : ...
_Débloque : <la décision ou la tâche concernée>_

## Autre chose à nous dire ?
Tout ce que nous n'avons pas demandé et qu'il faudrait savoir.
```

## 4. Garde-fous

- **Aucune donnée interne** : pas de nom d'équipier, d'hypothèse tarifaire, de lien privé, d'extrait de code non
  destiné au client. Du fonctionnel.
- **Aucun secret** demandé par écrit : pour un accès, demander « qui peut nous le fournir et par quel canal »,
  jamais la valeur dans le document.
- **Relire comme le destinataire** : chaque question se comprend-elle sans nous ? Si non, ajouter du contexte
  ou la retirer.

## Fin

Livrer : chemin du fichier, nombre de questions, quelles sont les trois qui bloquent le plus. Rappeler que l'envoi
est à faire par l'humain. Une fois les réponses reçues : `/kwa-brainstorm` ou `/kwa-plan` pour continuer,
`/kwa-learn` pour capitaliser les décisions de périmètre.

> Inspiré des skills de Matt Pocock (mattpocock/skills, MIT, commit f3fc563) ; réécrit pour Kwa.
