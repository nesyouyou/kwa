"""Arborescence de ce que Kwa installe dans un projet (et du dépôt de Kwa), générée à partir du manifeste.

Chaque fichier a une description d'une ligne, un type (couleur), les modules qui l'installent, un lien vers son code source
et, pour les skills et les hooks, un lien vers la carte. Rien n'est écrit à la main sauf les descriptions : un test vérifie
qu'aucun fichier n'en manque et que les liens vers la carte pointent vers des nœuds qui existent.
"""
from __future__ import annotations

import html
import os
import re

import pictos

REPO = "https://github.com/nesyouyou/kwa"

HOOK_NODE = {  # fichier de hook ou de garde -> nœud de la carte
    "guard-secrets.py": "g:secrets", "guard-git.py": "g:git", "guard-delete.py": "g:delete", "guard-policy.py": "g:policy",
    "guard-github.py": "g:github", "guard-write.py": "g:write", "skills-router.py": "h:router", "memory-context.py": "h:memctx",
    "format-after-edit.py": "h:format", "verify-stop.py": "h:verify", "memory-nudge.py": "h:nudge", "signal-prompt.py": "h:signal",
    "journal-compact.py": "h:compact", "journal-end.py": "h:end",
}

DESC = {  # fichiers installés : une ligne chacun
    "guard-secrets.py": "Refuse de lire .env, clés SSH, jetons et trousseau.",
    "guard-git.py": "Pas de commit ni de push sur main ; push forcé refusé ; push de branche confirmé.",
    "guard-delete.py": "Suppression récursive hors du dépôt ou à cible calculée : refus ou demande.",
    "guard-write.py": "Pas de code produit sur main, pas de secret en clair ; demande avant de toucher à .claude/kwa/.",
    "guard-policy.py": "Applique les règles bash.deny et bash.ask de la politique du projet.",
    "guard-github.py": "Une PR doit porter « Closes #N » ; fusion refusée sans issue liée ni preuve.",
    "_kwa.py": "Briques communes des gardes : découpe des commandes, lecture de la politique.",
    "_journal.py": "Journal des sessions, signaux d'apprentissage et masquage des secrets.",
    "skills-router.py": "Injecte au démarrage la table « quand → skill », filtrée sur les skills installées.",
    "memory-context.py": "Reprise de session : dernière entrée du journal, état git, notes en attente.",
    "memory-nudge.py": "Demande le journal et invite à capitaliser, une seule fois par session.",
    "journal-compact.py": "Sauvegarde les faits de la session avant la compaction.",
    "journal-end.py": "Filet à la fermeture : écrit les faits d'une session non racontée.",
    "signal-prompt.py": "Range les « retiens : » et les corrections dans les notes, sans modèle.",
    "format-after-edit.py": "Formate seulement les fichiers nouveaux, signale les autres.",
    "verify-stop.py": "Refuse de rendre la main sur du rouge (opt-in).",
    "kwa-start": "Ouvre l'issue, la branche et le worktree du workflow.",
    "kwa-memory": "Notes, journal des sessions et digest pour /kwa-learn.",
    "kwa-hygiene": "Contrôle d'hygiène avant une remise (secrets, noms, mesures datées).",
    "router.md": "La table de routage des skills, injectée au démarrage.",
    "kwa-git-discipline.md": "Discipline git : branche de travail, commit et publication sur demande.",
    "kwa-writing-standard.md": "Format des commits, des branches et des pull requests.",
    "kwa-github-workflow.md": "Le workflow : issue, branche, preuve, pull request.",
    "kwa-remise-au-client.md": "Règle de remise à un client : les quatre tests avant de livrer un dépôt.",
    "pull_request_template.md": "Gabarit de PR : contexte, changements, vérification, risque.",
    "kwa-hygiene.yml": "Job CI du contrôle d'hygiène.",
    "kwa.hygiene.allow": "Exceptions datées au contrôle d'hygiène.",
}
SYNTHETIC = [  # fichiers créés par l'installeur ou par l'usage, pas copiés depuis le pack
    ("AGENTS.md", "doc", ["core"], "Source unique des instructions de l'agent. Kwa ne gère que son bloc entre marqueurs, le reste est à vous."),
    ("CLAUDE.md", "doc", ["core"], "Un simple pointeur vers AGENTS.md."),
    (".claude/settings.json", "config", ["core"], "Branche les hooks de Kwa sur les événements de Claude Code ; vos propres hooks restent."),
    (".claude/kwa.policy.json", "config", ["core"], "La politique du projet : commandes interdites, environnements, vérifications. Propriété du projet."),
    (".claude/kwa/state.json", "config", ["core"], "Version installée et empreintes des fichiers gérés, pour repérer les retouches locales."),
    (".claude/kwa/local/inbox.md", "local", ["memory"], "Notes d'apprentissage en attente de /kwa-learn. Local, jamais versionné."),
    (".claude/kwa/local/journal", "local", ["memory"], "Une entrée par session : faits git et huit lignes de récit."),
    (".claude/kwa/local/signals.jsonl", "local", ["memory"], "Refus de garde et corrections repérées. Local."),
    (".claude/kwa/local/sessions", "local", ["memory"], "Début et base git de chaque session."),
]
KIND_LABEL = {"skill": "Skill", "guard": "Garde", "hook": "Hook", "rule": "Règle", "bin": "Outil", "config": "Configuration",
              "doc": "Document", "local": "Local", "other": "Autre"}


