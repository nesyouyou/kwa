"""Page « Le Mod » : le mod kwa-activity (mods/kwa-activity), qui dessine le workflow en cours et le coût de la session.

Les couleurs et les états décrits ici sont ceux de mods/kwa-activity/hooks/workflow.ts ; un test vérifie que les
libellés cités y figurent toujours. L'aperçu (assets/mod-apercu-*.svg) est le dessin que produit ce code, régénéré
par `npx tsx docs/site/src/mod_apercu.ts docs/site/assets` : ce n'est pas une capture d'écran.
"""
from __future__ import annotations

from parcours import code

INSTALL = "/plugin install kwa-activity@kwa"
TOGGLE = "/kwa-activity"
# libellés repris tels quels du dessin (mods/kwa-activity/hooks/workflow.ts)
LABELS = ["en cours", "passée", "refusé", "interrompue", "en parallèle", "Fenêtre de contexte", "modifie", "lance"]

STATES = [  # (pastille, nom, ce que ça veut dire)
    ("pn-done", "Faite", "L'étape a eu lieu et s'est terminée : coche verte et sa durée."),
    ("pn-run", "En cours", "La boîte est teintée et sa bordure pulse ; son chronomètre est sous le schéma."),
    ("pn-spin", "Sous-agent", "Un moulinet tourne tant qu'il travaille ; plusieurs agents d'une brique font une seule boîte « ×N »."),
    ("pn-deny", "Refusée", "Un garde de Kwa a refusé l'action : boîte rouge et croix. Dix refus du même garde font une boîte « ×10 »."),
    ("pn-pass", "Passée", "Une étape du parcours type qui précède une étape atteinte, sans trace : une validation, un hook."),
    ("pn-next", "À venir", "Cercle vide et cadre en pointillés."),
]

TOOLS = [  # (ce que fait l'outil, brique)
    ("Lire un fichier, chercher dans le code, consulter le web", "Cadrer"),
    ("Écrire ou modifier un fichier", "Faire"),
    ("Lancer une commande de vérification de la politique du projet, ou une commande de test ou de build connue "
     "(<code>unittest</code>, <code>pytest</code>, <code>jest</code>, <code>tsc</code>, <code>dotnet test</code>…)", "Prouver"),
    ("<code>git commit</code>, <code>git push</code>, ouvrir ou fusionner une PR", "Livrer"),
    ("Une autre commande (<code>ls</code>, <code>cat</code>…)", "aucune : elle s'affiche seulement en direct"),
]


