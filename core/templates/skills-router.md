Kwa — routage des skills. Ces skills portent la méthode de travail du projet. Quand la demande correspond à une
ligne ci-dessous, invoque la skill avec l'outil Skill AVANT d'agir, y compris avant de poser des questions ou
d'explorer le code ; elle dit comment le faire. Une question simple ou une conversation : réponds directement, sans skill.

| Quand | Skill |
|---|---|
| Fonctionnalité ou changement non trivial, intention encore floue | /kwa-brainstorm |
| Mettre un plan ou une décision à l'épreuve, question par question | /kwa-interview |
| Question de conception à trancher par un essai jetable | /kwa-prototype |
| Décision à faire trancher par quelqu'un d'autre (client, tiers) | /kwa-questionnaire |
| Spec approuvée à transformer en tâches | /kwa-plan |
| Plan prêt à exécuter dans cette session | /kwa-execute |
| Plan long, tâches indépendantes, travail à déléguer à des sous-agents | /kwa-agents |
| Deux problèmes indépendants ou plus à traiter en même temps | /kwa-parallel |
| Sur le point d'écrire du code neuf : y a-t-il plus simple ? | /kwa-simple |
| Plan ou spec à découper en tickets GitHub | /kwa-tickets |
| Bug, test qui échoue, comportement inattendu | /kwa-debug |
| Écrire une fonctionnalité ou corriger un bug | /kwa-tdd |
| Sur le point de dire « c'est fait » ou « ça marche » | /kwa-verify |
| Demande qui modifie le produit (issue, branche dédiée, preuve, PR) | /kwa-start-dev |
| Relire un diff ou une branche | /kwa-review |
| Repérer sur-ingénierie et dette dans un dépôt | /kwa-audit |
| Repérer où approfondir les modules d'un dépôt | /kwa-architecture |
| Retour de revue reçu à traiter | /kwa-review-feedback |
| Committer | /kwa-commit |
| Publier la branche, ouvrir la PR | /kwa-ship |
| Déployer un environnement | /kwa-deploy |
| Build ou soumission TestFlight | /kwa-testflight |
| Fin de session substantielle, piège coûteux à retenir | /kwa-learn |
| Passer le relais à un autre agent ou à une autre session | /kwa-handoff |
| Écrire ou modifier un AGENTS.md, une règle ou une skill | /kwa-agent-docs |
| « Je n'ai pas compris » : reformuler le dernier message | /kwa-rephrase |
| Texte à relire pour en retirer le ton « écrit par une IA » (doc, README, PR, message) | /kwa-humanize |
| Fusion ou rebase arrêté sur des conflits | /kwa-conflicts |
| Fait extérieur à vérifier dans les sources (API, version, option, spécification) | /kwa-research |
| Termes métier flous ou contradictoires, glossaire ou décision durable à écrire | /kwa-domain |
| L'utilisateur veut apprendre un sujet sur plusieurs séances | /kwa-teach |

Ordre : la méthode d'abord (cadrer, déboguer), l'implémentation ensuite. Les consignes de l'utilisateur et d'AGENTS.md
priment toujours sur une skill.
