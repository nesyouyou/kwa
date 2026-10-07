"""Données de la carte interactive : nœuds, vues, arêtes. Tout vient du contenu réel du pack.

- skills : frontmatter + sections `##` de chaque SKILL.md ; renvois /kata-* extraits du texte ;
- origines : credits.json (auteur, licence, avatar) ;
- gardes / hooks : manifeste et fichiers de core/hooks ;
- vues de workflow : positions et arêtes déclarées ici (le seul contenu écrit à la main), avec les textes de WF.
"""
from __future__ import annotations

import json
import os
import re

PACK = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SKILLS = os.path.join(PACK, "core", "skills")

AVATARS = {  # id de source (credits.json) -> avatar vendorisé
    "superpowers": ("assets/avatars/obra.jpg", "@obra"),
    "mattpocock": ("assets/avatars/mattpocock.png", "@mattpocock"),
    "ponytail": ("assets/avatars/DietrichGebert.png", "@DietrichGebert"),
    "super-board": ("assets/avatars/EricTechPro.jpg", "@EricTechPro"),
    "kata": ("assets/avatars/kata.svg", "Kata"),
}

KINDS = {
    "skill": "skill que l'agent invoque ou que tu tapes",
    "agent": "sous-agent lancé par une skill (outil Agent)",
    "hook": "hook déclenché tout seul par l'harnais",
    "garde": "garde PreToolUse : refuse ou demande",
    "humain": "porte où c'est toi qui décides",
    "policy": "fichier du projet lu par les skills et les gardes",
    "step": "étape interne d'une skill",
}

FAMILIES = {
    "cadrer": ["brainstorm", "interview", "plan", "tickets", "prototype", "questionnaire", "architecture", "rephrase"],
    "faire": ["start-dev", "tdd", "execute", "agents", "parallel", "simple"],
    "prouver": ["debug", "verify", "review", "review-feedback", "audit"],
    "livrer": ["commit", "ship", "deploy", "testflight"],
    "mémoire": ["learn", "handoff", "agent-docs"],
}
FAMILY_LABEL = {"cadrer": "Cadrer", "faire": "Faire", "prouver": "Prouver", "livrer": "Livrer", "mémoire": "Mémoire"}


DETAILS = {  # comment ça se comporte, par garde / hook
    "guard-secrets": "Analyse par segments de commande : bash -c, env, nice, .e''nv et sauts de ligne sont couverts. .env.example reste lisible.",
    "guard-git": "KATA_ALLOW_MAIN=1 pour une exception assumée. Les push de branche demandent confirmation selon git.push_branch de la politique.",
    "guard-delete": "Une cible calculée à l'exécution ($(…), variable) déclenche une demande plutôt qu'un passage.",
    "guard-policy": "Le refus l'emporte sur la demande. Un corps de heredoc non exécuté est une donnée, pas une commande.",
    "guard-github": "Lit la PR et ses issues via gh. Preuve = une image, ou une section « Preuve » réellement remplie.",
    "guard-write": "Demande aussi confirmation avant de toucher à .claude/kata/ ou settings.json.",
    "skills-router": "Court et calibré : une conversation simple n'appelle aucune skill. Les lignes dont la skill n'est pas installée sont retirées.",
    "memory-context": "Silencieux s'il n'y a rien. Propose de lancer /kata-learn, n'applique jamais rien seul.",
    "format-after-edit": "Un formatage global appartient à un lot dédié, pas à chaque sauvegarde.",
    "verify-stop": "Claude Code reprend la main après 8 blocages consécutifs : pas de boucle infinie.",
    "memory-nudge": "Seulement si 3 fichiers de code ou plus ont changé et qu'aucune note n'a été captée. Désactivable : KATA_MEMORY_NUDGE=0.",
}


def read(path: str) -> str:
    return open(path, encoding="utf-8").read()


