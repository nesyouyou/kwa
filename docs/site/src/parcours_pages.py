"""Les trois parcours et leur page d'accueil.

Contenu écrit à la main à partir des documentations officielles (liens en bas de chaque parcours). Les exemples de
configuration sont validés au build : JSON valide, aucun secret en clair, en-têtes de skill et d'agent complets.
"""
from __future__ import annotations

import json
import re
import sys

import hl
from parcours import code, cmd, esc, pill, reveal, stage

CULTURE_NAV = [("1", "Le modèle"), ("2", "Les jetons"), ("3", "Les hallucinations"), ("4", "Le contexte"), ("5", "Le prompt"), ("6", "L'agent"), ("7", "Risques")]
CONTEXTE_NAV = [("1", "Le contexte"), ("2", "La session"), ("3", "AGENTS.md"), ("4", "Règles"), ("5", "Skills"), ("6", "Agents"), ("7", "MCP"), ("8", "Context7 et Playwright"), ("9", "Permissions"), ("10", "Choisir")]
HARNESS_NAV = [("0", "L'histoire"), ("1", "Instructions"), ("2", "Un garde"), ("3", "Branchement"), ("4", "Événements"), ("5", "Politique"), ("6", "Une skill"), ("7", "Mémoire"), ("8", "Workflow"), ("9", "Le flux"), ("10", "Limites")]
TOC = {  # barre latérale : (ancre, libellé) sous la page courante
    "parcours-culture.html": [(f"etape-{n}", f"{n} · {t}") for n, t in CULTURE_NAV],
    "parcours-contexte.html": [(f"etape-{n}", f"{n} · {t}") for n, t in CONTEXTE_NAV],
    "parcours-harness.html": [(f"etape-{n}", f"{n} · {t}" if n != "0" else t) for n, t in HARNESS_NAV],
}

DOC = "https://code.claude.com/docs/en/"
API = "https://platform.claude.com/docs/en/"


def link(url: str, label: str) -> str:
    return f'<a href="{url}">{esc(label)}</a>'


def sources(items: list[tuple[str, str]]) -> str:
    li = "".join(f"<li>{link(u, t)}</li>" for u, t in items)
    return (f'<div class="pc-check"><h2>Sources</h2><p class="kd-note" style="margin:0 0 12px">Les documentations officielles font foi. '
            f'Les noms de réglages et les limites évoluent avec les versions : vérifiez avant une séance.</p><ul>{li}</ul></div>')


def checklist(title: str, items: list[str]) -> str:
    return f'<div class="pc-check"><h2>{esc(title)}</h2><ul>' + "".join(f"<li>{i}</li>" for i in items) + "</ul></div>"


def nav(items: list[tuple[str, str]]) -> str:
    return '<ol class="pc-nav">' + "".join(f'<li style="list-style:none"><a href="#etape-{n}">{n} · {esc(t)}</a></li>' for n, t in items) + "</ol>"


def intro(text: str) -> str:
    return f'<p class="pc-intro">{text}</p>'


def pair(bad_title: str, bad: str, good_title: str, good: str) -> str:
    return ('<div class="pc-proof" style="margin:0 0 16px">'
            f'<div><b>{esc(bad_title)}</b><pre class="kd-code" style="margin-top:10px;white-space:pre-wrap">{hl.highlight(bad)}</pre></div>'
            f'<div><b>{esc(good_title)}</b><pre class="kd-code" style="margin-top:10px;white-space:pre-wrap">{hl.highlight(good)}</pre></div></div>')


# ---------------------------------------------------------------------------------------------------------------------
# Parcours 1 : culture IA générative
# ---------------------------------------------------------------------------------------------------------------------

LOOP = """<div class="pc-widget po" id="loop">
<div class="pc-actions"><button type="button" class="kd-copy" data-loop-play>Dérouler l'exemple</button><button type="button" class="kd-copy" data-loop-next>Étape suivante</button></div>
<div class="lp-ring" aria-hidden="true"><span data-n="0">1 · Réfléchir</span><span data-n="1">2 · Appeler un outil</span><span data-n="2">3 · Lire le résultat</span><span data-n="3">4 · Terminé ?</span></div>
<p class="po-cap" id="loop-cap" aria-live="polite">Exemple : « corrige le test qui échoue ». Lancez la scène.</p>
<p class="pc-hint">Scénario simplifié : un vrai agent enchaîne souvent plus de tours.</p></div>"""

ORCH = """<div class="pc-widget po" id="orch">
<div class="pc-actions"><button type="button" class="kd-copy" data-orch="team">Avec sous-agents</button>
<button type="button" class="kd-copy" data-orch="solo">Sans sous-agents</button>
<button type="button" class="kd-copy" data-orch-next>Étape suivante</button></div>
<div class="po-main"><div class="po-t">Agent principal (l'orchestrateur)</div>
<div class="pc-stack" id="po-main"><i id="pm-sys"></i><i id="pm-hist"></i><i id="pm-files"></i><i id="pm-sum"></i></div>
<div class="po-v" id="po-v">Fenêtre principale : 0 %</div></div>
<div class="po-subs">
<div class="po-col"><div class="po-lane"><span class="po-pkt po-down">brief</span><span class="po-pkt po-up">résumé</span></div><div class="po-sub"><div class="po-t">Sous-agent A <small>les routes</small></div><div class="pc-stack"><i class="ps"></i></div></div></div>
<div class="po-col"><div class="po-lane"><span class="po-pkt po-down">brief</span><span class="po-pkt po-up">résumé</span></div><div class="po-sub"><div class="po-t">Sous-agent B <small>les tests</small></div><div class="pc-stack"><i class="ps"></i></div></div></div>
<div class="po-col"><div class="po-lane"><span class="po-pkt po-down">brief</span><span class="po-pkt po-up">résumé</span></div><div class="po-sub"><div class="po-t">Sous-agent C <small>la doc</small></div><div class="pc-stack"><i class="ps"></i></div></div></div>
</div>
<p class="po-cap" id="po-cap" aria-live="polite">Choisissez un mode pour lancer la scène.</p>
<p class="pc-hint">Pourcentages illustratifs : ils montrent la logique, pas des mesures.</p></div>"""

SKL = """<div class="pc-widget po" id="skl">
<div class="pc-actions"><button type="button" class="kd-copy" data-skl="0" aria-pressed="true">Au démarrage</button>
<button type="button" class="kd-copy" data-skl="1" aria-pressed="false">L'agent appelle la skill</button>
<button type="button" class="kd-copy" data-skl="2" aria-pressed="false">Il lit une annexe</button></div>
<div class="pc-stack" id="sk-bar"><i id="sk-desc"></i><i id="sk-body"></i><i id="sk-ann"></i></div>
<ul class="pc-legend"><li><i class="pc-k0"></i>Descriptions des skills (toujours là)</li><li><i class="pc-k1"></i>Corps de la skill appelée</li><li><i class="pc-k4"></i>Fichier annexe</li></ul>
<p class="po-cap" id="sk-cap" aria-live="polite"></p>
<p class="pc-hint">Largeurs agrandies pour être lisibles : une skill pèse peu devant la fenêtre.</p></div>"""

