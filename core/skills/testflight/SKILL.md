---
name: kata-testflight
description: Construire et soumettre l'app mobile Expo sur TestFlight via EAS, avec vérification Release sur simulateur avant tout build quand des modules natifs ont bougé. À lancer seulement sur demande explicite ("TestFlight", "build iOS", "/kata-testflight").
disable-model-invocation: true
allowed-tools: Bash(npx eas-cli *) Bash(git *)
---

# Livrer sur TestFlight

TestFlight est vu par le client. Un build qui crashe au lancement coûte plus qu'un build en retard.
Les profils viennent de `.claude/kata.policy.json` → `mobile` (et du `eas.json` qu'il désigne).

## La loi

```
TOUT AJOUT OU MISE À JOUR DE MODULE NATIF SE TESTE EN RELEASE SUR SIMULATEUR
AVANT LE BUILD EAS. UN TEST EN DEBUG NE COMPTE PAS.
```

Un décalage de versions entre modules natifs peut produire un crash au lancement **invisible en debug** (le binaire
debug résout ses symboles autrement). Seul un build Release lancé sur simulateur a valeur de preuve.

## 1. Choisir le profil

1. Des modules natifs ont-ils changé depuis le dernier build ? Comparer `package.json` / lockfile et `app.config`
   avec le dernier tag de build. Une mise à jour de dépendance peut tirer un module natif sans l'avoir demandé.
   Si oui : **vérification Release sur simulateur obligatoire** (étape 2) ; sinon passer à l'étape 3.
2. Profil : `mobile.testflight_profile`. S'il est `null` ou ambigu, **demander à l'utilisateur** lequel utiliser, ne
   pas trancher seul. Contrôler dans `eas.json` que le profil a `autoIncrement: true` (sinon : rejet « build number
   already used ») et qu'il n'est pas `distribution: internal` (un build ad hoc n'est pas une livraison TestFlight).

## 2. Vérification Release sur simulateur (si modules natifs touchés)

Construire en Release, installer sur un simulateur, lancer l'app, parcourir l'écran d'accueil et un parcours
touché. Prouver avec une capture. Sans cette étape, ne pas continuer.

## 3. Build puis soumission

```bash
npx eas-cli build --platform ios --profile <testflight_profile> --non-interactive
npx eas-cli submit --platform ios --latest --non-interactive   # le garde-fou demandera confirmation : voulu
```

## 4. Vérifier

1. Le build EAS est **finished**, pas seulement lancé.
2. Le traitement Apple est terminé (un build « en cours de traitement » n'est pas distribuable).
3. **Installer depuis TestFlight et lancer l'app** : seule preuve de l'absence de crash au démarrage.
4. Rédiger les notes « What to Test » : ce que le client doit regarder, une ligne par point, sans jargon.

## Rationalisations courantes

| Excuse | Réalité |
|---|---|
| « Ça tourne en debug sur mon simulateur » | Le crash n'apparaît qu'en Release. Debug ne prouve rien ici. |
| « Je n'ai touché qu'au JS » | Vérifie : une mise à jour de dépendance peut tirer un module natif. |
| « autoIncrement va gérer le numéro » | Selon le profil il n'y en a pas. Vérifie le profil, pas ton souvenir. |
| « Le build est parti, c'est livré » | Parti ≠ fini ≠ traité par Apple ≠ installable. Trois états à vérifier. |
| « Je testerai sur device après la démo » | La démo *est* le test, et c'est le client qui le fait. Installe avant. |
| « J'écris les notes plus tard » | Sans notes, le client teste au hasard et remonte des faux bugs. |

Pour les captures de fiche et l'audit ASO : skills `app-store-screenshots` et `aso` (voir `kata recommend`).