def kind_of(dest: str) -> str:
    name = os.path.basename(dest)
    if "/skills/" in dest:
        return "skill"
    if "/hooks/" in dest:
        return "guard" if name.startswith("guard-") else "hook"
    if "/rules/" in dest:
        return "rule"
    if "/bin/" in dest:
        return "bin"
    if dest.endswith((".json", ".yml", ".allow")):
        return "config"
    return "doc" if dest.endswith(".md") else "other"


def first_sentence(text: str, limit: int = 120) -> str:
    text = re.sub(r"\s+", " ", text).strip().strip('"')
    cut = re.split(r"(?<=[.!?])\s", text, 1)[0]
    return cut if len(cut) <= limit else cut[: limit - 1].rstrip(" ,;:") + "…"


def describe(dest: str, catalog: dict[str, str]) -> str:
    name = os.path.basename(dest)
    m = re.match(r"^\.claude/skills/kwa-([a-z-]+)/(.*)$", dest)
    if m:
        return first_sentence(catalog.get(m.group(1), "")) if m.group(2) == "SKILL.md" else "Annexe de la skill, lue seulement quand elle est utile."
    if "/ISSUE_TEMPLATE/" in dest:
        return "Gabarit d'issue : constat, décisions, critères de réussite."
    return DESC.get(name, "")


def project_files(man: dict, module_files, catalog: dict[str, str]) -> list[dict]:
    """Tous les fichiers que les modules installent, fusionnés par chemin, plus les fichiers créés par l'installeur."""
    files: dict[str, dict] = {}
    for mod, spec in man.items():
        for src, f in module_files(spec):
            dest = f["dest"]
            node = files.setdefault(dest, {"dest": dest, "src": src, "modules": [], "kind": kind_of(dest)})
            node["modules"].append(mod)
    for dest, kind, mods, desc in SYNTHETIC:
        files[dest] = {"dest": dest, "src": "", "modules": mods, "kind": kind, "desc": desc}
    for dest, f in files.items():
        f.setdefault("desc", describe(dest, catalog))
    return sorted(files.values(), key=lambda f: f["dest"])


# --------------------------------------------------------------------------- rendu