def culture() -> str:
    gauge = """<div class="pc-widget" id="ctx-gauge">
<div class="pc-stack pc-stack--big" id="ctx-stack" role="img" aria-label="Fenêtre de contexte qui se remplit au fil d'une session d'agent, puis se compacte"><i id="seg-sys"></i><i id="seg-rules"></i><i id="seg-tools"></i><i id="seg-hist"></i><i id="seg-files"></i><i id="seg-res"></i><i id="seg-sum"></i></div>
<ul class="pc-legend"><li><i class="pc-k0"></i>Consignes</li><li><i class="pc-k1"></i>Instructions</li><li><i class="pc-k2"></i>Outils</li><li><i class="pc-k3"></i>Historique</li><li><i class="pc-k4"></i>Fichiers lus</li><li><i class="pc-k5"></i>Résultats</li><li><i class="pc-k6"></i>Résumé</li></ul>
<p id="ctx-txt" class="pc-big"></p><p id="ctx-msg" aria-live="polite"></p>
<p class="pc-hint">Animation illustrative sur une fenêtre de 200 000 jetons : les quantités sont des exemples, pas des mesures.</p></div>"""
    tok = """<div class="pc-widget" id="tk">
<div class="pc-presets"><span>Choisir une phrase</span>
<button type="button" class="kd-copy" data-tk-s="0" aria-pressed="true">La capitale…</button>
<button type="button" class="kd-copy" data-tk-s="1" aria-pressed="false">Il était une fois…</button>
<button type="button" class="kd-copy" data-tk-s="2" aria-pressed="false">Pour limiter…</button></div>
<p class="pc-step"><b>1</b> Le texte est découpé en jetons, chacun repéré par un numéro.</p>
<div id="tk-chips" class="pc-chips tk-chips" aria-live="polite"></div>
<p class="pc-step"><b>2</b> Le modèle calcule une probabilité pour chacun des jetons possibles à la suite.</p>
<div id="tk-probs" class="tk-probs"></div>
<div class="tk-ctl"><label for="tk-temp">Température <b id="tk-tv">1,0</b></label><input id="tk-temp" type="range" min="0.2" max="2" step="0.1" value="1">
<button type="button" class="kd-copy" id="tk-draw">Tirer 20 fois</button></div>
<p class="pc-step"><b>3</b> Un jeton est tiré au sort selon ces probabilités, puis le calcul recommence avec lui en plus.</p>
<div id="tk-draws" class="tk-draws"></div>
<p class="pc-hint">Chiffres inventés pour illustrer : un vrai modèle calcule sur des dizaines de milliers de jetons possibles, et découpe autrement. La formule est réelle : probabilité = softmax(score ÷ température).</p></div>
<div class="pc-widget"><label class="pc-lbl" for="tok-input">Estimer vos propres textes (ils restent dans votre navigateur)</label>
<textarea id="tok-input" rows="4" placeholder="Un paragraphe d'un rapport, un e-mail, une page de documentation..."></textarea>
<div id="tok-chips" class="pc-chips" aria-hidden="true"></div>
<div id="tok-out" class="pc-out"></div></div>"""
    s = [
        ("1", "Ce qu'est un modèle de langage", "Un outil qui prolonge un texte, pas une base de connaissances.",
         """<p>Un modèle de langage a lu une très grande quantité de textes et calcule, mot après mot, la suite la plus plausible de ce qu'on lui donne. Il ne consulte pas une base de faits : il produit du texte vraisemblable. De là viennent ses deux forces (rédiger, reformuler, transformer) et ses deux faiblesses (inventer, ignorer ce qui s'est passé après son entraînement).</p>
<p><strong>À essayer</strong> avec l'outil de votre choix : posez trois fois exactement la même question ouverte (par exemple « propose-moi un plan pour présenter notre offre »). Comparez les trois réponses.</p>
""" + reveal("Ce qu'on observe", "<p>Les réponses diffèrent : le modèle tire sa suite parmi plusieurs possibles, il ne rejoue pas une réponse stockée. Pour une tâche qui doit être identique à chaque fois (un calcul, un contrôle), on ne s'en remet pas au texte du modèle : on utilise un programme, et le modèle ne fait que lire ou rédiger.</p>"),
         "Expliquer en deux phrases pourquoi deux réponses à la même question peuvent différer.",
         "« Il sait » ou « il a cherché » : le modèle ne cherche pas, il produit. Les outils de recherche ou de lecture de fichiers sont ajoutés à côté."),
        ("2", "Les jetons", "L'unité de texte que le modèle lit, écrit, et que l'on compte.",
         """<p>Le modèle ne lit pas des lettres ni des mots entiers : il découpe le texte en morceaux appelés <strong>jetons</strong> (tokens). Tout se mesure en jetons : la longueur de ce qu'il peut lire, la longueur de sa réponse, les limites d'usage et le coût d'un appel à l'API. Un texte plus long, ou une langue découpée plus finement, consomme plus de jetons.</p>
<p>Ce découpage a une conséquence importante : le modèle ne « comprend » pas une phrase puis répond. À chaque pas, il calcule <strong>une probabilité pour chaque jeton qui pourrait suivre</strong>, en tire un, l'ajoute, et recommence. Ce sont des statistiques sur des quantités énormes de texte, appliquées par des calculs mathématiques. Deux phrases possibles après « Il était une fois » : la plus probable n'est pas toujours tirée, d'où des réponses différentes à chaque essai.</p>
<p>Choisissez une phrase, déplacez la température, puis tirez 20 fois. Ensuite, estimez un de vos textes : le résultat est un <strong>ordre de grandeur</strong>, le vrai compte dépend du modèle et l'API propose un compteur exact (voir les sources).</p>""" + tok,
         "Expliquer pourquoi une réponse est un tirage parmi des probabilités, et donner l'ordre de grandeur d'un document en jetons.",
         "Compter en pages ou en mots donne une idée, jamais le chiffre : deux textes de même longueur peuvent coûter des jetons différents."),
        ("3", "Les hallucinations", "Un texte faux dit avec assurance.",
         """<p>Puisque le modèle tire la suite la plus plausible, et non la plus vraie, il peut produire une affirmation fausse ou une source qui n'existe pas, avec le même ton que le vrai. On parle d'<strong>hallucination</strong> : c'est une conséquence directe de ce que vous venez de voir, pas un bogue rare. Aucune phrase magique ne la supprime : on la réduit par la manière de demander, puis on la contrôle.</p>
<p>Quatre leviers documentés :</p>
<ul class="pc-list">
<li><strong>Autoriser le « je ne sais pas »</strong> : dire explicitement qu'admettre l'incertitude est une bonne réponse.</li>
<li><strong>Citer d'abord</strong> : sur un long document, demander les passages exacts avant l'analyse, puis ne raisonner que sur eux.</li>
<li><strong>Exiger des citations</strong> pour chaque affirmation, et retirer celles qu'aucun passage ne soutient.</li>
<li><strong>Limiter aux documents fournis</strong> : interdire de s'appuyer sur ses connaissances générales.</li>
</ul>
<p>Réécrivez cette demande avec au moins deux leviers :</p>""" +
         pair("Avant", "Résume les risques juridiques de ce contrat et dis-moi ce qu'on doit négocier.", "Une version possible",
              "Voici le contrat entre <contrat> et </contrat> (ces balises de délimitation sont expliquées à l'étape 5).\n1. Extrais d'abord les passages exacts qui parlent de responsabilité, de résiliation et de pénalités. Si tu n'en trouves pas, écris « aucun passage trouvé ».\n2. Analyse les risques en citant le numéro de chaque passage. N'utilise rien d'autre que ce contrat.\n3. Si un point te semble manquer, dis « je ne peux pas l'affirmer à partir du document ».") +
         reveal("Ce que ça ne règle pas", "<p>Ces techniques réduisent les hallucinations, elles ne les suppriment pas. Pour une décision importante, une personne relit les passages cités dans le document d'origine. Un chiffre, une date, une référence légale ou une citation s'écrivent dans un texte seulement après vérification à la source.</p>"),
         "Réécrire une demande pour qu'elle autorise l'incertitude et exige des passages, puis vérifier un passage cité à la main.",
         "Une réponse bien rédigée peut être fausse : le ton d'assurance ne dit rien de l'exactitude."),
        ("4", "La fenêtre de contexte", "Tout ce que le modèle peut voir à un instant donné, et rien d'autre.",
         """<p>La fenêtre de contexte est la « mémoire de travail » du modèle : <strong>tout</strong> ce qu'il peut consulter pour répondre, sa réponse comprise. Elle contient bien plus que votre dernier message : consignes du système, fichiers d'instructions, définitions des outils, historique de la conversation, fichiers lus, résultats des outils. Le modèle n'a pas de mémoire en dehors de cette fenêtre : une nouvelle session repart de zéro.</p>
<p>Une fenêtre plus grande n'améliore pas la réponse : à mesure que le contexte grossit, la précision et le rappel peuvent baisser : c'est ce que la documentation appelle <em>context rot</em>. Choisir ce qui entre compte autant que la place disponible.</p>
<p>Regardez la fenêtre se remplir au fil d'une session d'agent, puis se compacter.</p>""" + gauge,
         "Citer ce qui occupe une fenêtre en dehors de votre message, et dire pourquoi la remplir n'est pas un but.",
         "Les valeurs de l'animation sont des exemples pour comprendre, pas des mesures. Une interface de chat peut aussi faire glisser la conversation en oubliant les débuts."),
        ("5", "Le prompt engineering", "Écrire pour un lecteur très compétent qui n'a aucun contexte.",
         """<p>Un prompt est un texte de travail : on le rédige comme une consigne à un collègue brillant qui arrive ce matin. La règle d'or de la documentation : montrez votre consigne à quelqu'un qui n'a pas le contexte et demandez-lui de l'exécuter. S'il hésite, le modèle hésitera aussi.</p>
<ul class="pc-list">
<li><strong>Être clair et direct</strong> : le résultat attendu, son format, ses contraintes, les étapes dans l'ordre quand l'ordre compte.</li>
<li><strong>Donner le contexte et la raison</strong> : « pas de listes à puces, ce texte sera lu à voix haute » vaut mieux que « pas de listes ».</li>
<li><strong>Donner des exemples</strong> : trois à cinq, proches de votre cas réel, variés, séparés des consignes par des balises.</li>
<li><strong>Structurer avec des balises</strong> (<code>&lt;consignes&gt;</code>, <code>&lt;document&gt;</code>, <code>&lt;exemple&gt;</code>) quand le prompt mélange consignes, documents et exemples.</li>
<li><strong>Donner un rôle</strong> en une phrase pour cadrer le ton et le point de vue.</li>
</ul>
<p>Améliorez cette demande :</p>""" +
         pair("Avant", "Fais-moi un mail de relance client.", "Une version possible",
              "Tu rédiges pour une ESN. Écris un e-mail de relance à un client dont la proposition est restée sans réponse depuis dix jours.\nContexte : première relance, ton cordial et direct, sans pression commerciale.\nFormat : objet, puis trois phrases au plus, une question fermée pour avancer.\n<exemple>\nObjet : Votre avis sur la proposition\nBonjour, je reviens vers vous au sujet de la proposition du 3. Avez-vous pu la relire ? Je peux répondre à vos questions cette semaine.\n</exemple>") +
         reveal("Pourquoi la seconde marche mieux", "<p>Elle dit pour qui on écrit, dans quelle situation, avec quel ton, quel format, et montre un exemple. Rien n'est laissé à deviner. Notez aussi ce qu'elle ne fait pas : elle n'empile pas vingt règles. Le but est le plus petit ensemble d'informations qui change vraiment le résultat.</p>"),
         "Transformer une demande vague en consigne qu'un collègue sans contexte pourrait exécuter.",
         "Ajoutez au prompt ce qui manque au lecteur ; ce qui rassure l'auteur l'alourdit sans l'améliorer."),
        ("6", "De l'assistant à l'agent", "Un modèle, des outils et une boucle.",
         f"""<p>Un assistant de conversation répond puis s'arrête. Un <strong>agent</strong> reçoit un objectif et <strong>boucle</strong> : il réfléchit, appelle un outil (lire un fichier, lancer une commande, chercher), lit le résultat qui entre dans son contexte, puis décide de continuer ou de s'arrêter. Tout ce que vous venez de voir (jetons, fenêtre, probabilités) se rejoue à chaque tour de cette boucle.</p>
{LOOP}
<p>Deux familles de systèmes se distinguent : dans un <strong>workflow</strong>, le chemin est écrit à l'avance dans du code et le modèle remplit des étapes ; dans un <strong>agent</strong>, c'est le modèle qui décide des étapes et des outils. Le conseil constant de la documentation d'Anthropic : commencer par la solution la plus simple (un seul appel, bien contextualisé) et n'ajouter de l'autonomie que si la tâche l'exige, parce que l'autonomie coûte en latence, en argent et en risque d'erreurs qui s'accumulent.</p>
<p>Deux conséquences pour la suite. D'abord, <strong>chaque outil est une porte ouverte</strong> : lire un fichier est bénin, lancer une commande ou écrire dans une base ne l'est pas, d'où les permissions du parcours suivant. Ensuite, <strong>ce qui entre dans la boucle</strong> (pages web, fichiers, résultats d'outils) est du texte que le modèle lit : s'il est hostile, il peut tenter de détourner l'agent (étape 7).</p>""" +
         reveal("Question", "<p>Dans l'exemple, qu'est-ce qui décide que la boucle s'arrête ? Aucun compteur : le modèle juge que le test est vert. D'où l'intérêt de lui donner un contrôle qu'il peut lancer, plutôt que de lui faire confiance sur parole (parcours Harness).</p>"),
         "Décrire la boucle d'un agent et dire ce qui distingue un workflow d'un agent.",
         "Plus d'autonomie n'améliore pas le résultat : une tâche aux étapes connues se traite mieux avec un workflow, plus simple à contrôler."),
        ("7", "Risques et usages responsables", "Ce qu'on n'envoie pas, ce qu'on vérifie, qui décide.",
         """<ul class="pc-list">
<li><strong>Données</strong> : ne pas coller de données personnelles, de secrets ni de données client réelles dans un outil que l'on ne maîtrise pas. Anonymiser ou fabriquer des exemples.</li>
<li><strong>Vérification</strong> : relire, contrôler les chiffres, les références et les citations à la source.</li>
<li><strong>Responsabilité</strong> : la décision et la signature restent humaines. Le modèle propose, la personne répond du résultat.</li>
<li><strong>Calcul</strong> : un montant, un total ou un contrôle s'obtiennent par un tableur ou un script vérifiable. Le modèle lit et rédige autour.</li>
<li><strong>Injection de prompt</strong> : un texte lu par l'agent (page web, README, ticket, résultat d'un outil) peut contenir des instructions cachées qui cherchent à détourner son comportement. Le modèle ne distingue pas toujours ce qui vient de vous de ce qui vient du contenu qu'il lit.</li>
</ul>
<table class="pc-table"><thead><tr><th>Réflexe</th><th>Pourquoi</th></tr></thead><tbody>
<tr><td>Relire les commandes avant de les approuver</td><td>C'est le dernier filet quand le contenu lu est hostile</td></tr>
<tr><td>Ne pas passer de contenu non fiable directement à l'agent</td><td>Un fichier téléchargé, un e-mail ou un ticket externe sont des entrées, pas des consignes</td></tr>
<tr><td>Limiter les permissions et isoler (bac à sable, machine virtuelle)</td><td>Un agent détourné ne peut faire que ce qu'on lui a permis</td></tr>
<tr><td>Ne brancher que des serveurs MCP de confiance</td><td>Ils agissent avec vos droits et renvoient du texte que l'agent lira</td></tr></tbody></table>
<p>Ces réflexes figurent dans la documentation de sécurité de Claude Code, qui ajoute qu'aucune protection n'est complète. Un exemple concret au parcours suivant : les documentations et les pages web que l'agent consulte avec Context7 ou Playwright sont aussi des entrées non fiables.</p>
<p>Prochaine étape : passer d'un prompt isolé à un <strong>contexte entretenu</strong>, avec des fichiers, des skills et des outils. C'est le parcours suivant.</p>""",
         "Dire ce qu'on ne colle jamais dans un outil d'IA, nommer l'injection de prompt et ses parades, et dire qui répond du résultat.",
         "« C'est l'IA qui l'a dit » ne tient devant personne. La personne qui diffuse un texte en répond."),
    ]
    out = "\n".join(stage(*x) for x in s)
    return (intro("Sept étapes pour comprendre ce que fait vraiment un modèle de langage : le texte, les jetons, les erreurs qui en découlent, la fenêtre de contexte, la manière de demander, l'agent, les risques. Aucun outil à installer ; un outil d'IA au choix suffit pour les exercices. Environ deux heures et demie, à calibrer en séance.") +
            nav(CULTURE_NAV) + out +
            checklist("Vous avez compris si vous savez", [
                "dire pourquoi un modèle produit du texte plausible sans consulter une base de faits ;",
                "estimer les jetons d'un texte et lister ce qui occupe une fenêtre de contexte ;",
                "expliquer pourquoi remplir la fenêtre ne rend pas la réponse meilleure ;",
                "réécrire une demande pour réduire le risque d'hallucination, puis vérifier à la source ;",
                "décrire la boucle d'un agent, et nommer l'injection de prompt et deux parades ;",
                "écrire une consigne qu'un collègue sans contexte pourrait exécuter."]) +
            sources([("https://www.anthropic.com/engineering/building-effective-agents", "Building effective agents (workflows et agents)"),
                     (DOC + "security", "Sécurité de Claude Code (injection de prompt)"),
                     (API + "build-with-claude/context-windows", "Fenêtres de contexte (jetons, context rot, compaction)"),
                     (API + "test-and-evaluate/strengthen-guardrails/reduce-hallucinations", "Réduire les hallucinations"),
                     (API + "build-with-claude/prompt-engineering/claude-prompting-best-practices", "Bonnes pratiques de prompting"),
                     (API + "build-with-claude/token-counting", "Compter les jetons (API)")]) +
            '<script src="src/parcours.js"></script>')


