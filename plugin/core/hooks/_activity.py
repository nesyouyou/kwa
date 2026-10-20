"""Journal d'activité (module memory) : ce qui se passe dans une session, une ligne JSON par événement.

Un fichier par session dans `.claude/kwa/local/activity/` du dépôt principal : des sessions en parallèle, y compris
dans des worktrees, n'écrivent jamais dans le même fichier. Rien de versionné, rien qui quitte la machine, aucun
contenu de fichier ni de prompt : un nom d'outil, une brique, un chemin ou une commande tronqués et nettoyés.
Bibliothèque standard uniquement. Désactivé avec le journal (KWA_JOURNAL=0).
"""
from __future__ import annotations

import json
import os
import re
import time

from _journal import enabled, local_dir, scrub

SESSION_BYTES = 1024 * 1024        # plafond d'un fichier de session (environ 5 000 lignes)
TOTAL_BYTES = 20 * 1024 * 1024     # plafond du dossier : au-delà, les plus anciens partent
KEEP_DAYS = 30                     # durée de garde par défaut (memory.activity_days)
TARGET_CHARS = 120                 # longueur gardée d'un chemin ou d'une commande
# Toujours écrits, même au-delà du plafond : ce sont les étapes, pas le détail.
STEPS = {"session", "skill", "agent", "agent-end", "deny", "turn"}
_UNSAFE = re.compile(r"[^A-Za-z0-9_-]")


def activity_dir(root: str, create: bool = True) -> str:
    d = os.path.join(local_dir(root, create), "activity")
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def activity_days(policy: dict | None) -> int:
    try:
        return max(1, int(((policy or {}).get("memory") or {}).get("activity_days", KEEP_DAYS)))
    except (TypeError, ValueError):
        return KEEP_DAYS


def session_file(root: str, session: str, create: bool = True) -> str:
    """Le fichier de la session : celui qui existe déjà (une session qui passe minuit garde le sien), sinon un neuf
    daté du jour."""
    sid = _UNSAFE.sub("", session or "")[:64] or "sans-session"
    d = activity_dir(root, create)
    try:
        for name in os.listdir(d):
            if name.endswith(f"-{sid}.jsonl"):
                return os.path.join(d, name)
    except OSError:
        pass
    return os.path.join(d, f"{time.strftime('%Y-%m-%d')}-{sid}.jsonl")


def _short(value: object) -> str:
    text = scrub(" ".join(str(value).split()))
    return text if len(text) <= TARGET_CHARS else text[:TARGET_CHARS - 1] + "…"


def record(root: str, session: str, kind: str, agent: str = "claude", **fields: object) -> None:
    """Ajoute un événement au journal de la session. Jamais bloquant : une erreur d'écriture est ignorée.

    Au-delà du plafond d'un fichier, seules les étapes (STEPS) sont encore écrites ; les autres événements sont
    seulement comptés, par brique, dans `<fichier>.counts.json`."""
    if not enabled():
        return
    try:
        path = session_file(root, session)
        rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "ts": round(time.time(), 3), "kind": kind, "agent": agent}
        rec.update({k: _short(v) for k, v in fields.items() if v not in (None, "")})
        line = json.dumps(rec, ensure_ascii=False) + "\n"
        if kind not in STEPS and os.path.exists(path) and os.path.getsize(path) >= SESSION_BYTES:
            _count(path, str(fields.get("brick") or "autre"))
            return
        # une seule écriture d'une ligne courte en ajout : deux écrivains ne mêlent pas leurs lignes
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


# Ce que fait un appel d'outil, en une brique : la même lecture que le mod kwa-activity. Les noms d'outils de Codex
# (shell, apply_patch) et de Copilot (convertis en noms Claude quand ses hooks sont au format Claude) sont compris.
READ_TOOLS = {"Read", "NotebookRead", "Grep", "Glob", "LS", "WebFetch", "WebSearch", "view", "glob", "grep", "web_fetch"}
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch", "create", "edit"}
SHELL_TOOLS = {"Bash", "shell", "bash", "powershell"}
TEST = re.compile(r"\b(test|tests|pytest|unittest|jest|vitest|mocha|tsc|lint|eslint|typecheck|go test|cargo (test|check)"
                  r"|mvn (test|verify)|gradle (test|check)|dotnet (build|test))\b")
SHIP = re.compile(r"\b(git (commit|push|merge|tag)|gh pr (create|merge))\b")