ICONS = {
    "dir": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 6.5A1.5 1.5 0 0 1 4.5 5h4l2 2.5h9A1.5 1.5 0 0 1 21 9v8.5a1.5 1.5 0 0 1-1.5 1.5h-15A1.5 1.5 0 0 1 3 17.5z"/></svg>',
    "file": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 3.5h7l4 4v13h-11z"/><path d="M13.5 3.5v4h4"/></svg>',
}
ORDER = {"AGENTS.md": 0, "CLAUDE.md": 1, ".claude": 2, ".github": 3}


def _tree(files: list[dict]) -> dict:
    root: dict = {}
    for f in files:
        cur = root
        parts = f["dest"].split("/")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {"__dir__": True})
        cur[parts[-1]] = {"__file__": f}
    return root


def _mods(node) -> set[str]:
    if "__file__" in node:
        return set(node["__file__"]["modules"])
    out: set[str] = set()
    for k, v in node.items():
        if k != "__dir__":
            out |= _mods(v)
    return out


def _link(f: dict) -> str:
    links = []
    if f["src"]:
        links.append(f'<a class="tr-l" href="{REPO}/blob/main/{html.escape(f["src"])}" title="Code source dans le dépôt">source</a>')
    name = os.path.basename(f["dest"])
    node = None
    m = re.match(r"^\.claude/skills/kwa-([a-z-]+)/SKILL\.md$", f["dest"])
    if m:
        node = f"s:{m.group(1)}"
    elif name in HOOK_NODE and "/hooks/" in f["dest"]:
        node = HOOK_NODE[name]
    if node:
        links.append(f'<a class="tr-l" href="skill-map.html#view=pack&amp;node={html.escape(node)}" title="Voir dans la carte">carte</a>')
    return "".join(links)


def _render(name: str, node: dict, depth: int) -> str:
    if "__file__" in node:
        f = node["__file__"]
        mods = " ".join(sorted(f["modules"]))
        chips = "".join(f'<i class="tr-m">{html.escape(m)}</i>' for m in sorted(f["modules"]))
        icon = pictos.svg("agent") if name == "AGENTS.md" else pictos.svg({"skill": "sword", "guard": "shield", "hook": "hook"}[f["kind"]]) if f["kind"] in ("skill", "guard", "hook") else ICONS["file"]
        return (f'<div class="tr-row tr-file tr-k-{f["kind"]}" data-mod="{mods}">{icon}'
                f'<span class="tr-n">{html.escape(name)}</span><span class="tr-d">{html.escape(f["desc"])}</span>'
                f'<span class="tr-r">{chips}{_link(f)}</span></div>')
    kids = sorted((k for k in node if k != "__dir__"), key=lambda k: (ORDER.get(k, 9) if depth == 0 else 0, "__file__" in node[k], k))
    inner = "".join(_render(k, node[k], depth + 1) for k in kids)
    mods = " ".join(sorted(_mods(node)))
    is_local = name in ("local",) or name.startswith("local")
    return (f'<details class="tr-dir{" tr-local" if is_local else ""}" data-mod="{mods}"{" open" if depth == 0 and name == ".claude" else ""}>'
            f'<summary class="tr-row">{ICONS["dir"]}<span class="tr-n">{html.escape(name)}/</span></summary><div class="tr-kids">{inner}</div></details>')


def render_project(files: list[dict]) -> str:
    tree = _tree(files)
    kids = sorted(tree, key=lambda k: (ORDER.get(k, 9), "__file__" in tree[k], k))
    return "".join(_render(k, tree[k], 0) for k in kids)