# ---------------------------------------------------------------------------------------------------------------------
# Parcours 2 : context engineering
# ---------------------------------------------------------------------------------------------------------------------

AGENTS_GOOD = """# AGENTS.md

Site vitrine (Next.js, pnpm). Répondre en français.

## Vérifier avant de dire « fait »
- `npx tsc --noEmit` puis `pnpm test:int` : citer le résultat.
- `pnpm lint` est cassé : ne pas s'y fier.

## Pièges
- Le serveur de développement tourne sur le port 3100, pas 3000.
- Après un changement de collection : `pnpm migrate:create <nom>` puis `pnpm migrate`.

## Interdit
- Pas de commit sur main : une branche par sujet, une PR par branche."""

AGENTS_BAD = """# AGENTS.md

Tu es un expert senior. Écris du code propre, performant et maintenable.
Fais attention à la sécurité. Teste bien ton code. Sois prudent."""

RULE_EX = """---
paths:
  - "src/api/**/*.ts"
---

# Règles de l'API

- Valider toute entrée avant de l'utiliser.
- Répondre aux erreurs avec le format commun (code, message, identifiant de requête).
- Un endpoint nouveau a un test qui échoue avant d'être écrit."""

SKILL_EX = """---
name: relance-client
description: Rédiger une relance commerciale. À utiliser quand l'utilisateur demande un mail de relance ou « relance ce client ».
disable-model-invocation: false
---

# Relance client

1. Demander la date et l'objet de la dernière proposition si absents.
2. Rédiger un objet et trois phrases au plus, une question fermée.
3. Relire : aucun montant ni date qui ne vienne de l'utilisateur."""