def classify(tool: str, tool_input: dict, verify: list[str] | None = None, root: str = "") -> tuple[str, str]:
    """(brique, cible) d'un appel d'outil ; brique vide pour une commande qui ne relève d'aucune étape."""
    path = str(tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path") or "")
    if root and path.startswith(root.rstrip("/") + "/"):
        path = path[len(root.rstrip("/")) + 1:]
    if tool in READ_TOOLS:
        return "cadrer", path or str(tool_input.get("pattern") or tool_input.get("url") or tool_input.get("query") or "")
    if tool in WRITE_TOOLS:
        if tool == "apply_patch":
            m = re.search(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", str(tool_input.get("input") or tool_input.get("patch") or ""), re.M)
            path = m.group(1).strip() if m else path
        return "faire", path
    if tool in SHELL_TOOLS:
        cmd = tool_input.get("command") or ""
        cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if any(v and v in cmd for v in (verify or [])) or TEST.search(cmd):
            return "prouver", cmd
        if SHIP.search(cmd):
            return "livrer", cmd
        return "", cmd
    return "", ""


def _count(path: str, brick: str) -> None:
    counts_path = path + ".counts.json"
    try:
        with open(counts_path, encoding="utf-8") as f:
            counts = json.load(f)
    except (OSError, ValueError):
        counts = {}
    counts[brick] = int(counts.get(brick, 0)) + 1
    tmp = counts_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(counts, f)
    os.replace(tmp, counts_path)


def read_session(root: str, session: str) -> list[dict]:
    """Les événements d'une session, dans l'ordre ; une ligne illisible est ignorée."""
    return read_file(session_file(root, session, create=False))


def prune(root: str, policy: dict | None = None, now: float | None = None) -> int:
    """Supprime les fichiers de session plus vieux que la durée de garde, puis les plus anciens tant que le dossier
    dépasse son plafond. Renvoie le nombre de fichiers supprimés."""
    d = activity_dir(root, create=False)
    try:
        names = os.listdir(d)
    except OSError:
        return 0
    now = time.time() if now is None else now
    cutoff = now - activity_days(policy) * 86400
    files = []
    for name in names:
        p = os.path.join(d, name)
        if name.endswith(".jsonl") and os.path.isfile(p):
            files.append((os.path.getmtime(p), p))
    removed = 0
    files.sort()
    kept = []
    for mtime, p in files:
        if mtime < cutoff:
            removed += _remove(p)
        else:
            kept.append((mtime, p))
    total = sum(_size(p) for _, p in kept)
    for _, p in kept:
        if total <= TOTAL_BYTES:
            break
        total -= _size(p)
        removed += _remove(p)
    return removed


def _size(p: str) -> int:
    try:
        return os.path.getsize(p) + (os.path.getsize(p + ".counts.json") if os.path.exists(p + ".counts.json") else 0)
    except OSError:
        return 0


def _remove(p: str) -> int:
    try:
        os.unlink(p)
        if os.path.exists(p + ".counts.json"):
            os.unlink(p + ".counts.json")
        return 1
    except OSError:
        return 0


# --------------------------------------------------------------------------- lecture et résumé (kwa activity)

WORKFLOWS = {"feature": "Développer une fonctionnalité", "bug": "Corriger un bug", "review": "Relire", "ship": "Livrer",
             "learn": "Capitaliser"}
# la première skill Kwa de la session dit le workflow (même table que le mod) ; les autres skills n'en disent rien
FLOW_OF = {"debug": "bug", "review": "review", "review-feedback": "review", "commit": "ship", "ship": "ship",
           "deploy": "ship", "learn": "learn", "handoff": "learn"}
BRANCH_FLOW = {"fix": "bug", "hotfix": "bug", "feat": "feature", "feature": "feature"}
BRICKS = ["cadrer", "faire", "prouver", "relire", "livrer", "capitaliser"]
LIVE_SECONDS = 600   # une session dont le dernier événement a moins de dix minutes est dite en cours


def sessions(root: str) -> list[dict]:
    """Les sessions du projet, la plus récente d'abord : fichier, identifiant, date de dernière écriture."""
    d = activity_dir(root, create=False)
    out = []
    try:
        for name in os.listdir(d):
            if name.endswith(".jsonl"):
                p = os.path.join(d, name)
                out.append({"file": p, "session": name[11:-6], "mtime": os.path.getmtime(p)})
    except OSError:
        pass
    return sorted(out, key=lambda s: s["mtime"], reverse=True)


def workflow(events: list[dict]) -> tuple[str, str]:
    """(workflow, ce qui l'a désigné) : la première skill Kwa, sinon le préfixe de la branche, sinon une fonctionnalité."""
    for e in events:
        if e.get("kind") == "skill":
            name = str(e.get("name") or "").removeprefix("/").removeprefix("kwa:")
            return FLOW_OF.get(name, "feature"), f"skill {e.get('name')}"
    branch = next((str(e["branch"]) for e in events if e.get("branch")), "")
    prefix = branch.split("/", 1)[0] if "/" in branch else ""
    if prefix in BRANCH_FLOW:
        return BRANCH_FLOW[prefix], f"branche {branch}"
    return "feature", "par défaut"


def summarize(events: list[dict], counts: dict | None = None, now: float | None = None) -> dict:
    """Ce que dit le journal d'une session : workflow, branche et issue, étapes par brique, skills, sous-agents,
    refus, tours, durée, et si elle est encore en cours."""
    now = time.time() if now is None else now
    key, why = workflow(events)
    branch = next((str(e["branch"]) for e in events if e.get("branch")), "")
    issue = re.match(r"^[a-z]+/(\d+)-", branch)
    bricks = {b: 0 for b in BRICKS}
    for e in events:
        if e.get("kind") == "tool" and e.get("brick") in bricks:
            bricks[e["brick"]] += 1
    for b, n in (counts or {}).items():   # au-delà du plafond, les outils ne sont plus que comptés
        if b in bricks:
            bricks[b] += int(n)
    ts = [float(e["ts"]) for e in events if "ts" in e]
    return {
        "workflow": key, "title": WORKFLOWS[key], "why": why, "branch": branch,
        "issue": int(issue.group(1)) if issue else None,
        "agents": sorted({str(e.get("agent")) for e in events if e.get("agent")}),
        "skills": [str(e.get("name")) for e in events if e.get("kind") == "skill"],
        "bricks": bricks,
        "subagents": sum(1 for e in events if e.get("kind") == "agent"),
        "denials": [str(e.get("reason") or "") for e in events if e.get("kind") == "deny"],
        "turns": sum(1 for e in events if e.get("kind") == "turn"),
        "start": min(ts) if ts else None, "end": max(ts) if ts else None,
        "minutes": round((max(ts) - min(ts)) / 60) if ts else 0,
        "live": bool(ts) and now - max(ts) < LIVE_SECONDS,
    }


def read_counts(path: str) -> dict:
    try:
        with open(path + ".counts.json", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def read_file(path: str) -> list[dict]:
    out: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        pass
    return out