def clean_md(t: str) -> str:
    t = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", t)
    t = re.sub(r"\*\*([^*]*)\*\*", r"\1", t)
    t = re.sub(r"`([^`]*)`", r"\1", t)
    return t.strip()


def paragraph(lines: list[str], start: int) -> str:
    """Premier paragraphe à partir de `start` : lignes consécutives jusqu'à une ligne vide ou un bloc (titre, tableau, code)."""
    out = []
    for l in lines[start:]:
        if not l.strip():
            if out:
                break
            continue
        if l.startswith(("#", "|", "```", ">")):
            if out:
                break
            continue
        out.append(clean_md(l))
    return " ".join(out)


def first_sentence(text: str, limit: int = 420) -> str:
    """Phrases entières jusqu'à `limit` caractères ; une phrase unique plus longue est coupée au dernier mot, avec « … »."""
    text = re.sub(r"`([^`]*)`", r"\1", re.sub(r"\*\*([^*]*)\*\*", r"\1", text)).strip()
    out = ""
    for part in re.split(r"(?<=[.!?])\s+", text):
        if out and len(out) + len(part) + 1 > limit:
            break
        out = f"{out} {part}".strip()
    if len(out) > limit:
        out = out[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"
    return out


def parse_skill(skill_id: str, credits: dict) -> dict:
    path = os.path.join(SKILLS, skill_id, "SKILL.md")
    text = read(path)
    fm = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    meta = {k.strip(): v.strip() for k, v in (l.split(":", 1) for l in fm.group(1).splitlines() if ":" in l)}
    body = fm.group(2)
    lines = body.splitlines()
    intro = ""
    for i, l in enumerate(lines):
        if l.startswith("# "):
            intro = paragraph(lines, i + 1)
            break
    sections = []
    in_code = False
    for i, l in enumerate(lines):
        if l.strip().startswith("```"):
            in_code = not in_code
        if not in_code and l.startswith("## "):
            sections.append({"title": l[3:].strip(), "text": first_sentence(paragraph(lines, i + 1), 320)})
    refs = sorted({m for m in re.findall(r"(?<![\w./-])/kata-([a-z]+(?:-[a-z]+)*)(?![\w/])", body) if m != skill_id})
    origins = [s["id"] for s in credits["sources"] if skill_id in s["skills"]] or ["kata"]
    annex = sorted(f for f in os.listdir(os.path.join(SKILLS, skill_id)) if f != "SKILL.md")
    return {
        "id": f"s:{skill_id}", "kind": "skill", "label": f"/kata-{skill_id}", "skill": skill_id,
        "what": first_sentence(intro or meta.get("description", "")),
        "when": meta.get("description", "").strip('"'),
        "how": " → ".join(s["title"] for s in sections[:7]),
        "source": [f"core/skills/{skill_id}/SKILL.md"] + [f"core/skills/{skill_id}/{a}" for a in annex],
        "origin": origins, "refs": [f"s:{r}" for r in refs], "sections": sections,
    }


def build(catalog_ids: list[str], credits: dict, wf_text: dict) -> dict:
    nodes: dict[str, dict] = {}
    for sid in catalog_ids:
        nodes[f"s:{sid}"] = parse_skill(sid, credits)

    def add(nid, kind, label, what, when="", how="", source=None, origin=None):
        nodes[nid] = {"id": nid, "kind": kind, "label": label, "what": what, "when": when, "how": how,
                      "source": source or [], "origin": origin or ["kata"], "refs": []}

    # gardes
    G = {
        "secrets": ("guard-secrets", "Refuse .env, clés SSH, jetons CLI, trousseau.", "PreToolUse · Bash, Read, Grep"),
        "git": ("guard-git", "Pas de commit ni de push sur main ; force refusé ; push de branche confirmé.", "PreToolUse · Bash"),
        "delete": ("guard-delete", "Refuse rm, find -delete, rsync --delete hors du projet, et .git / .claude/kata.", "PreToolUse · Bash"),
        "policy": ("guard-policy", "Applique bash.deny et bash.ask de la politique du projet.", "PreToolUse · Bash"),
        "github": ("guard-github", "« Closes #N » à la création d'une PR ; issue et preuve avant fusion.", "PreToolUse · Bash · module issue-flow"),
        "write": ("guard-write", "Secrets en clair, .env, migrations appliquées, pas de code sur main.", "PreToolUse · Edit, Write"),
    }
    for k, (label, what, when) in G.items():
        add(f"g:{k}", "garde", label, what, when, DETAILS.get(label, ""), [f"core/hooks/{label}.py"])
    H = {
        "router": ("skills-router", "Injecte la table « quand → skill », filtrée sur les skills installées.", "SessionStart · startup, clear, compact"),
        "memctx": ("memory-context", "Rappelle les notes d'apprentissage restées en attente.", "SessionStart"),
        "format": ("format-after-edit", "Formate seulement les fichiers nouveaux, signale les autres.", "PostToolUse · Edit, Write"),
        "verify": ("verify-stop", "Refuse de rendre la main sur du rouge (typecheck, lint).", "Stop · opt-in KATA_STOP_VERIFY=1"),
        "nudge": ("memory-nudge", "Une invitation à capitaliser, une seule par session.", "Stop · module memory"),
    }
    for k, (label, what, when) in H.items():
        add(f"h:{k}", "hook", label, what, when, DETAILS.get(label, ""), [f"core/hooks/{label}.py"])
    A = {
        "impl": ("Implémenteur", "Un agent frais par tâche, modèle choisi selon la difficulté.", "/kata-agents · outil Agent", "haiku pour le mécanique, sonnet pour l'intégration, opus pour la conception. Il ne commite pas et remonte tout refus de garde en BLOCKED.", ["core/skills/agents/implementer-prompt.md"]),
        "spec": ("Relecteur de conformité", "Le code fait-il exactement ce que la tâche demande, ni plus ni moins ?", "Après chaque tâche", "Agent neuf, jamais l'implémenteur. Passe avant la qualité.", ["core/skills/agents/spec-reviewer-prompt.md"]),
        "qual": ("Relecteur de qualité", "Lisibilité, tests, sécurité, simplicité, sur-ingénierie.", "Quand la conformité est verte", "Les retours critiques repartent vers l'implémenteur.", ["core/skills/agents/quality-reviewer-prompt.md"]),
        "rev": ("Relecteur de branche", "Revue de toute la branche : correction, sécurité, régressions, tests manquants.", "/kata-review · fin de plan", "Sortie de boucle : zéro critique et zéro important ouverts, sinon remontée après 3 tours.", ["core/skills/review/reviewer-prompt.md"]),
        "explore": ("Explore (lecture seule)", "Cartographie large du code concerné.", "Si le périmètre est vaste", "Sous-agent Explore : ne peut rien écrire.", []),
    }
    for k, (label, what, when, how, src) in A.items():
        add(f"a:{k}", "agent", label, what, when, how, src, ["superpowers"] if k in ("impl", "spec", "qual", "rev") else ["kata"])
    U = {
        "spec": ("Tu approuves la spec", "Porte d'approbation avant tout plan.", "", "Sans accord, on ne passe pas à /kata-plan."),
        "commit": ("Tu décides du commit", "/kata-commit puis /kata-ship, jamais sans ta demande.", "", "Un commit par changement logique ; push de branche confirmé ; fusion = décision séparée."),
        "go": ("Tu donnes le GO", "La fusion est une décision séparée.", "", "Kata annonce si elle déclenche un déploiement."),
        "preflight": ("Tu valides le pré-vol", "Chaque point du pré-vol est coché avec preuve, puis tu autorises le déploiement.", "", "Un point non vérifiable reste non coché : on n'avance pas."),
        "learn": ("Tu valides ce qu'on retient", "Tableau de 7 lignes maximum ; rien n'est appliqué sans « tout », « 1 et 3 » ou « rien ».", "", "« Rien à capitaliser » est une réponse valable."),
    }
    for k, (label, what, when, how) in U.items():
        add(f"u:{k}", "humain", label, what, when, how)
    add("p:policy", "policy", ".claude/kata.policy.json", "La politique du projet : commandes interdites, chemins protégés, vérifications, environnements.",
        "Créée une fois à partir de la détection, puis propriété du projet", "Lue par guard-policy, guard-write, /kata-verify, /kata-deploy, /kata-start-dev. Jamais écrasée par kata install.",
        ["examples/expo-monorepo.policy.json"])
    add("r:request", "humain", "Ta demande", "Tu écris. L'agent choisit la skill qui correspond.", "", "Les consignes d'AGENTS.md et les tiennes priment toujours sur une skill.")

    W, H_ = 280, 118  # pas de grille ; un nœud fait 224 × 92, l'écart laisse la place aux cadres et aux arêtes
    NW, NH = 224, 92

    def grp(label, c0, ncols, rows):
        """Cadre qui englobe vraiment ses nœuds : marge de 18 px autour, 56 px pour le titre en haut."""
        return {"label": label, "x": c0 * W - 18, "y": 8, "w": (ncols - 1) * W + NW + 36, "h": 48 + (rows - 1) * H_ + NH + 18}

    def pos(c, r, x0=0, y0=0):
        return {"x": x0 + c * W, "y": y0 + r * H_}

    views: dict[str, dict] = {}

    # --- vue d'ensemble du pack
    items, groups, edges = [], [], []
    colmap = {"cadrer": (0, 2), "faire": (2, 1), "prouver": (3, 1), "livrer": (4, 1), "mémoire": (5, 1)}
    for fam, ids in FAMILIES.items():
        c0, ncols = colmap[fam]
        for i, sid in enumerate(ids):
            if f"s:{sid}" not in nodes:
                continue
            if ncols == 2:
                items.append({"id": f"s:{sid}", **pos(c0 + i % 2, i // 2, 0, 56)})
            else:
                items.append({"id": f"s:{sid}", **pos(c0, i, 0, 56)})
        rows = (len(ids) + 1) // 2 if ncols == 2 else len(ids)
        groups.append(grp(FAMILY_LABEL[fam], c0, ncols, rows))
    # gardes et hooks : deux colonnes à droite, pour garder un plan large plutôt que haut
    for i, k in enumerate(["secrets", "git", "delete", "policy", "github", "write"]):
        items.append({"id": f"g:{k}", **pos(6, i, 0, 56)})
    groups.append(grp("Gardes · PreToolUse", 6, 1, 6))
    for i, k in enumerate(["router", "memctx", "format", "verify", "nudge"]):
        items.append({"id": f"h:{k}", **pos(7, i, 0, 56)})
    groups.append(grp("Hooks · Session, Stop", 7, 1, 6))
    items.append({"id": "p:policy", **pos(7, 5, 0, 56)})
    for a, b, kind in [("brainstorm", "plan", "calls"), ("interview", "brainstorm", "feeds"), ("plan", "start-dev", "calls"), ("plan", "execute", "calls"),
                       ("plan", "agents", "calls"), ("start-dev", "tdd", "calls"), ("tdd", "verify", "calls"), ("debug", "tdd", "calls"),
                       ("agents", "review", "calls"), ("verify", "commit", "calls"), ("review", "review-feedback", "calls"),
                       ("commit", "ship", "calls"), ("ship", "deploy", "calls"), ("deploy", "learn", "calls"), ("learn", "handoff", "feeds")]:
        edges.append({"from": f"s:{a}", "to": f"s:{b}", "kind": kind})
    edges.append({"from": "s:learn", "to": "s:brainstorm", "kind": "loop", "label": "la connaissance revient au cadrage"})
    views["pack"] = {"title": "Le pack Kata", "nodes": items, "groups": groups, "edges": edges,
                     "intro": "26 skills en 5 familles, gardes et hooks, politique du projet. Cliquer un nœud ; double-clic sur une skill pour ses étapes."}

    def flow(view_id, title, intro, seq, per_row=4, extra=None, loop=None):
        its, eds = [], []
        for i, nid in enumerate(seq):
            its.append({"id": nid, **pos(i % per_row, i // per_row, 0, 0)})
            if i:
                eds.append({"from": seq[i - 1], "to": nid, "kind": "calls"})
        for a, b, kind in (extra or []):
            eds.append({"from": a, "to": b, "kind": kind})
        if loop:
            eds.append({"from": loop[0], "to": loop[1], "kind": "loop", "label": loop[2]})
        views[view_id] = {"title": title, "intro": intro, "nodes": its, "groups": [], "edges": eds}

    flow("session", "Une session", "Ce qui se déclenche tout seul, dans l'ordre, de l'ouverture à la fermeture.",
         ["h:router", "h:memctx", "r:request", "g:secrets", "g:git", "g:delete", "g:policy", "g:github", "g:write", "h:format", "h:verify", "h:nudge"], per_row=4)
    flow("feature", "Une fonctionnalité", "De l'intention floue à la décision de commit : trois portes humaines, quatre sous-agents.",
         ["s:interview", "s:brainstorm", "u:spec", "s:plan", "s:start-dev", "a:impl", "a:spec", "a:qual", "s:verify", "a:rev", "u:commit"], per_row=4,
         loop=("a:qual", "a:impl", "retours critiques"))
    flow("bug", "Un bug", "Aucune correction avant la cause racine ; le correctif est prouvé en le retirant.",
         ["s:debug", "a:explore", "s:tdd", "s:simple", "s:verify", "h:nudge", "s:learn"], per_row=4)
    flow("delivery", "Livraison", "Du push à la production : chaque porte est un garde ou toi.",
         ["s:ship", "g:git", "g:github", "u:go", "s:deploy", "g:policy", "u:preflight", "s:learn", "u:learn"], per_row=4)

    # vues internes des skills : sections ## réelles
    for sid in catalog_ids:
        n = nodes[f"s:{sid}"]
        secs = n["sections"][:8]
        if not secs:
            continue
        its, eds = [], []
        for i, s in enumerate(secs):
            cid = f"t:{sid}:{i}"
            nodes[cid] = {"id": cid, "kind": "step", "label": s["title"], "what": s["text"] or "Détail dans la skill (tableau ou liste).", "when": "", "how": "",
                          "source": [f"core/skills/{sid}/SKILL.md"], "origin": ["kata"], "refs": []}
            its.append({"id": cid, **pos(i % 4, i // 4, 0, 0)})
            if i:
                eds.append({"from": f"t:{sid}:{i - 1}", "to": cid, "kind": "calls"})
        views[f"skill:{sid}"] = {"title": f"/kata-{sid}", "intro": n["what"], "nodes": its, "groups": [], "edges": eds, "parent": "pack"}
        n["child"] = f"skill:{sid}"
    for n in nodes.values():
        n.pop("sections", None)

    origins = {}
    for s in credits["sources"]:
        path, handle = AVATARS.get(s["id"], AVATARS["kata"])
        origins[s["id"]] = {"avatar": path, "handle": handle, "name": s["author"], "license": s["license"], "ref": s["ref"], "url": s["url"]}
    origins["kata"] = {"avatar": AVATARS["kata"][0], "handle": "Kata", "name": "Nakama", "license": "interne", "ref": "", "url": ""}
    return {"kinds": KINDS, "nodes": nodes, "views": views, "origins": origins, "start": "pack", "grid": {"w": 224, "h": 92}}