AGENT_EX = """---
name: relecteur
description: Relit un diff et signale les risques. À utiliser après une modification, avant la PR.
tools: Read, Glob, Grep
model: sonnet
---

Tu relis un changement sans le modifier. Pour chaque constat : fichier, comportement observé, comment le reproduire,
importance. N'affirme pas avoir exécuté une commande que tu ne peux pas lancer."""

MCP_EX = {
    "mcpServers": {
        "base-de-donnees": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@bytebase/dbhub"],
            "env": {"DATABASE_URL": "${DB_CONNECTION_STRING}"},
        },
        "api-interne": {
            "type": "http",
            "url": "https://mcp.example.org/mcp",
            "headers": {"Authorization": "Bearer ${API_TOKEN}"},
        },
    }
}

PROMPT_DEV = """Ajoute la pagination à la liste des commandes avec TanStack Query. use context7

Puis ouvre http://localhost:3100/commandes, prends une capture à 1280 px et une en mobile, et liste les erreurs de la console."""

MCP_DEV = {
    "mcpServers": {
        "context7": {
            "type": "http",
            "url": "https://mcp.context7.com/mcp",
            "headers": {"Authorization": "Bearer ${CONTEXT7_API_KEY}"},
        },
        "playwright": {
            "type": "stdio",
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--isolated", "--viewport-size", "1280x720", "--output-dir", "./captures"],
        },
        "playwright-mobile": {
            "type": "stdio",
            "command": "npx",
            "args": ["@playwright/mcp@latest", "--isolated", "--device", "iPhone 15", "--output-dir", "./captures"],
        },
    }
}

SETTINGS_EX = {
    "permissions": {
        "allow": ["Bash(npm test *)", "Bash(git status)"],
        "ask": ["Bash(git push *)"],
        "deny": ["Read(./.env)", "Read(./secrets/**)", "Bash(rm -rf *)", "mcp__playwright__browser_run_code_unsafe"],
    }
}


def parse_front(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit("parcours : en-tête manquant dans un exemple de skill ou d'agent")
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}


MCP_REST = """GET /orders/42 HTTP/1.1
Authorization: Bearer <jeton>

200 OK
{ "id": 42, "status": "shipped" }"""

MCP_LIST = """-> {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

<- {"jsonrpc": "2.0", "id": 1, "result": {"tools": [{
     "name": "get_order",
     "description": "Retourne une commande à partir de son numéro.",
     "inputSchema": {"type": "object",
       "properties": {"id": {"type": "integer"}}, "required": ["id"]}
   }]}}"""

MCP_CALL = """-> {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "get_order", "arguments": {"id": 42}}}

<- {"jsonrpc": "2.0", "id": 2, "result": {
     "content": [{"type": "text", "text": "Commande 42 : expédiée"}],
     "isError": false}}"""

MCP_VS = """<h3 class="pc-h3">Une API, pour un agent</h3>
<p>Vous connaissez déjà le principe : un service expose des opérations, un client les appelle. MCP est ce contrat, pensé pour un <strong>agent</strong> plutôt que pour votre code. Les différences tiennent à une idée : <strong>c'est le modèle qui découvre les opérations et décide de les appeler pendant la session</strong>, au lieu d'un développeur qui les a codées à l'avance.</p>
<table class="pc-table mcp-vs"><thead><tr><th></th><th>API classique (REST)</th><th>Serveur MCP</th></tr></thead><tbody>
<tr><td>Qui appelle</td><td>Votre code, écrit à l'avance</td><td>Le modèle, qui décide en cours de session</td></tr>
<tr><td>Découverte</td><td>Vous lisez la documentation (OpenAPI) avant de coder</td><td>Le client demande la liste au serveur, à la connexion (<code>tools/list</code>)</td></tr>
<tr><td>Description</td><td>Pour un humain : pages de doc, exemples</td><td>Pour le modèle : une phrase en langage naturel et un schéma JSON des paramètres</td></tr>
<tr><td>Forme d'un appel</td><td><code>GET /orders/42</code></td><td><code>tools/call</code> avec le nom de l'outil et ses arguments</td></tr>
<tr><td>Données</td><td>Des URL de ressources</td><td><code>resources/list</code> et <code>resources/read</code>, par URI</td></tr>
<tr><td>Modèles de demande</td><td>Aucun</td><td><code>prompts/list</code> et <code>prompts/get</code></td></tr>
<tr><td>Format</td><td>Libre (JSON, XML, formulaire)</td><td>Toujours du JSON-RPC 2.0</td></tr>
<tr><td>Transport</td><td>HTTP</td><td>Un processus local en entrée et sortie standard, ou HTTP</td></tr>
<tr><td>Authentification</td><td>Clé ou OAuth gérés par votre code</td><td>En-têtes ou OAuth déclarés dans la configuration du client</td></tr>
<tr><td>Résultat</td><td>Code HTTP et corps de réponse</td><td>Du contenu lisible par le modèle, qui entre dans le contexte</td></tr></tbody></table>
<div class="mcp-duo">
<div><b>REST : un appel codé en dur</b>""" + code(MCP_REST) + """</div>
<div><b>MCP : l'agent découvre la liste</b>""" + code(MCP_LIST) + """</div>
<div><b>MCP : puis il appelle un outil</b>""" + code(MCP_CALL) + """</div>
</div>
<p>Un serveur MCP expose trois choses, chacune déclenchée par quelqu'un de différent :</p>
<div class="mcp-three">
<div class="mcp-card"><span class="mcp-tag mcp-t0">Outils</span><p>Des <strong>actions</strong> : chercher, créer, lancer. Elles sont décrites au modèle, qui décide de les appeler.</p><p class="mcp-ex">Exemples : <code>get_order</code>, <code>browser_click</code></p></div>
<div class="mcp-card"><span class="mcp-tag mcp-t1">Ressources</span><p>Des <strong>données à lire</strong>, désignées par une URI. Dans Claude Code, vous les référencez vous-même avec <code>@</code>.</p><p class="mcp-ex">Exemple : <code>@postgres:schema://users</code></p></div>
<div class="mcp-card"><span class="mcp-tag mcp-t2">Prompts</span><p>Des <strong>modèles de demande</strong> avec des arguments, qui deviennent des commandes que vous tapez.</p><p class="mcp-ex">Exemple : <code>/mcp__github__pr_review 456</code></p></div>
</div>
"""

