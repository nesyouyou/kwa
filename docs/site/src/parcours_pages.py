"""Les trois parcours et leur page d'accueil.

Contenu écrit à la main à partir des documentations officielles (liens en bas de chaque parcours). Les exemples de
configuration sont validés au build : JSON valide, aucun secret en clair, en-têtes de skill et d'agent complets.
"""
from __future__ import annotations

import json
import re
import sys

from parcours import code, cmd, esc, pill, reveal, stage

CULTURE_NAV = [("1", "Le modèle"), ("2", "Les jetons"), ("3", "Le contexte"), ("4", "Les hallucinations"), ("5", "Le prompt"), ("6", "Usages")]
CONTEXTE_NAV = [("1", "Le contexte"), ("2", "AGENTS.md"), ("3", "Skills"), ("4", "Agents"), ("5", "MCP"), ("6", "Permissions")]
HARNESS_NAV = [("0", "L'histoire"), ("1", "Instructions"), ("2", "Un garde"), ("3", "Branchement"), ("4", "Politique"), ("5", "Une skill"), ("6", "Mémoire"), ("7", "Circuit"), ("8", "Limites")]
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
            f'<div><b>{esc(bad_title)}</b><pre class="kd-code" style="margin-top:10px;white-space:pre-wrap">{esc(bad)}</pre></div>'
            f'<div><b>{esc(good_title)}</b><pre class="kd-code" style="margin-top:10px;white-space:pre-wrap">{esc(good)}</pre></div></div>')


# ---------------------------------------------------------------------------------------------------------------------
# Parcours 1 : culture IA générative
# ---------------------------------------------------------------------------------------------------------------------