REPO_TREE = [  # structure du dépôt de Kwa : (chemin, type, description)
    ("bin/kwa", "bin", "L'installeur : detect, install, status, doctor, recommend."),
    ("core/hooks", "guard", "Les gardes et les hooks, des scripts Python sans dépendance."),
    ("core/skills", "skill", "Une skill par dossier : SKILL.md et ses annexes."),
    ("core/rules", "rule", "Les règles communes copiées dans les projets."),
    ("core/bin", "bin", "kwa-start, kwa-memory, kwa-hygiene."),
    ("core/templates", "doc", "Bloc d'AGENTS.md, table de routage, gabarits GitHub."),
    ("manifest.json", "config", "Ce que chaque module installe, et les hooks qu'il branche."),
    ("credits.json", "config", "Les projets dont Kwa reprend des idées, avec licence et référence."),
    ("licenses", "doc", "Les textes de licence des projets crédités."),
    ("THIRD_PARTY_NOTICES.md", "doc", "Ce que Kwa doit aux autres projets, en clair."),
    ("examples", "config", "Exemples de politique de projet (monorepo web, API, mobile)."),
    ("profiles", "doc", "Le profil de flux (pr-flow)."),
    ("docs/specs", "doc", "Les spécifications des fonctionnalités."),
    ("docs/site", "doc", "Ce site : généré par build.py, avec de vraies sorties de gardes."),
    ("docs/gotchas.md", "doc", "Les pièges déjà rencontrés, pour ne pas les repayer."),
    ("tests", "config", "Les tests : gardes, installeur, skills, parcours, mémoire."),
]


PACK = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def render_repo() -> str:
    rows = []
    for path, kind, desc in REPO_TREE:
        isdir = os.path.isdir(os.path.join(PACK, path))
        icon = ICONS["dir"] if isdir else ICONS["file"]
        rows.append(f'<div class="tr-row tr-file tr-k-{kind}" data-mod="repo">{icon}<span class="tr-n">'
                    f'<a href="{REPO}/{"tree" if isdir else "blob"}/main/{html.escape(path)}">{html.escape(path)}{"/" if isdir else ""}</a></span>'
                    f'<span class="tr-d">{html.escape(desc)}</span></div>')
    return "".join(rows)


def section(files: list[dict], modules: list[str], about: dict | None = None) -> str:
    about = about or {}
    mod_chips = "".join(f'<button type="button" class="tr-chip" aria-pressed="true" data-m="{html.escape(m)}" data-about="{html.escape(about.get(m, ""))}">{html.escape(m)}</button>' for m in modules)
    legend = "".join(f'<li><i class="tr-key tr-k-{k}"></i>{KIND_LABEL[k]}</li>' for k in ("skill", "guard", "hook", "rule", "bin", "config", "doc", "local"))
    return f"""<section class="kw-container kd-section kd-rv" id="arborescence">
  <div class="kd-head"><div class="kd-eyebrow"><i class="kd-dot" style="--dot:var(--tr-config)"></i>Arborescence</div><h2 class="kw-section-title">Ce que Kwa installe dans un projet</h2>
    <p class="kd-lead">Ouvrez un dossier pour voir ce qu'il contient. Chaque ligne renvoie à son code source ; les skills et les gardes renvoient aussi à la carte. Décochez un module pour voir ce qui disparaît : on n'installe que ce qui sert.</p></div>
  <div class="tr" id="tree">
    <div class="tr-tabs" role="tablist"><button type="button" role="tab" aria-selected="true" data-tab="project">Dans votre projet</button><button type="button" role="tab" aria-selected="false" data-tab="repo">Dans le dépôt Kwa</button></div>
    <div class="tr-panel" data-panel="project">
      <div class="tr-bar"><div class="tr-mods" role="group" aria-label="Modules">{mod_chips}</div>
        <div class="tr-act"><button type="button" class="tr-btn" data-act="open">Tout ouvrir</button><button type="button" class="tr-btn" data-act="close">Tout replier</button></div></div>
      <p class="tr-modnote" id="tr-modnote">Survolez un module pour voir son rôle ; décochez-le pour voir ce qui disparaît.</p>
      <div class="tr-body">{render_project(files)}</div>
    </div>
    <div class="tr-panel" data-panel="repo" hidden><div class="tr-body">{render_repo()}</div></div>
    <ul class="tr-legend" aria-label="Légende des couleurs">{legend}</ul>
  </div>
</section>"""