def contexte() -> str:
    # contrôles du build : les exemples doivent être corrects
    for must in ("name", "description"):
        if must not in parse_front(SKILL_EX) or must not in parse_front(AGENT_EX):
            sys.exit(f"parcours : exemple sans {must}")
    mcp_json = json.dumps(MCP_EX, indent=2, ensure_ascii=False)
    settings_json = json.dumps(SETTINGS_EX, indent=2, ensure_ascii=False)
    mcp_dev_json = json.dumps(MCP_DEV, indent=2, ensure_ascii=False)
    for payload in (mcp_json, settings_json, mcp_dev_json):
        json.loads(payload)
        if re.search(r"(?i)(sk-[a-z0-9]{8,}|bearer\s+[a-z0-9]{12,}|password\"\s*:\s*\"[^$])", payload):
            sys.exit("parcours : un secret semble écrit en clair dans un exemple de configuration")

    rule_quiz = [
        ("allow Bash(aws s3 ls) et deny Bash(aws *) : que se passe-t-il pour aws s3 ls ?", pill("deny") + " Refusé. Une règle d'interdiction large bloque aussi ce qu'une règle d'autorisation plus précise voudrait laisser passer."),
        ("allow Bash(git push *) et ask Bash(git push *) : que se passe-t-il pour git push origin feat ?", pill("ask") + " Une confirmation est demandée. Une règle « demander » l'emporte sur une règle « autoriser »."),
        ("Un hook PreToolUse répond « autoriser » mais deny Read(./.env) existe : lecture de .env ?", pill("deny") + " Refusée. Les règles d'interdiction et de confirmation sont évaluées quel que soit le résultat d'un hook."),
    ]
    quiz_rows = "".join(f"<tr><td>{esc(q)}</td><td>{reveal('Mon pronostic', a)}</td></tr>" for q, a in rule_quiz)

    s = [
        ("1", "Du prompt au contexte", "Choisir ce que le modèle voit, au lieu de tout lui montrer.",
         """<p>Le <strong>context engineering</strong> est l'ensemble des moyens qui sélectionnent et entretiennent ce qui se trouve dans le contexte du modèle pendant le travail : consignes, outils, données externes, historique. Le prompt n'en est qu'une partie. L'objectif tient en une phrase : le plus petit ensemble d'informations très utiles qui produit le résultat voulu.</p>
<p>Dans une session d'agent de code, ce qui entre dans la fenêtre vient de six endroits : les consignes du système, vos fichiers d'instructions, les définitions des outils (y compris ceux des serveurs MCP), la liste des skills, l'historique, et les résultats des outils. Quatre techniques gardent le contexte sain, et chacune a son pendant dans l'outil :</p>
<table class="pc-table"><thead><tr><th>Technique</th><th>Dans Claude Code</th></tr></thead><tbody>
<tr><td>Charger à la demande plutôt que tout précharger</td><td>Une skill n'entre en entier que lorsqu'elle est appelée ; l'agent lit les fichiers au moment du besoin</td></tr>
<tr><td>Résumer quand la fenêtre se remplit</td><td>La compaction de la conversation</td></tr>
<tr><td>Écrire des notes hors de la fenêtre</td><td>Les fichiers d'instructions, la mémoire automatique, les notes de session</td></tr>
<tr><td>Déléguer à un contexte propre</td><td>Les sous-agents, qui renvoient un résumé</td></tr></tbody></table>
<p>Revoyez l'animation de la fenêtre dans le parcours précédent et repérez les deux postes que vous contrôlez le mieux.</p>""",
         "Nommer les six sources du contexte d'une session d'agent et associer une technique à chacun de ses problèmes.",
         "Ajouter des informations « au cas où » alourdit le contexte. Ce qui n'aide pas la tâche la dessert."),
        ("2", "Piloter la session", "Une session est un outil qu'on conduit : l'effacer, la résumer, la rejouer.",
         """<p>Tout ce que vous venez de voir se joue pendant une <strong>session</strong>. Les bonnes pratiques de Claude Code tiennent en une contrainte : la fenêtre se remplit vite et la précision baisse quand elle se remplit. Presque chaque commande de session sert donc à garder le contexte utile.</p>
<table class="pc-table"><thead><tr><th>Geste</th><th>Effet</th></tr></thead><tbody>
<tr><td><code>Esc</code></td><td>Arrête l'agent en plein travail ; le contexte est conservé, on peut rediriger</td></tr>
<tr><td><code>Esc</code> deux fois, ou <code>/rewind</code></td><td>Restaure la conversation, le code, ou les deux, à un point précédent ; permet aussi de résumer à partir d'un message</td></tr>
<tr><td><code>/clear</code></td><td>Vide le contexte : à faire entre deux tâches sans rapport</td></tr>
<tr><td><code>/compact &lt;consignes&gt;</code></td><td>Résume la conversation en gardant ce que vous précisez (par exemple « les fichiers modifiés et les commandes de test »)</td></tr>
<tr><td><code>/context</code></td><td>Montre ce qui occupe la fenêtre et confirme que vos fichiers d'instructions sont chargés</td></tr>
<tr><td><code>/btw</code></td><td>Pose une question annexe dont la réponse n'entre pas dans l'historique</td></tr>
<tr><td><code>/rename</code>, <code>claude --continue</code>, <code>claude --resume</code></td><td>Nomme une session, reprend la dernière, ou choisit dans une liste : une session se traite comme une branche</td></tr>
<tr><td><code>Maj+Tab</code> (mode plan)</td><td>Explorer et planifier sans rien modifier, avant d'implémenter</td></tr></tbody></table>
<p>Le flux recommandé tient en quatre temps : <strong>explorer</strong>, <strong>planifier</strong>, <strong>implémenter</strong>, <strong>commiter</strong>. Si vous pouvez décrire la modification en une phrase, sautez la planification.</p>
<p>Trois mauvaises habitudes reviennent tout le temps :</p>
<ul class="pc-list">
<li><strong>La session fourre-tout</strong> : une tâche, puis une question sans rapport, puis on revient à la première. Le contexte est plein de bruit. Remède : <code>/clear</code> entre deux sujets.</li>
<li><strong>Corriger en boucle</strong> : l'agent se trompe, on corrige, il se trompe encore. Le contexte est pollué par les essais ratés. Remède : après deux corrections, <code>/clear</code> et un prompt meilleur qui reprend ce qu'on a appris.</li>
<li><strong>L'exploration sans limite</strong> : « investigue » sans cadrer fait lire des centaines de fichiers. Remède : cadrer, ou déléguer à un sous-agent (étape 6).</li>
</ul>
<p><strong>Exercice</strong> : vous avez corrigé trois fois la même erreur et l'agent recommence. Que faites-vous ?</p>""" +
         reveal("Piste", "<p>Ne pas corriger une quatrième fois. Noter ce qui a manqué (le fichier à suivre en exemple, la contrainte, le résultat attendu), faire <code>/clear</code>, et reformuler la demande avec ces éléments. Une session propre avec un meilleur prompt bat presque toujours une longue session de corrections.</p>"),
         "Choisir entre <code>/clear</code>, <code>/compact</code> et <code>/rewind</code> face à trois situations données.",
         "Les points de restauration ne suivent que les modifications faites par les outils d'édition de l'agent, pas celles d'une commande shell : ils ne remplacent pas git."),
        ("3", "Les fichiers d'instructions", "CLAUDE.md et AGENTS.md : du contexte persistant, pas une contrainte.",
         """<p>Chaque session démarre avec une fenêtre vide. Deux mécanismes transmettent la connaissance d'une session à l'autre : les fichiers d'instructions que <strong>vous</strong> écrivez (<code>CLAUDE.md</code>, ou <code>AGENTS.md</code> que Claude Code peut lire à la place), et la <strong>mémoire automatique</strong> que Claude écrit lui-même d'après vos corrections.</p>
<p>Deux faits à retenir. D'abord, ces fichiers sont du <strong>contexte</strong> : l'agent les lit et peut s'en écarter. Pour interdire une action quelle que soit sa décision, il faut un hook (parcours suivant). Ensuite, plus une instruction est précise et courte, plus elle est suivie de manière constante.</p>
<p>Si <code>CLAUDE.md</code> et <code>AGENTS.md</code> existent tous les deux, Claude Code lit <code>CLAUDE.md</code> ; pour partager un seul fichier avec d'autres outils, <code>CLAUDE.md</code> importe l'autre avec une ligne <code>@AGENTS.md</code>. C'est ce que fait ce projet : <code>AGENTS.md</code> porte les consignes, <code>CLAUDE.md</code> n'est qu'un pointeur. Des consignes qui ne concernent qu'une partie du code se rangent à part : c'est l'étape suivante, les règles.</p>
<p>Lequel de ces deux fichiers est le plus utile à un agent qui arrive sur le projet ?</p>""" +
         pair("Fichier A", AGENTS_BAD, "Fichier B", AGENTS_GOOD) +
         reveal("Réponse", "<p>Le B. Il contient ce que l'agent ne peut pas deviner en lisant le code : les commandes de vérification, les pièges, ce qui est interdit. Le A dit des intentions que n'importe quel modèle suit déjà (« écris du code propre ») sans rien de vérifiable. Une bonne instruction se teste : on peut dire si elle a été suivie.</p>") +
         "<p><strong>Exercice</strong> : écrivez dix lignes d'<code>AGENTS.md</code> pour un projet que vous connaissez, avec uniquement des commandes, des pièges et des interdits.</p>",
         "Produire dix lignes d'instructions vérifiables, et expliquer pourquoi elles ne remplacent pas un garde-fou.",
         "Un fichier trop long ou contradictoire dilue ce qui compte. Deux sources qui se contredisent valent pire qu'une seule."),
        ("4", "Les règles", "Des instructions rangées par sujet, chargées au bon moment.",
         f"""<p>Quand <code>AGENTS.md</code> grossit, tout y est lu à chaque session, même ce qui ne concerne qu'une partie du code. Les <strong>règles</strong> répondent à ce problème : un fichier Markdown par sujet dans <code>.claude/rules/</code> (<code>tests.md</code>, <code>api.md</code>, <code>securite.md</code>), découverts récursivement. Elles sont du contexte, comme les fichiers d'instructions : l'agent les lit et peut s'en écarter.</p>
<p>Deux comportements, selon l'en-tête du fichier :</p>
<table class="pc-table"><thead><tr><th>Règle</th><th>Quand elle entre dans le contexte</th></tr></thead><tbody>
<tr><td>Sans <code>paths</code></td><td>Au lancement de la session, avec la même priorité que <code>.claude/CLAUDE.md</code></td></tr>
<tr><td>Avec <code>paths</code> (motifs de fichiers)</td><td>Seulement quand l'agent lit, écrit ou modifie un fichier qui correspond</td></tr></tbody></table>
{code(RULE_EX)}
<p>Le champ <code>paths</code> accepte des motifs comme <code>src/**/*.{{ts,tsx}}</code> ; c'est le seul champ que Claude Code lit dans une règle. Vos règles personnelles vont dans <code>~/.claude/rules/</code> et s'appliquent à tous vos projets ; elles sont chargées avant celles du projet, et si les deux se contredisent, l'agent peut suivre l'une ou l'autre : gardez-les cohérentes.</p>
<p>Où ranger quoi ? Lisez les cinq cas puis pronostiquez :</p>
<table class="pc-table"><thead><tr><th>Cas</th><th>Où</th></tr></thead><tbody>
<tr><td>« Les tests se lancent avec <code>pnpm test</code> »</td><td>{reveal("Mon pronostic", "<p><code>AGENTS.md</code> : valable partout, court, utile à chaque session.</p>")}</td></tr>
<tr><td>« Les endpoints valident toute entrée »</td><td>{reveal("Mon pronostic", "<p>Une règle avec <code>paths: src/api/**</code> : elle ne pèse sur le contexte que quand on touche à l'API.</p>")}</td></tr>
<tr><td>« Pour publier une version, suivre ces onze étapes »</td><td>{reveal("Mon pronostic", "<p>Une skill : c'est une procédure appelée pour une tâche, pas une consigne permanente.</p>")}</td></tr>
<tr><td>« Ne jamais pousser sur <code>main</code> »</td><td>{reveal("Mon pronostic", "<p>Un hook (parcours Harness) : une interdiction doit être appliquée par l'outil, pas suggérée au modèle. On peut aussi l'écrire en règle pour l'expliquer, mais elle ne suffit pas.</p>")}</td></tr>
<tr><td>« Je préfère des réponses courtes »</td><td>{reveal("Mon pronostic", "<p><code>~/.claude/rules/</code> : une préférence personnelle, indépendante du projet.</p>")}</td></tr></tbody></table>
<p><strong>À ne pas confondre</strong> : les « règles de permission » (deny, ask, allow) de l'étape 9 sont appliquées par l'outil, dans les réglages. Les règles de cette étape sont des instructions lues par le modèle.</p>
<p><strong>Exercice</strong> : prenez votre <code>AGENTS.md</code> et repérez deux paragraphes qui ne concernent qu'un type de fichier. Déplacez-les dans une règle avec <code>paths</code>.</p>""",
         "Écrire une règle avec <code>paths</code> et dire pourquoi elle ne se charge pas à chaque session.",
         "Une règle est aussi peu contraignante qu'une ligne d'AGENTS.md : elle range les consignes sans rien garantir."),
        ("5", "Les skills", "Une procédure chargée seulement quand elle sert.",
         f"""<p>Une skill est un dossier avec un fichier <code>SKILL.md</code> : un en-tête qui dit <strong>quand</strong> l'appeler, un corps qui dit <strong>comment</strong>. Claude l'invoque quand la description correspond à la conversation, ou vous la tapez avec <code>/nom</code>.</p>
{code(SKILL_EX)}
<p>Le point clé est le <strong>chargement progressif</strong> : seule la description reste toujours dans le contexte ; le corps n'est lu qu'à l'appel, et les fichiers annexes seulement au besoin. Une skill volumineuse ne coûte donc rien tant qu'on ne s'en sert pas.</p>
{SKL}
<table class="pc-table"><thead><tr><th>Emplacement</th><th>Portée</th></tr></thead><tbody>
<tr><td><code>~/.claude/skills/&lt;nom&gt;/SKILL.md</code></td><td>Personnel : tous vos projets</td></tr>
<tr><td><code>.claude/skills/&lt;nom&gt;/SKILL.md</code></td><td>Ce dépôt, partagé en le versionnant</td></tr>
<tr><td>Plugin</td><td>Là où le plugin est activé</td></tr></tbody></table>
<p>Champs utiles : <code>disable-model-invocation: true</code> pour ne la lancer que par commande, <code>allowed-tools</code> pour pré-autoriser des outils pendant son exécution.</p>
<p><strong>Exercice</strong> : transformez une tâche que vous répétez (relance, compte rendu, revue) en skill. Écrivez d'abord la description : elle doit dire quand, jamais le déroulé.</p>""",
         "Écrire une skill dont la description déclenche au bon moment et dont le corps tient en dix lignes.",
         "Une description qui résume les étapes pousse l'agent à les suivre sans lire le corps. Elle sert à choisir, pas à exécuter."),
        ("6", "Les agents", "Un second collaborateur avec sa propre fenêtre de contexte.",
         f"""<p>Un <strong>sous-agent</strong> est un assistant spécialisé qui travaille dans une fenêtre de contexte isolée, avec ses propres consignes, ses propres outils et éventuellement un autre modèle. Il fait la tâche et ne renvoie qu'un résumé : la lecture de trente fichiers ne pollue pas la conversation principale. C'est la technique « déléguer à un contexte propre » du début du parcours.</p>
<p>Dans un schéma <strong>orchestrateur</strong>, l'agent principal ne lit pas tout : il distribue à chaque sous-agent le <em>minimum</em> dont il a besoin (la tâche, les critères, les fichiers utiles), puis ne reçoit que des résumés. Comparez les deux modes :</p>
{ORCH}
{code(AGENT_EX)}
<p>Le fichier vit dans <code>.claude/agents/</code> (projet) ou <code>~/.claude/agents/</code> (personnel). Les champs obligatoires sont <code>name</code> et <code>description</code> ; <code>tools</code> restreint ses outils (ici, lecture seule) et hérite de tout si on l'omet. On l'invoque en le nommant, par @-mention, ou pour toute la session.</p>
<p>Limites à connaître : un sous-agent n'a pas votre conversation et un nouvel appel repart d'un contexte vide (un sous-agent terminé peut toutefois être repris), il consomme du quota comme la session principale, et le nombre d'agents simultanés et la profondeur d'imbrication sont bornés.</p>
<p><strong>Exercice</strong> : écrivez un agent « relecteur » en lecture seule pour votre projet. Quelles sont les trois informations que vous lui donnez avec sa tâche, puisqu'il n'a pas votre conversation ?</p>""" +
         reveal("Piste", "<p>La demande d'origine et ses critères de réussite, le diff ou les fichiers touchés, et les résultats des vérifications déjà faites. Un agent ne voit que ce qu'on lui envoie : un résumé vague produit une relecture vague.</p>"),
         "Dire ce qu'un sous-agent gagne (un contexte propre) et ce qu'il perd (la conversation).",
         "Restreindre les outils est une protection réelle pour un relecteur. Un agent qui peut tout modifier relit mal ce qu'il peut aussi corriger."),
        ("7", "MCP : brancher des outils", "Un protocole commun pour donner à l'agent l'accès à des données et à des services.",
         f"""<p>Le <strong>Model Context Protocol</strong> (MCP) permet à l'agent d'utiliser des serveurs externes : base de données, tracker, documentation, navigateur.</p>
{MCP_VS}
<p>Deux conséquences pour vous. Leurs outils <strong>coûtent du contexte</strong>, mais peu : par défaut, la recherche d'outils ne charge au démarrage que les noms, et les définitions complètes seulement au moment du besoin. Et ils <strong>peuvent agir</strong> (lire des données, écrire, supprimer) : on n'installe donc que des serveurs de confiance, avec l'accès minimal.</p>
<table class="pc-table"><thead><tr><th>Portée</th><th>Visible</th><th>Stockée dans</th></tr></thead><tbody>
<tr><td>Locale (par défaut)</td><td>Ce projet, vous seul</td><td><code>~/.claude.json</code></td></tr>
<tr><td>Projet</td><td>Ce projet, toute l'équipe</td><td><code>.mcp.json</code> à la racine, versionné</td></tr>
<tr><td>Utilisateur</td><td>Tous vos projets, vous seul</td><td><code>~/.claude.json</code></td></tr></tbody></table>
<p>Un fichier <code>.mcp.json</code> de projet :</p>{code(mcp_json)}
<p>Remarquez les <code>${{...}}</code> : les secrets viennent de variables d'environnement, jamais du fichier versionné. Un serveur de portée projet demande une approbation avant son premier usage.</p>
{cmd("claude mcp add --transport http <nom> <url>")}{cmd("claude mcp list")}{cmd("claude mcp remove <nom>")}
<p>Dans les règles de permission, un outil MCP se nomme <code>mcp__&lt;serveur&gt;__&lt;outil&gt;</code> (par exemple <code>mcp__notion__*</code> ou simplement <code>mcp__notion</code> pour tous les outils d'un serveur ; une règle <code>mcp__</code> avec des parenthèses est ignorée).</p>
<p><strong>Exercice</strong> : écrivez le <code>.mcp.json</code> d'un serveur en lecture seule sur une base de test. Où va le mot de passe ?</p>""" +
         reveal("Réponse", "<p>Dans une variable d'environnement, référencée par <code>${NOM}</code>, définie hors du dépôt. Le fichier versionné ne contient aucun secret. Pour la base elle-même, un compte en lecture seule : la permission la plus étroite possible est la première protection.</p>"),
         "Choisir la bonne portée d'un serveur MCP et écrire sa configuration sans secret en clair.",
         "Un serveur MCP agit avec vos droits, il ne se limite pas à lire. Chaque serveur ajouté alourdit aussi le contexte."),
        ("8", "Context7 et Playwright", "Deux serveurs MCP que tout développeur devrait avoir : la doc à jour, et un navigateur pour vérifier.",
         f"""<p>Parmi tous les serveurs MCP possibles, deux changent le quotidien d'un développeur web, parce qu'ils attaquent deux défauts classiques d'un agent : <strong>il code avec des API périmées</strong>, et <strong>il affirme que l'interface marche sans l'avoir vue</strong>.</p>
<h3 class="pc-h3">Context7 : la documentation à jour, à la version</h3>
<p>Un modèle a été entraîné jusqu'à une date. Une bibliothèque a changé depuis : il écrit alors une API qui n'existe plus, avec assurance (c'est une hallucination, parcours Culture). <strong>Context7</strong> est un service qui fournit à l'agent la documentation et des exemples de code <em>de la version voulue</em>. Il expose deux outils : <code>resolve-library-id</code> (trouver l'identifiant d'une bibliothèque à partir de son nom) et <code>query-docs</code> (interroger sa documentation). On l'appelle en ajoutant « use context7 » à la demande, ou en nommant l'identifiant (<code>/supabase/supabase</code>) pour sauter la recherche. Une clé d'API gratuite relève les limites d'usage.</p>
<p>Le plus utile : l'écrire une fois dans <code>AGENTS.md</code> (« pour toute API de bibliothèque, consulter Context7 avant d'écrire du code »), pour ne plus avoir à le demander. Limite à garder en tête : ces documentations sont alimentées par la communauté et ne sont pas garanties exactes ; c'est une source à citer et à vérifier, qui reste du texte non fiable (voir l'injection de prompt).</p>
<h3 class="pc-h3">Playwright : un navigateur que l'agent pilote</h3>
<p>Le serveur MCP <strong>Playwright</strong> donne à l'agent un vrai navigateur : ouvrir une page, cliquer, remplir un formulaire, lire la console et les requêtes réseau, prendre une capture. Il travaille surtout à partir d'<strong>instantanés d'accessibilité</strong> (l'arbre de la page, en texte), pas de pixels : l'agent n'a pas besoin de « voir » l'image pour agir. La capture sert à <em>montrer</em> le résultat, à vous comme à un agent vérificateur. Outils principaux : <code>browser_navigate</code>, <code>browser_snapshot</code>, <code>browser_click</code>, <code>browser_type</code>, <code>browser_take_screenshot</code>, <code>browser_console_messages</code>, <code>browser_network_requests</code>.</p>
<p>Un fichier <code>.mcp.json</code> avec les deux, plus un second navigateur configuré en mobile (le serveur se lance avec <code>--viewport-size</code> ou <code>--device</code>) :</p>{code(mcp_dev_json)}
<p>Variante sans serveur MCP : Context7 propose aussi un mode « CLI + skill » (<code>npx ctx7 setup --claude</code>), et Claude Code peut piloter votre navigateur Chrome via son extension. Le principe reste le même : donner à l'agent un moyen de <strong>vérifier</strong>.</p>
<p>Voici ce que ça donne en pratique. Demandez, avec ces deux serveurs branchés :</p>{code(PROMPT_DEV)}
<p>L'agent lit la documentation de la bonne version, écrit le code, ouvre la page, capture les deux tailles et rapporte les erreurs. Vous relisez des preuves.</p>
<p><strong>Exercice</strong> : branchez les deux serveurs sur un projet jetable, demandez une petite évolution d'interface, et obtenez deux captures (bureau et mobile) sans aucune erreur de console.</p>""" +
         reveal("Sécurité : ce qu'il faut restreindre", "<p>Playwright n'est <strong>pas une frontière de sécurité</strong>. Son outil <code>browser_run_code_unsafe</code> exécute du JavaScript arbitraire côté serveur et équivaut à une exécution de code à distance : refusez-le dans les permissions (<code>mcp__playwright__browser_run_code_unsafe</code>). N'ouvrez que des sites de confiance : une page hostile est une entrée non fiable (injection de prompt). N'exposez jamais le serveur au réseau (<code>--host 0.0.0.0</code>). Pour Context7, la clé d'API se passe par variable d'environnement, jamais en clair dans le fichier versionné.</p>"),
         "Obtenir, avec Context7 et Playwright, une évolution d'interface vérifiée par deux captures et une console propre.",
         "Une capture n'est une preuve que si l'agent a ouvert la bonne page, dans la bonne taille. Demandez l'adresse, la taille et la date de chaque capture."),
        ("9", "Permissions et réglages", "Ce que l'agent peut faire, décidé hors de son texte.",
         f"""<p>Contrairement aux fichiers d'instructions, les <strong>règles de permission</strong> sont appliquées par l'outil, pas suggérées au modèle. Elles vivent dans les fichiers de réglages : <code>.claude/settings.json</code> (projet, partagé), <code>.claude/settings.local.json</code> (vos choix locaux, à garder hors du dépôt), <code>~/.claude/settings.json</code> (personnel), et des réglages d'organisation qui priment.</p>
{code(settings_json)}
<p>Trois listes, évaluées dans cet ordre : <strong>deny</strong>, puis <strong>ask</strong>, puis <strong>allow</strong>. La première qui correspond décide, quelle que soit la précision des règles. Pronostiquez :</p>
<table class="pc-table"><thead><tr><th>Cas</th><th>Résultat</th></tr></thead><tbody>{quiz_rows}</tbody></table>
<p>Les <strong>modes</strong> règlent le niveau d'autonomie : <code>default</code> (demande à la première utilisation), <code>acceptEdits</code> (accepte les modifications de fichiers), <code>plan</code> (explore sans modifier), <code>auto</code> (un classifieur vérifie les actions), <code>dontAsk</code> (refuse ce qui demanderait), <code>bypassPermissions</code> (aucune demande : réservé aux environnements isolés).</p>
<p><strong>Limite à connaître</strong> : une règle sur une commande shell lit le texte que l'agent écrit. Elle couvre la forme habituelle d'un appel, pas toutes ses variantes : ce n'est pas une frontière de sécurité autour d'un programme. Pour bloquer la lecture d'un fichier par les outils de fichiers, on écrit une règle <code>Read</code> sur son chemin.</p>
<p>Ce que les règles ne savent pas dire (« pas de commit sur main », « une PR doit être liée à une issue ») se règle avec des <strong>hooks</strong>. Un hook est un script que l'outil lance à un moment précis du travail (avant un outil, après une modification, à la fin d'une réponse). Il reçoit du JSON sur son entrée, et s'il termine avec le code <strong>2</strong>, l'action est bloquée et son message d'erreur revient à l'agent comme retour. C'est l'objet du parcours Harness, où l'on en écrit un.</p>""",
         "Prédire le résultat d'un jeu de règles deny, ask et allow, et dire ce qu'elles ne couvrent pas.",
         "Mettre le mode le plus permissif « pour aller vite » retire justement la couche qui rattrape les erreurs. Il se réserve aux environnements jetables."),
        ("10", "Choisir le bon mécanisme", "Chaque besoin a son bon support : la synthèse du parcours.",
         f"""<p>Vous connaissez maintenant sept mécanismes. Le piège classique est d'utiliser le mauvais : tout mettre dans <code>AGENTS.md</code>, ou espérer qu'une instruction tienne lieu d'interdiction. Un critère simple : <strong>à quelle fréquence l'agent en a-t-il besoin, et est-ce une suggestion ou une garantie ?</strong></p>
<table class="pc-table"><thead><tr><th>Besoin</th><th>Mécanisme</th><th>Coût pour le contexte</th></tr></thead><tbody>
<tr><td>Un fait valable dans toutes les sessions (commandes, pièges)</td><td><code>AGENTS.md</code></td><td>Toujours chargé</td></tr>
<tr><td>Une consigne propre à un sujet ou à un type de fichier</td><td>Règle, avec ou sans <code>paths</code></td><td>Au lancement, ou à la lecture d'un fichier concerné</td></tr>
<tr><td>Une procédure appelée pour une tâche</td><td>Skill</td><td>Description seule, corps à l'appel</td></tr>
<tr><td>Un travail de lecture volumineux ou une revue indépendante</td><td>Sous-agent</td><td>Fenêtre séparée, un résumé revient</td></tr>
<tr><td>Un accès à un service ou à des données (docs, navigateur, base)</td><td>Serveur MCP</td><td>Noms d'outils, définitions à la demande</td></tr>
<tr><td>Une interdiction ou une obligation qui ne doit jamais dépendre du modèle</td><td>Hook, règle de permission</td><td>Aucun, appliqué par l'outil</td></tr>
<tr><td>Partager le tout avec une équipe</td><td>Dépôt versionné, ou plugin qui regroupe skills, hooks, agents et serveurs</td><td>Selon ce qu'il contient</td></tr></tbody></table>
<p>Cas pratique : « les composants React se testent avec Testing Library, jamais avec Enzyme ». Où l'écrire ? Une règle avec <code>paths: src/**/*.tsx</code>, parce que cela ne concerne que ces fichiers. Et « ne jamais supprimer une migration » ? Un hook, parce que c'est une garantie.</p>
<p>Pour la gestion d'équipe, deux compléments existent : les <strong>plugins</strong> (un paquet installable qui regroupe skills, hooks, sous-agents et serveurs MCP) et les réglages gérés par l'organisation. Le parcours Harness montre comment l'ensemble s'assemble.</p>""",
         "Placer cinq consignes de votre projet dans le bon mécanisme, en justifiant le coût et la garantie.",
         "Une interdiction écrite dans AGENTS.md reste une demande polie : une garantie passe par un hook ou une règle de permission."),
    ]
    out = "\n".join(stage(*x) for x in s)
    return (intro("Du prompt isolé à un contexte entretenu : la session, les fichiers d'instructions, les règles, les skills, les agents, les serveurs MCP (dont Context7 et Playwright) et les permissions, avec les vrais fichiers de configuration. Les exemples sont des configurations valides, vérifiées à la génération de la page. Prérequis : le parcours Culture, ou une bonne pratique d'un assistant d'IA. Environ quatre heures, à calibrer en séance.") +
            nav(CONTEXTE_NAV) + out +
            checklist("Vous avez compris si vous savez", [
                "lister ce qui remplit la fenêtre d'une session d'agent, et la technique qui répond à chaque problème ;",
                "écrire des instructions vérifiables et dire pourquoi elles ne contraignent pas ;",
                "ranger une consigne au bon endroit : AGENTS.md, règle avec ou sans paths, skill ou hook ;",
                "écrire une skill, un sous-agent, et choisir leur emplacement ;",
                "configurer un serveur MCP sans secret en clair, avec la bonne portée ;",
                "prédire le résultat de règles deny, ask et allow, et nommer ce qu'elles ne garantissent pas ;",
                "brancher Context7 et Playwright et obtenir une évolution vérifiée par des captures ;",
                "choisir, pour une consigne donnée, entre AGENTS.md, règle, skill, sous-agent, MCP et hook."]) +
            sources([(DOC + "memory", "Instructions, mémoire et règles (CLAUDE.md, AGENTS.md, .claude/rules)"), (DOC + "skills", "Skills"), (DOC + "sub-agents", "Sous-agents"),
                     (DOC + "mcp", "MCP : portées et configuration"), ("https://github.com/upstash/context7", "Context7"), ("https://github.com/microsoft/playwright-mcp", "Playwright MCP"), (DOC + "best-practices", "Bonnes pratiques de Claude Code (sessions, vérification)"), (DOC + "features-overview", "Choisir entre skills, sous-agents, hooks et MCP"), (DOC + "permissions", "Permissions"),
                     ("https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents", "Effective context engineering for AI agents")]))