def culture() -> str:
    gauge = """<div class="pc-widget" id="ctx-gauge">
<div class="pc-presets"><span>Situations types</span>
<button type="button" class="kd-copy" data-ctx-preset="chat">Discussion courte</button>
<button type="button" class="kd-copy" data-ctx-preset="agent">Session d'agent</button>
<button type="button" class="kd-copy" data-ctx-preset="long">Session trop longue</button></div>
<div class="pc-fields">
<label>Consignes du système<input id="ctx-sys" type="number" min="0" step="500" value="6000"></label>
<label>Fichiers d'instructions<input id="ctx-rules" type="number" min="0" step="500" value="3000"></label>
<label>Définitions d'outils<input id="ctx-tools" type="number" min="0" step="500" value="12000"></label>
<label>Historique de la conversation<input id="ctx-hist" type="number" min="0" step="1000" value="30000"></label>
<label>Fichiers lus<input id="ctx-files" type="number" min="0" step="1000" value="40000"></label>
<label>Résultats d'outils<input id="ctx-res" type="number" min="0" step="1000" value="25000"></label>
<label>Taille de la fenêtre<select id="ctx-win"><option value="200000">200 000</option><option value="1000000">1 000 000</option></select></label>
</div>
<div class="pc-actions"><button type="button" class="kd-copy" data-ctx-play>Simuler une session d'agent</button>
<button type="button" class="kd-copy" data-ctx-compact>Compacter</button></div>
<div class="pc-stack" id="ctx-stack"><i id="seg-sys"></i><i id="seg-rules"></i><i id="seg-tools"></i><i id="seg-hist"></i><i id="seg-files"></i><i id="seg-res"></i></div>
<ul class="pc-legend"><li><i class="pc-k0"></i>Consignes</li><li><i class="pc-k1"></i>Instructions</li><li><i class="pc-k2"></i>Outils</li><li><i class="pc-k3"></i>Historique</li><li><i class="pc-k4"></i>Fichiers lus</li><li><i class="pc-k5"></i>Résultats</li></ul>
<p id="ctx-txt" class="pc-big"></p><p id="ctx-msg"></p></div>"""
    tok = """<div class="pc-widget"><label class="pc-lbl" for="tok-input">Collez un texte de votre travail (il reste dans votre navigateur)</label>
<textarea id="tok-input" rows="5" placeholder="Un paragraphe d'un rapport, un e-mail, une page de documentation..."></textarea>
<p class="pc-hint">Découpage illustratif : un vrai modèle coupe autrement.</p>
<div id="tok-chips" class="pc-chips" aria-hidden="true"></div>
<div class="pc-actions"><button type="button" class="kd-copy" id="tok-replay">Rejouer l'animation</button></div>
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
<p>Estimez les jetons d'un de vos textes. Le résultat est un <strong>ordre de grandeur</strong> : le vrai compte dépend du modèle, et l'API propose un compteur exact (voir les sources).</p>""" + tok,
         "Donner l'ordre de grandeur d'un document de votre travail en jetons, et dire ce qui le rend plus ou moins gros.",
         "Compter en pages ou en mots donne une idée, jamais le chiffre : deux textes de même longueur peuvent coûter des jetons différents."),
        ("3", "La fenêtre de contexte", "Tout ce que le modèle peut voir à un instant donné, et rien d'autre.",
         """<p>La fenêtre de contexte est la « mémoire de travail » du modèle : <strong>tout</strong> ce qu'il peut consulter pour répondre, sa réponse comprise. Elle contient bien plus que votre dernier message : consignes du système, fichiers d'instructions, définitions des outils, historique de la conversation, fichiers lus, résultats des outils. Le modèle n'a pas de mémoire en dehors de cette fenêtre : une nouvelle session repart de zéro.</p>
<p>Plus grande ne veut pas dire meilleure. À mesure que le contexte grossit, la précision et le rappel peuvent baisser : c'est ce que la documentation appelle <em>context rot</em>. Choisir ce qui entre compte autant que la place disponible.</p>
<p>Remplissez la jauge, puis essayez les trois situations types.</p>""" + gauge,
         "Citer ce qui occupe une fenêtre en dehors de votre message, et dire pourquoi la remplir n'est pas un but.",
         "Les valeurs de la jauge sont des exemples pour comprendre, pas des mesures. Une interface de chat peut aussi faire glisser la conversation en oubliant les débuts."),
        ("4", "Les hallucinations", "Un texte faux dit avec assurance.",
         """<p>Un modèle peut produire une affirmation fausse ou une source qui n'existe pas, avec le même ton que le vrai. On parle d'<strong>hallucination</strong>. Elle ne se règle pas par une phrase magique : on la réduit par la manière de demander, puis on la contrôle.</p>
<p>Quatre leviers documentés :</p>
<ul class="pc-list">
<li><strong>Autoriser le « je ne sais pas »</strong> : dire explicitement qu'admettre l'incertitude est une bonne réponse.</li>
<li><strong>Citer d'abord</strong> : sur un long document, demander les passages exacts avant l'analyse, puis ne raisonner que sur eux.</li>
<li><strong>Exiger des citations</strong> pour chaque affirmation, et retirer celles qu'aucun passage ne soutient.</li>
<li><strong>Limiter aux documents fournis</strong> : interdire de s'appuyer sur ses connaissances générales.</li>
</ul>
<p>Réécrivez cette demande avec au moins deux leviers :</p>""" +
         pair("Avant", "Résume les risques juridiques de ce contrat et dis-moi ce qu'on doit négocier.", "Une version possible",
              "Voici le contrat entre <contrat> et </contrat>.\n1. Extrais d'abord les passages exacts qui parlent de responsabilité, de résiliation et de pénalités. Si tu n'en trouves pas, écris « aucun passage trouvé ».\n2. Analyse les risques en citant le numéro de chaque passage. N'utilise rien d'autre que ce contrat.\n3. Si un point te semble manquer, dis « je ne peux pas l'affirmer à partir du document ».") +
         reveal("Ce que ça ne règle pas", "<p>Ces techniques réduisent les hallucinations, elles ne les suppriment pas. Pour une décision importante, une personne relit les passages cités dans le document d'origine. Un chiffre, une date, une référence légale ou une citation s'écrivent dans un texte seulement après vérification à la source.</p>"),
         "Réécrire une demande pour qu'elle autorise l'incertitude et exige des passages, puis vérifier un passage cité à la main.",
         "Une réponse bien rédigée n'est pas une réponse vraie. Le ton d'assurance ne dit rien sur l'exactitude."),
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
         "Un prompt plus long n'est pas un meilleur prompt. Ajoutez ce qui manque au lecteur, pas ce qui rassure l'auteur."),
        ("6", "Usages responsables", "Ce qu'on n'envoie pas, ce qu'on vérifie, qui décide.",
         """<ul class="pc-list">
<li><strong>Données</strong> : ne pas coller de données personnelles, de secrets ni de données client réelles dans un outil que l'on ne maîtrise pas. Anonymiser ou fabriquer des exemples.</li>
<li><strong>Vérification</strong> : relire, contrôler les chiffres, les références et les citations à la source.</li>
<li><strong>Responsabilité</strong> : la décision et la signature restent humaines. Le modèle propose, la personne répond du résultat.</li>
<li><strong>Calcul</strong> : un montant, un total ou un contrôle s'obtiennent par un tableur ou un script vérifiable. Le modèle lit et rédige autour.</li>
</ul>
<p>Prochaine étape : passer d'un prompt isolé à un <strong>contexte entretenu</strong>, avec des fichiers, des skills et des outils. C'est le parcours suivant.</p>""",
         "Dire ce qu'on ne colle jamais dans un outil d'IA et qui répond du résultat.",
         "« C'est l'IA qui l'a dit » ne tient devant personne. La personne qui diffuse un texte en répond."),
    ]
    out = "\n".join(stage(*x) for x in s)
    return (intro("Six étapes pour comprendre ce que fait vraiment un modèle de langage : le texte, les jetons, la fenêtre de contexte, les erreurs, la manière de demander. Aucun outil à installer ; un outil d'IA au choix suffit pour les exercices. Environ deux heures, à calibrer en séance.") +
            nav(CULTURE_NAV) + out +
            checklist("Vous avez compris si vous savez", [
                "dire pourquoi un modèle produit du texte plausible sans consulter une base de faits ;",
                "estimer les jetons d'un texte et lister ce qui occupe une fenêtre de contexte ;",
                "expliquer pourquoi remplir la fenêtre ne rend pas la réponse meilleure ;",
                "réécrire une demande pour réduire le risque d'hallucination, puis vérifier à la source ;",
                "écrire une consigne qu'un collègue sans contexte pourrait exécuter."]) +
            sources([(API + "build-with-claude/context-windows", "Fenêtres de contexte (jetons, context rot, compaction)"),
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

SETTINGS_EX = {
    "permissions": {
        "allow": ["Bash(npm test *)", "Bash(git status)"],
        "ask": ["Bash(git push *)"],
        "deny": ["Read(./.env)", "Read(./secrets/**)", "Bash(rm -rf *)"],
    }
}


def parse_front(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        sys.exit("parcours : en-tête manquant dans un exemple de skill ou d'agent")
    return {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in m.group(1).splitlines() if ":" in l)}


def contexte() -> str:
    # contrôles du build : les exemples doivent être corrects
    for must in ("name", "description"):
        if must not in parse_front(SKILL_EX) or must not in parse_front(AGENT_EX):
            sys.exit(f"parcours : exemple sans {must}")
    mcp_json = json.dumps(MCP_EX, indent=2, ensure_ascii=False)
    settings_json = json.dumps(SETTINGS_EX, indent=2, ensure_ascii=False)
    for payload in (mcp_json, settings_json):
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
         """<p>Le <strong>context engineering</strong> est l'ensemble des moyens qui curent et entretiennent ce qui se trouve dans le contexte du modèle pendant le travail : consignes, outils, données externes, historique. Le prompt n'en est qu'une partie. L'objectif tient en une phrase : le plus petit ensemble d'informations très utiles qui produit le résultat voulu.</p>
<p>Dans une session d'agent de code, ce qui entre dans la fenêtre vient de six endroits : les consignes du système, vos fichiers d'instructions, les définitions des outils (y compris ceux des serveurs MCP), la liste des skills, l'historique, et les résultats des outils. Quatre techniques gardent le contexte sain, et chacune a son pendant dans l'outil :</p>
<table class="pc-table"><thead><tr><th>Technique</th><th>Dans Claude Code</th></tr></thead><tbody>
<tr><td>Charger à la demande plutôt que tout précharger</td><td>Une skill n'entre en entier que lorsqu'elle est appelée ; l'agent lit les fichiers au moment du besoin</td></tr>
<tr><td>Résumer quand la fenêtre se remplit</td><td>La compaction de la conversation</td></tr>
<tr><td>Écrire des notes hors de la fenêtre</td><td>Les fichiers d'instructions, la mémoire automatique, les notes de session</td></tr>
<tr><td>Déléguer à un contexte propre</td><td>Les sous-agents, qui renvoient un résumé</td></tr></tbody></table>
<p>Retournez à la jauge du parcours précédent, préréglage « Session d'agent », et repérez les deux postes que vous contrôlez le mieux.</p>""",
         "Nommer les six sources du contexte d'une session d'agent et associer une technique à chacun de ses problèmes.",
         "Ajouter des informations « au cas où » alourdit le contexte. Ce qui n'aide pas la tâche la dessert."),
        ("2", "Les fichiers d'instructions", "CLAUDE.md et AGENTS.md : du contexte persistant, pas une contrainte.",
         """<p>Chaque session démarre avec une fenêtre vide. Deux mécanismes transmettent la connaissance d'une session à l'autre : les fichiers d'instructions que <strong>vous</strong> écrivez (<code>CLAUDE.md</code>, ou <code>AGENTS.md</code> que Claude Code peut lire à la place), et la <strong>mémoire automatique</strong> que Claude écrit lui-même d'après vos corrections.</p>
<p>Deux faits à retenir. D'abord, ces fichiers sont du <strong>contexte</strong> : l'agent les lit et peut s'en écarter. Pour interdire une action quelle que soit sa décision, il faut un hook (parcours suivant). Ensuite, plus une instruction est précise et courte, plus elle est suivie de manière constante.</p>
<p>Le projet de ce site utilise un seul fichier commun et un pointeur : <code>AGENTS.md</code> porte les règles, <code>CLAUDE.md</code> contient une ligne <code>@AGENTS.md</code>. Des règles par type de fichier peuvent vivre dans <code>.claude/rules/</code>.</p>
<p>Lequel de ces deux fichiers est le plus utile à un agent qui arrive sur le projet ?</p>""" +
         pair("Fichier A", AGENTS_BAD, "Fichier B", AGENTS_GOOD) +
         reveal("Réponse", "<p>Le B. Il contient ce que l'agent ne peut pas deviner en lisant le code : les commandes de vérification, les pièges, ce qui est interdit. Le A dit des intentions que n'importe quel modèle suit déjà (« écris du code propre ») sans rien de vérifiable. Une bonne instruction se teste : on peut dire si elle a été suivie.</p>") +
         "<p><strong>Exercice</strong> : écrivez dix lignes d'<code>AGENTS.md</code> pour un projet que vous connaissez, avec uniquement des commandes, des pièges et des interdits.</p>",
         "Produire dix lignes d'instructions vérifiables, et expliquer pourquoi elles ne remplacent pas un garde-fou.",
         "Un fichier trop long ou contradictoire dilue ce qui compte. Deux sources qui se contredisent valent pire qu'une seule."),
        ("3", "Les skills", "Une procédure chargée seulement quand elle sert.",
         f"""<p>Une skill est un dossier avec un fichier <code>SKILL.md</code> : un en-tête qui dit <strong>quand</strong> l'appeler, un corps qui dit <strong>comment</strong>. Claude l'invoque quand la description correspond à la conversation, ou vous la tapez avec <code>/nom</code>.</p>
{code(SKILL_EX)}
<p>Le point clé est le <strong>chargement progressif</strong> : seule la description reste toujours dans le contexte ; le corps n'est lu qu'à l'appel, et les fichiers annexes seulement au besoin. Une skill volumineuse ne coûte donc rien tant qu'on ne s'en sert pas.</p>
<table class="pc-table"><thead><tr><th>Emplacement</th><th>Portée</th></tr></thead><tbody>
<tr><td><code>~/.claude/skills/&lt;nom&gt;/SKILL.md</code></td><td>Personnel : tous vos projets</td></tr>
<tr><td><code>.claude/skills/&lt;nom&gt;/SKILL.md</code></td><td>Ce dépôt, partagé en le versionnant</td></tr>
<tr><td>Plugin</td><td>Là où le plugin est activé</td></tr></tbody></table>
<p>Champs utiles : <code>disable-model-invocation: true</code> pour ne la lancer que par commande, <code>allowed-tools</code> pour pré-autoriser des outils pendant son exécution.</p>
<p><strong>Exercice</strong> : transformez une tâche que vous répétez (relance, compte rendu, revue) en skill. Écrivez d'abord la description : elle doit dire quand, jamais le déroulé.</p>""",
         "Écrire une skill dont la description déclenche au bon moment et dont le corps tient en dix lignes.",
         "Une description qui résume les étapes pousse l'agent à les suivre sans lire le corps. Elle sert à choisir, pas à exécuter."),
        ("4", "Les agents", "Un second collaborateur avec sa propre fenêtre de contexte.",
         f"""<p>Un <strong>sous-agent</strong> est un assistant spécialisé qui travaille dans une fenêtre de contexte isolée, avec ses propres consignes, ses propres outils et éventuellement un autre modèle. Il fait la tâche et ne renvoie qu'un résumé : la lecture de trente fichiers ne pollue pas la conversation principale. C'est la technique « déléguer à un contexte propre » du début du parcours.</p>
{code(AGENT_EX)}
<p>Le fichier vit dans <code>.claude/agents/</code> (projet) ou <code>~/.claude/agents/</code> (personnel). Les champs obligatoires sont <code>name</code> et <code>description</code> ; <code>tools</code> restreint ses outils (ici, lecture seule) et hérite de tout si on l'omet. On l'invoque en le nommant, par @-mention, ou pour toute la session.</p>
<p>Limites à connaître : chaque appel repart de zéro, il consomme du quota comme la session principale, et le nombre d'agents simultanés et la profondeur d'imbrication sont bornés.</p>
<p><strong>Exercice</strong> : écrivez un agent « relecteur » en lecture seule pour votre projet. Quelles sont les trois informations que vous lui donnez avec sa tâche, puisqu'il n'a pas votre conversation ?</p>""" +
         reveal("Piste", "<p>La demande d'origine et ses critères de réussite, le diff ou les fichiers touchés, et les résultats des vérifications déjà faites. Un agent ne voit que ce qu'on lui envoie : un résumé vague produit une relecture vague.</p>"),
         "Dire ce qu'un sous-agent gagne (un contexte propre) et ce qu'il perd (la conversation).",
         "Restreindre les outils est une protection réelle pour un relecteur. Un agent qui peut tout modifier relit mal ce qu'il peut aussi corriger."),
        ("5", "MCP : brancher des outils", "Un protocole commun pour donner à l'agent l'accès à des données et à des services.",
         f"""<p>Le <strong>Model Context Protocol</strong> permet à l'agent d'utiliser des serveurs externes : base de données, tracker, documentation, navigateur. Chaque serveur expose des outils que l'agent appelle. Deux conséquences : ils <strong>entrent dans le contexte</strong> (leurs définitions comptent dans la fenêtre) et ils <strong>peuvent agir</strong> (lire des données, écrire, supprimer). On n'installe donc que des serveurs de confiance, avec l'accès minimal.</p>
<table class="pc-table"><thead><tr><th>Portée</th><th>Visible</th><th>Stockée dans</th></tr></thead><tbody>
<tr><td>Locale (par défaut)</td><td>Ce projet, vous seul</td><td><code>~/.claude.json</code></td></tr>
<tr><td>Projet</td><td>Ce projet, toute l'équipe</td><td><code>.mcp.json</code> à la racine, versionné</td></tr>
<tr><td>Utilisateur</td><td>Tous vos projets, vous seul</td><td><code>~/.claude.json</code></td></tr></tbody></table>
<p>Un fichier <code>.mcp.json</code> de projet :</p>{code(mcp_json)}
<p>Remarquez les <code>${{...}}</code> : les secrets viennent de variables d'environnement, jamais du fichier versionné. Un serveur de portée projet demande une approbation avant son premier usage.</p>
{cmd("claude mcp add --transport http <nom> <url>")}{cmd("claude mcp list")}{cmd("claude mcp remove <nom>")}
<p>Dans les règles de permission, un outil MCP se nomme <code>mcp__&lt;serveur&gt;__&lt;outil&gt;</code> (par exemple <code>mcp__notion__.*</code> pour tous les outils d'un serveur).</p>
<p><strong>Exercice</strong> : écrivez le <code>.mcp.json</code> d'un serveur en lecture seule sur une base de test. Où va le mot de passe ?</p>""" +
         reveal("Réponse", "<p>Dans une variable d'environnement, référencée par <code>${NOM}</code>, définie hors du dépôt. Le fichier versionné ne contient aucun secret. Pour la base elle-même, un compte en lecture seule : la permission la plus étroite possible est la première protection.</p>"),
         "Choisir la bonne portée d'un serveur MCP et écrire sa configuration sans secret en clair.",
         "Un serveur MCP n'est pas une simple lecture : il agit avec vos droits. Chaque serveur ajouté alourdit aussi le contexte."),
        ("6", "Permissions et réglages", "Ce que l'agent peut faire, décidé hors de son texte.",
         f"""<p>Contrairement aux fichiers d'instructions, les <strong>règles de permission</strong> sont appliquées par l'outil, pas suggérées au modèle. Elles vivent dans les fichiers de réglages : <code>.claude/settings.json</code> (projet, partagé), <code>.claude/settings.local.json</code> (vos choix locaux, à garder hors du dépôt), <code>~/.claude/settings.json</code> (personnel), et des réglages d'organisation qui priment.</p>
{code(settings_json)}
<p>Trois listes, évaluées dans cet ordre : <strong>deny</strong>, puis <strong>ask</strong>, puis <strong>allow</strong>. La première qui correspond décide, quelle que soit la précision des règles. Pronostiquez :</p>
<table class="pc-table"><thead><tr><th>Cas</th><th>Résultat</th></tr></thead><tbody>{quiz_rows}</tbody></table>
<p>Les <strong>modes</strong> règlent le niveau d'autonomie : <code>default</code> (demande à la première utilisation), <code>acceptEdits</code> (accepte les modifications de fichiers), <code>plan</code> (explore sans modifier), <code>auto</code> (un classifieur vérifie les actions), <code>dontAsk</code> (refuse ce qui demanderait), <code>bypassPermissions</code> (aucune demande : réservé aux environnements isolés).</p>
<p><strong>Limite à connaître</strong> : une règle sur une commande shell lit le texte que l'agent écrit. Elle couvre la forme habituelle d'un appel, pas toutes ses variantes : ce n'est pas une frontière de sécurité autour d'un programme. Pour bloquer la lecture d'un fichier par les outils de fichiers, on écrit une règle <code>Read</code> sur son chemin.</p>
<p>Ce que les règles ne savent pas dire (« pas de commit sur main », « une PR doit être liée à une issue ») se règle avec des <strong>hooks</strong> : c'est l'objet du parcours Harness.</p>""",
         "Prédire le résultat d'un jeu de règles deny, ask et allow, et dire ce qu'elles ne couvrent pas.",
         "Mettre le mode le plus permissif « pour aller vite » retire justement la couche qui rattrape les erreurs. Il se réserve aux environnements jetables."),
    ]
    out = "\n".join(stage(*x) for x in s)
    return (intro("Du prompt isolé à un contexte entretenu : fichiers d'instructions, skills, agents, serveurs MCP et permissions, avec les vrais fichiers de configuration. Les exemples sont des configurations valides, vérifiées à la génération de la page. Prérequis : le parcours Culture, ou une bonne pratique d'un assistant d'IA. Environ trois heures, à calibrer en séance.") +
            nav(CONTEXTE_NAV) + out +
            checklist("Vous avez compris si vous savez", [
                "lister ce qui remplit la fenêtre d'une session d'agent, et la technique qui répond à chaque problème ;",
                "écrire des instructions vérifiables et dire pourquoi elles ne contraignent pas ;",
                "écrire une skill, un sous-agent, et choisir leur emplacement ;",
                "configurer un serveur MCP sans secret en clair, avec la bonne portée ;",
                "prédire le résultat de règles deny, ask et allow, et nommer ce qu'elles ne garantissent pas."]) +
            sources([(DOC + "memory", "Instructions et mémoire (CLAUDE.md, AGENTS.md)"), (DOC + "skills", "Skills"), (DOC + "sub-agents", "Sous-agents"),
                     (DOC + "mcp", "MCP : portées et configuration"), (DOC + "permissions", "Permissions"),
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
    return f"""<section class="pc-stage" id="etape-0"><div class="pc-num">0</div><div class="pc-main">
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
<div class="pc-proof"><div><b>Preuve attendue</b><p>Placer cinq étapes de votre processus actuel et dire ce qui les remplace quand un agent travaille.</p></div><div><b>Piège</b><p>Un harness n'ajoute pas de la bureaucratie : il rend vérifiables par une machine des contrôles que l'équipe faisait déjà.</p></div></div></div></section>"""


def harness(practice_html: str) -> str:
    return (intro("De l'histoire du processus de développement jusqu'à un harness complet, puis huit étapes pratiques sur un dépôt jetable, avec les vrais gardes : les sorties affichées sont celles de l'exécution, recalculées à chaque génération du site. Prérequis : les parcours Culture et Contexte, Python 3, git, un terminal. Aucun compte, aucune clé. Environ trois heures et demie, à calibrer en séance.") +
            nav(HARNESS_NAV) +
            history() + practice_html)


# ---------------------------------------------------------------------------------------------------------------------
# Accueil des parcours
# ---------------------------------------------------------------------------------------------------------------------

def hub() -> str:
    cards = [
        ("1", "Culture IA générative", "parcours-culture.html", "Environ 2 h",
         "Ce qu'est un modèle, les jetons, la fenêtre de contexte, les hallucinations, le prompt engineering, les usages responsables.",
         "Tout public. Aucun outil à installer."),
        ("2", "Context engineering", "parcours-contexte.html", "Environ 3 h",
         "Le contexte d'un agent, AGENTS.md et CLAUDE.md, les skills, les sous-agents, MCP avec ses fichiers de configuration, les permissions.",
         "Avoir utilisé un assistant d'IA. Un terminal est un plus."),
        ("3", "Harness", "parcours-harness.html", "Environ 3 h 30",
         "De l'histoire du processus de développement jusqu'à Kwa : gardes, branchement, politique, skills, mémoire, circuit, limites.",
         "Les parcours 1 et 2, Python 3, git, un terminal."),
    ]
    c = "".join(
        f'<a class="pc-card" data-acc="{u[9:-5]}" href="{u}"><div class="pc-num">{n}</div><h2>{esc(t)}</h2><p class="pc-tag">{esc(d)}</p><p>{esc(txt)}</p><p class="kd-note">{esc(pre)}</p></a>'
        for n, t, u, d, txt, pre in cards)
    return (intro("Trois parcours qui s'enchaînent : comprendre le modèle, apprendre à lui donner le bon contexte, puis l'encadrer avec un harness. Chacun se lit seul, mais l'ordre est celui d'une progression. Les durées sont des estimations de conception, à ajuster après une première séance.") +
            f'<div class="pc-cards">{c}</div>' +
            checklist("Comment les utiliser", [
                "En autoformation : comptez une demi-journée par parcours, en faisant les exercices.",
                "En séance : chaque étape a une preuve attendue, que l'animateur peut demander à chaque participant.",
                "Les parcours 2 et 3 s'appuient sur de vrais fichiers de configuration et de vraies commandes : testez-les sur une copie avant de les projeter."]))