def page() -> str:
    states = "".join(f'<li><span class="pn-dot {cls}" aria-hidden="true"></span><b>{name}</b><span>{what}</span></li>'
                     for cls, name, what in STATES)
    tools = "".join(f"<tr><td>{what}</td><td>{brick}</td></tr>" for what, brick in TOOLS)
    return f"""<p class="kw-lead">Le Mod affiche, à droite de la conversation, où en est la session : le workflow en
cours, brique par brique, ce que l'agent est en train de faire, les sous-agents qui tournent, la fenêtre de contexte
et le coût. C'est un mod de Claude Code, séparé du plugin : il observe la session et dessine, sans rien écrire dans le
contexte du modèle ni bloquer quoi que ce soit.</p>

<div class="pn-grid">
<figure class="pn-shot">
<img class="pn-img pn-dark" src="assets/mod-apercu-sombre.svg" width="348" height="945" loading="lazy" alt="">
<img class="pn-img pn-light" src="assets/mod-apercu-clair.svg" width="348" height="945" loading="lazy"
  alt="Le Mod pendant la correction d'un bug : rond « Bug » allumé, briques Cadrer et Faire faites, brique Prouver ouverte avec /kwa:tdd en cours et un sous-agent, briques Livrer et Capitaliser à venir, carte de la fenêtre de contexte à 38 %.">
<figcaption>Le dessin que produit le Mod pendant la correction d'un bug, généré par son code (pas une capture). Sous
le schéma, Desktop ajoute en texte la ligne « En direct », les chronomètres et le coût.</figcaption></figure>

<div class="pn-text">
<h2 class="kw-section-title">Ce qu'il montre</h2>
<ul class="pn-list">
<li><b>Les cinq workflows</b>, en haut : Feature, Bug, Relire, Livrer, Capitaliser. Celui qui est détecté s'allume.
La première skill Kwa de la session le désigne : <code>/kwa:debug</code> pour un bug, <code>/kwa:review</code> pour une
relecture, <code>/kwa:ship</code> ou <code>/kwa:commit</code> pour une livraison, <code>/kwa:learn</code> pour capitaliser.
Sans skill, la branche de la session le dit : <code>fix/…</code> pour un bug, <code>feat/…</code> pour une
fonctionnalité. Ce sont les cinq <a href="board.html">workflows animés</a> du site.</li>
<li><b>Une brique ouverte à la fois</b>, celle où l'on est. Les autres restent fermées, avec une pastille par étape.
Quand la session entre dans une nouvelle brique, elle se déplie.</li>
<li><b>En direct</b>, sous le schéma : la dernière action de l'agent ou d'un sous-agent, par exemple « modifie
panier.py · il y a 3 s », et le chronomètre de chaque étape en cours.</li>
<li><b>Les sous-agents qui tournent</b> : combien en ce moment, le pic en parallèle, et pour chacun son type et sa tâche.</li>
<li><b>La fenêtre de contexte</b> : un anneau vert sous 50 %, orange jusqu'à 80 %, rouge au-delà, avec le conseil qui
va avec (<code>/compact</code>, ou <a href="glossaire.html">passer le relais</a>). Puis le coût de la session, sa durée
et les jetons.</li>
</ul>

<h2 class="kw-section-title">Lire une étape</h2>
<ul class="pn-states">{states}</ul>
</div>
</div>

<h2 class="kw-section-title">Comment il sait où on en est</h2>
<p>Le Mod ne lit pas la conversation. Il reçoit les événements de la session au moment où ils se produisent, et en
déduit l'avancement :</p>
<ul class="pn-list">
<li><b>Une skill Kwa démarre</b> : c'est une étape, rangée dans sa brique (<code>debug</code> en Cadrer,
<code>tdd</code> en Prouver, <code>ship</code> en Livrer…). La première de la session désigne le workflow.</li>
<li><b>Un outil est appelé</b> : le Mod en déduit la brique, même sans skill.</li>
<li><b>Un sous-agent part ou revient</b> : il est compté. Le moteur confirme toutes les quatre secondes ceux qui ont
fini, au cas où leur fin n'aurait pas été signalée.</li>
<li><b>Un garde de Kwa refuse</b> : une étape rouge. L'action refusée n'a pas eu lieu, elle ne compte pas comme activité.</li>
<li><b>Un tour se termine</b> : l'étape en cours se clôt et le coût est relevé.</li>
</ul>
<p>Le Mod lit aussi le <b>journal d'activité</b> que les hooks de Kwa écrivent pour chaque session (module
<code>memory</code>, voir <a href="memoire.html">Mémoire</a>). Il y trouve la branche de la session, et ce qui s'est
passé avant lui : une session reprise ou un Mod installé en cours de route retrouve ses skills, ses sous-agents et ses
refus. Après un <code>/clear</code>, qui ouvre une nouvelle session dans le même processus, le Mod oublie l'ancienne et
repart du journal de la nouvelle. Sans journal (Kwa sans le module <code>memory</code>), il suit la session en direct
seulement. Pour relire une session terminée, ou celle d'un autre agent : <code>kwa activity</code>.</p>
<div class="kd-wrap"><table class="dg-table"><thead><tr><th>Ce que fait l'outil</th><th>Brique</th></tr></thead><tbody>{tools}</tbody></table></div>
<p>Puis il compare ce qu'il a vu au parcours type du workflow : ce qui est fait, en cours, passé ou à venir. Le
schéma est un dessin vectoriel (SVG) qui ne change qu'avec les étapes, pour ne pas clignoter ; tout ce qui bouge sans
cesse (chronomètres, coût, ligne en direct) est du texte natif de Claude Code, mis à jour en place.</p>

<h2 class="kw-section-title">Installer</h2>
<p>Le mod est dans la même marketplace que Kwa. Dans Claude Code, une fois la marketplace <code>kwa</code> ajoutée
(<a href="avant-de-commencer.html">Avant de commencer</a>) :</p>
{code(INSTALL)}
<p>Le Mod s'ouvre au démarrage de chaque session. La commande suivante le ferme ou le rouvre :</p>
{code(TOGGLE)}

<h2 class="kw-section-title">Selon l'endroit</h2>
<ul class="pn-list">
<li><b>Claude Desktop et l'application mobile</b> : le dessin animé ci-dessus, en thème clair ou sombre, et les textes
natifs dessous.</li>
<li><b>Terminal</b> : la même information en texte, briques numérotées et étapes en dessous, avec la ligne en direct et
un indicateur qui tourne. Quand le terminal est trop étroit pour l'afficher à droite, une ligne au-dessus du prompt la
remplace : la brique, l'étape, les sous-agents en cours et le coût.</li>
</ul>

<h2 class="kw-section-title">Ce qu'il ne fait pas</h2>
<ul class="pn-list">
<li>Il ne compte comme étapes que les skills de Kwa : une commande intégrée comme <code>/review</code> ou une skill de
projet n'en est pas une. Les outils qu'elles appellent, eux, sont suivis.</li>
<li>Le classement des outils est une déduction : un <code>cat</code> qui lit un fichier n'ouvre pas Cadrer, une commande
de test inconnue n'ouvre pas Prouver. Ajoutez-la aux <code>verify.commands</code> de la politique pour qu'il la reconnaisse.</li>
<li>Les validations par vous, les hooks silencieux et les étapes sautées ne laissent pas de trace : elles deviennent
« passées » dès qu'une étape suivante est atteinte, jamais « faites ».</li>
<li>Le coût affiché est celui que Claude Code calcule pour la session ; sur un abonnement, c'est une estimation, pas
une facture. Pour mesurer ce que coûte Kwa lui-même, voir <a href="alleger.html">Quand alléger</a>.</li>
</ul>
<p class="kd-note">Le code est dans <a href="https://github.com/nesyouyou/kwa/tree/main/mods/kwa-activity"><code>mods/kwa-activity</code></a>,
avec ses tests (<code>claude plugin test mods/kwa-activity</code>).</p>
"""