# ---------------------------------------------------------------------------------------------------------------------
# Parcours 3 : harness (introduction historique, puis pratique dans parcours.py)
# ---------------------------------------------------------------------------------------------------------------------

def history() -> str:
    rows = [
        ("1970", "Cycle séquentiel", "Les personnes, en phases successives", "Spécification et recette finales, revues de documents"),
        ("2001", "Méthodes agiles", "Les personnes, par petits lots", "Itérations courtes, tests, revue entre pairs"),
        ("2008 à 2010", "Pull requests, CI/CD, DevOps", "Les personnes, avec des machines qui vérifient", "Revue de code sur chaque changement, intégration continue, déploiement automatisé, branches protégées"),
        ("2021", "Complétion dans l'éditeur", "La personne, avec des suggestions", "Inchangé : la personne relit chaque ligne qu'elle accepte"),
        ("2022", "Assistant par conversation", "La personne, qui copie et colle", "Inchangé, mais le volume de texte relu augmente"),
        ("2024 à 2025", "Agents avec outils (MCP, terminal)", "Un agent, qui lit, modifie, lance et commit", "Les demandes d'autorisation de l'outil existent, mais elles ignorent votre processus et les règles de votre équipe"),
        ("Aujourd'hui", "Harness", "Un agent, dans un cadre", "Règles, gardes, skills, mémoire et preuve rebranchés autour de l'agent"),
    ]
    tr = "".join(f"<tr><td><b>{esc(a)}</b></td><td>{esc(b)}</td><td>{esc(c)}</td><td>{esc(d)}</td></tr>" for a, b, c, d in rows)
    return f"""<section class="pc-stage" id="etape-0"><div class="pc-main"><p class="pc-kicker">Introduction</p>
<h2 class="pc-h">D'où vient le harness</h2><p class="pc-tag">Le processus protégeait la qualité. L'agent l'a contourné par vitesse.</p>
<p>Pendant cinquante ans, la qualité d'un logiciel ne dépendait pas que du talent de chacun : elle venait d'un <strong>processus</strong> (spécifier, tester, relire, intégrer, déployer). Chaque époque a ajouté une couche de vérification. Un agent de code écrit et exécute plus vite que ce processus ne peut suivre : sans cadre, il décide et agit seul. Le <strong>harness</strong> est ce cadre : tout ce qui entoure le modèle pour qu'il travaille dans le processus, et non à côté.</p>
<table class="pc-table"><thead><tr><th>Époque</th><th>Pratique</th><th>Qui écrit</th><th>Ce qui protège la qualité</th></tr></thead><tbody>{tr}</tbody></table>
<p class="kd-note">Dates : repères généraux de l'histoire du génie logiciel (article de Royce en 1970, Manifeste agile en 2001, GitHub en 2008, GitHub Copilot en 2021, ChatGPT fin 2022, MCP fin 2024). La lecture « le harness rebranche le processus » est celle de Kwa, pas un consensus.</p>
<p>Chaque étape du processus d'équipe a donc son équivalent autour de l'agent :</p>
<table class="pc-table"><thead><tr><th>Étape du processus</th><th>Dans le harness (Kwa)</th></tr></thead><tbody>
<tr><td>Cadrer le besoin</td><td><code>/kwa-brainstorm</code>, <code>/kwa-plan</code></td></tr>
<tr><td>Ticket et branche dédiée</td><td><code>/kwa-start-dev</code> et <code>kwa-start</code></td></tr>
<tr><td>Tests d'abord</td><td><code>/kwa-tdd</code></td></tr>
<tr><td>Revue de code</td><td><code>/kwa-review</code>, retours traités par <code>/kwa-review-feedback</code></td></tr>
<tr><td>Branches protégées, pas de force-push</td><td>Gardes <code>guard-git</code>, <code>guard-write</code></td></tr>
<tr><td>Intégration continue</td><td><code>/kwa-verify</code>, vérifications de la politique</td></tr>
<tr><td>Pull request avec preuve</td><td><code>/kwa-ship</code>, <code>guard-github</code></td></tr>
<tr><td>Déploiement vérifié</td><td><code>/kwa-deploy</code></td></tr>
<tr><td>Rétrospective</td><td><code>/kwa-learn</code>, mémoire de session</td></tr></tbody></table>
<div class="pc-proof"><div><b>Preuve attendue</b><p>Placer cinq étapes de votre processus actuel et dire ce qui les remplace quand un agent travaille.</p></div><div><b>Piège</b><p>Un harness rend vérifiables par une machine des contrôles que l'équipe faisait déjà ; il ne doit pas en ajouter par réflexe.</p></div></div></div></section>"""


def harness(practice_html: str) -> str:
    return (intro("De l'histoire du processus de développement jusqu'à un harness complet, puis dix étapes sur un dépôt jetable, avec les vrais gardes : les sorties affichées sont celles de l'exécution, recalculées à chaque génération du site. Prérequis : les parcours Culture et Contexte, Python 3, git, un terminal. Aucun compte, aucune clé. Environ quatre heures, à calibrer en séance.") +
            nav(HARNESS_NAV) +
            history() + practice_html)


# ---------------------------------------------------------------------------------------------------------------------
# Accueil des parcours
# ---------------------------------------------------------------------------------------------------------------------

def hub() -> str:
    cards = [
        ("1", "Culture IA générative", "parcours-culture.html", "Environ 2 h 30",
         "Ce qu'est un modèle, les jetons et les probabilités, la fenêtre de contexte, l'agent, les hallucinations, le prompt engineering, les risques dont l'injection de prompt.",
         "Tout public. Aucun outil à installer."),
        ("2", "Context engineering", "parcours-contexte.html", "Environ 4 h",
         "Le contexte et la session, AGENTS.md, les règles, les skills, les sous-agents, MCP avec Context7 et Playwright, les permissions, et comment choisir.",
         "Avoir utilisé un assistant d'IA. Un terminal est un plus."),
        ("3", "Harness", "parcours-harness.html", "Environ 4 h",
         "De l'histoire du processus de développement jusqu'à Kwa : gardes, événements de hooks, politique, skills, mémoire, workflow, et le flux complet d'un développeur aujourd'hui.",
         "Les parcours 1 et 2, Python 3, git, un terminal."),
    ]
    c = "".join(
        f'<a class="pc-card" data-acc="{u[9:-5]}" href="{u}"><p class="pc-kicker">Parcours {n}</p><h2>{esc(t)}</h2><p class="pc-tag">{esc(d)}</p><p>{esc(txt)}</p><p class="kd-note">{esc(pre)}</p></a>'
        for n, t, u, d, txt, pre in cards)
    return (intro("Trois parcours qui s'enchaînent : comprendre le modèle, apprendre à lui donner le bon contexte, puis l'encadrer avec un harness. Chacun se lit seul, mais l'ordre est celui d'une progression. Les durées sont des estimations de conception, à ajuster après une première séance.") +
            f'<div class="pc-cards">{c}</div>' +
            checklist("Comment les utiliser", [
                "En autoformation : comptez une demi-journée par parcours, en faisant les exercices.",
                "En séance : chaque étape a une preuve attendue, que l'animateur peut demander à chaque participant.",
                "Les parcours 2 et 3 s'appuient sur de vrais fichiers de configuration et de vraies commandes : testez-les sur une copie avant de les projeter."]))
