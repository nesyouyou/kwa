"""Journal de sessions et signaux d'apprentissage (module memory). Bibliothèque standard uniquement.

Tout est local et jamais versionné : `.claude/kwa/local/` du dépôt principal (un worktree qui disparaît n'emporte donc
pas le journal). Aucun hook n'appelle un modèle. Désactivable : KWA_JOURNAL=0.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time

BUDGET = 2000          # caractères injectés au démarrage d'une session
BODY_LINES = 8         # lignes au plus dans le corps d'une entrée
STALE_DAYS = 14        # au-delà, une entrée est signalée comme ancienne
_DEADLINE = [0.0]      # échéance commune des appels git (SessionEnd dispose d'1,5 s au total)


def enabled() -> bool:
    return os.environ.get("KWA_JOURNAL") != "0"


# --------------------------------------------------------------------------- git, dossiers

def git(root: str, *args: str, timeout: float = 0.8) -> str:
    left = _DEADLINE[0] - time.time() if _DEADLINE[0] else timeout
    if left <= 0.05:
        return ""
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, timeout=min(timeout, left))
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def main_root(root: str) -> str:
    """Racine du dépôt principal : un worktree partage les notes de son dépôt, il ne les enterre pas avec lui."""
    common = git(root, "rev-parse", "--git-common-dir")
    if not common:
        return root
    common = os.path.realpath(common if os.path.isabs(common) else os.path.join(root, common))
    return os.path.dirname(common) if os.path.basename(common) == ".git" else root


def local_dir(root: str, create: bool = True) -> str:
    d = os.path.join(main_root(root), ".claude", "kwa", "local")
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def journal_dir(root: str, policy: dict | None = None, create: bool = True) -> str:
    custom = ((policy or {}).get("memory") or {}).get("journal_dir")
    d = os.path.join(root, custom) if custom else os.path.join(local_dir(root, create), "journal")
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def journal_days(policy: dict | None) -> int:
    try:
        return int(((policy or {}).get("memory") or {}).get("journal_days", 90))
    except (TypeError, ValueError):
        return 90


# --------------------------------------------------------------------------- masquage des secrets

_SECRETS = [
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}"), "Bearer [masqué]"),
    (re.compile(r"(?i)\b(api[_-]?key|token|secret|passw(?:or)?d|pwd|authorization|credentials?)s?\b(\s*[:=]\s*|\s+)(\"[^\"]*\"|'[^']*'|\S+)"), r"\1=[masqué]"),
    (re.compile(r"\b(?:sk|pk|rk)-[A-Za-z0-9_-]{12,}"), "[masqué]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), "[masqué]"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "[masqué]"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "[masqué]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "[masqué]"),
    (re.compile(r"://[^/\s:@]+:[^/\s@]+@"), "://[masqué]@"),
    (re.compile(r"\b[A-Fa-f0-9]{32,}\b"), "[masqué]"),
    (re.compile(r"\b[A-Za-z0-9_-]{40,}\b"), "[masqué]"),
]


def scrub(text: str) -> str:
    """Masque ce qui ressemble à un secret. En cas de clé privée, ne garde rien."""
    if re.search(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", text):
        return "[secret masqué]"
    for rx, repl in _SECRETS:
        text = rx.sub(repl, text)
    return text


# --------------------------------------------------------------------------- sessions

def _sid(payload: dict) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("session_id") or "")) or "inconnue"


def sessions_dir(root: str) -> str:
    d = os.path.join(local_dir(root), "sessions")
    os.makedirs(d, exist_ok=True)
    return d


def start_session(root: str, payload: dict) -> dict:
    """Enregistre la session (une seule fois : une compaction ou une reprise ne change ni son début ni sa base)."""
    sid = _sid(payload)
    path = os.path.join(sessions_dir(root), f"{sid}.json")
    try:
        with open(path, encoding="utf-8") as f:
            sess = json.load(f)
        os.utime(path)
        return sess
    except (OSError, ValueError):
        pass
    now = time.time()
    sess = {"id": sid, "started": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)), "ts": now,
            "head": git(root, "rev-parse", "HEAD"), "branch": git(root, "rev-parse", "--abbrev-ref", "HEAD"),
            "worktree": os.path.realpath(root)}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sess, f)
    return sess


def current_session(root: str) -> dict | None:
    """Pour la ligne de commande, qui ne connaît pas l'identifiant : la session la plus récente de ce dossier de travail."""
    wt = os.path.realpath(root)
    best = None
    try:
        names = os.listdir(sessions_dir(root))
    except OSError:
        return None
    for n in names:
        if not n.endswith(".json"):
            continue
        p = os.path.join(sessions_dir(root), n)
        try:
            with open(p, encoding="utf-8") as f:
                s = json.load(f)
            m = os.path.getmtime(p)
        except (OSError, ValueError):
            continue
        w = s.get("worktree", "")
        if (w == wt or wt.startswith(w + os.sep) or w.startswith(wt + os.sep)) and (best is None or m > best[0]):
            best = (m, s)
    return best[1] if best else None


# --------------------------------------------------------------------------- faits git

def facts(sess: dict) -> dict:
    wt = sess.get("worktree") or os.getcwd()
    head = sess.get("head", "")
    branch = git(wt, "rev-parse", "--abbrev-ref", "HEAD") or sess.get("branch", "")
    commits = [x for x in git(wt, "log", "--format=%h %s", f"{head}..HEAD").splitlines() if x] if head else []
    touched = set(x for x in git(wt, "diff", "--name-only", head).splitlines() if x) if head else set()
    touched |= set(x for x in git(wt, "ls-files", "--others", "--exclude-standard").splitlines() if x)
    touched = sorted(f for f in touched if not f.startswith(".claude/"))
    uncommitted = len([x for x in git(wt, "status", "--porcelain").splitlines() if x])
    m = re.match(r"^[a-z]+/(\d+)-", branch or "")
    return {"branch": branch, "commits": commits, "files": touched, "uncommitted": uncommitted, "issue": m.group(1) if m else ""}


def _line_facts(f: dict) -> list[str]:
    out = [f"- Branche : {f['branch'] or '(inconnue)'}" + (f", issue #{f['issue']}" if f["issue"] else "")]
    n = len(f["commits"])
    out.append(f"- Commits de la session : {n}" + ("" if not n else " (" + " ; ".join(c[:70] for c in f["commits"][:5]) + (" ; …" if n > 5 else "") + ")"))
    k = len(f["files"])
    out.append(f"- Fichiers touchés : {k}" + ("" if not k else " (" + ", ".join(f["files"][:8]) + (", …" if k > 8 else "") + ")"))
    out.append(f"- Non committé : {f['uncommitted']} fichier(s)")
    return out


# --------------------------------------------------------------------------- entrées

def entry_path(jdir: str, sess: dict) -> str:
    stamp = re.sub(r"[^0-9]", "", sess["started"])
    return os.path.join(jdir, f"{sess['started'][:10]}-{stamp[8:14]}-{sess['id'][:8]}.md")


def parse_entry(path: str) -> dict | None:
    try:
        text = open(path, encoding="utf-8").read()
    except OSError:
        return None
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return None
    meta = dict(x.split(": ", 1) for x in m.group(1).splitlines() if ": " in x)
    body = ""
    if "## Journal" in m.group(2):
        body = m.group(2).split("## Journal", 1)[1].strip()
    meta.update({"path": path, "body": body, "auto": meta.get("auto") == "true"})
    return meta


def write_entry(root: str, sess: dict, policy: dict | None = None, body: str | None = None, f: dict | None = None) -> str:
    jdir = journal_dir(root, policy)
    path = entry_path(jdir, sess)
    old = parse_entry(path)
    keep = body if body is not None else (old["body"] if old else "")
    f = f or facts(sess)
    head = ["---", f"session: {sess['id']}", f"date: {sess['started'][:16]}", f"branch: {f['branch']}",
            f"auto: {'false' if keep else 'true'}", "---", "## Faits"] + _line_facts(f)
    text = "\n".join(head) + "\n" + (f"## Journal\n{keep.strip()}\n" if keep else "")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    return path


def read_entries(jdir: str, limit: int = 40) -> list[dict]:
    try:
        names = sorted((n for n in os.listdir(jdir) if n.endswith(".md")), reverse=True)[:limit]
    except OSError:
        return []
    return [e for e in (parse_entry(os.path.join(jdir, n)) for n in names) if e]


def has_body(root: str, sess: dict, policy: dict | None = None) -> bool:
    e = parse_entry(entry_path(journal_dir(root, policy, create=False), sess))
    return bool(e and e["body"])


def validate_body(text: str) -> tuple[str, str]:
    """Retourne (texte nettoyé, erreur). Au plus BODY_LINES lignes non vides ; secrets masqués."""
    lines = [x.rstrip() for x in text.strip().splitlines() if x.strip()]
    if not lines:
        return "", "entrée vide"
    if len(lines) > BODY_LINES:
        return "", f"{BODY_LINES} lignes au plus (reçu : {len(lines)}) : garder l'essentiel"
    return scrub("\n".join(lines)), ""


def prune(jdir: str, days: int) -> int:
    cutoff, n = time.time() - days * 86400, 0
    try:
        for name in os.listdir(jdir):
            p = os.path.join(jdir, name)
            if name.endswith(".md") and os.path.getmtime(p) < cutoff:
                os.unlink(p)
                n += 1
    except OSError:
        pass
    return n


def housekeeping(root: str, policy: dict | None) -> None:
    """Au démarrage d'une session : purge du journal, des vieux marqueurs et des vieilles sessions."""
    prune(journal_dir(root, policy, create=False), journal_days(policy))
    for sub, days in (("sessions", 30), ("", 30)):
        base = os.path.join(local_dir(root), sub) if sub else local_dir(root)
        try:
            for name in os.listdir(base):
                p = os.path.join(base, name)
                if (name.startswith("nudged-") or (sub and name.endswith(".json"))) and os.path.getmtime(p) < time.time() - days * 86400:
                    os.unlink(p)
        except OSError:
            pass


# --------------------------------------------------------------------------- signaux

def signals_path(root: str) -> str:
    return os.path.join(local_dir(root), "signals.jsonl")


def append_signal(root: str, kind: str, session: str = "", key: str = "", text: str = "") -> None:
    rec = {"t": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time(), "session": session, "kind": kind,
           "key": scrub(key)[:90], "text": scrub(text)[:300]}
    with open(signals_path(root), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_signals(root: str, days: int = 30) -> list[dict]:
    out, cutoff = [], time.time() - days * 86400
    try:
        for line in open(signals_path(root), encoding="utf-8"):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("ts", 0) >= cutoff:
                out.append(rec)
    except OSError:
        pass
    return out


def session_signals(root: str, sid: str) -> int:
    return sum(1 for r in read_signals(root, 2) if r.get("session") == sid)


def inbox_count(root: str) -> int:
    try:
        return sum(1 for x in open(os.path.join(local_dir(root, False), "inbox.md"), encoding="utf-8") if x.strip())
    except OSError:
        return 0


# --------------------------------------------------------------------------- reprise au démarrage

def _age_days(date: str) -> int:
    try:
        return max(0, int((time.time() - time.mktime(time.strptime(date, "%Y-%m-%d %H:%M"))) // 86400))
    except ValueError:
        return 0


def _first(entry: dict) -> str:
    if entry["body"]:
        return entry["body"].splitlines()[0][:110]
    return "session fermée sans journal (faits seulement)"


def _branch_gone(root: str, branch: str) -> bool:
    if not branch or branch in ("HEAD", "main", "master"):
        return False
    return not git(root, "rev-parse", "--verify", "-q", f"refs/heads/{branch}") and not git(root, "rev-parse", "--verify", "-q", f"refs/remotes/origin/{branch}")


def render_resume(root: str, sess: dict, policy: dict | None = None) -> str:
    """Bloc injecté au démarrage : la dernière session de la branche, deux titres, l'état actuel, les candidats en attente."""
    entries = [e for e in read_entries(journal_dir(root, policy, create=False)) if e.get("session") != sess.get("id")]
    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD") or sess.get("branch", "")
    dirty = len([x for x in git(root, "status", "--porcelain").splitlines() if x])
    waiting = inbox_count(root)
    if not entries and not waiting:
        return ""
    lines = ["Kwa, reprise de session (journal local) :"]
    if entries:
        pick = next((e for e in entries if e.get("branch") == branch), entries[0])
        age = _age_days(pick.get("date", ""))
        flags = (f", ancienne : {age} jours" if age > STALE_DAYS else "") + (", branche supprimée ou fusionnée" if _branch_gone(root, pick.get("branch", "")) else "")
        lines.append(f"Dernière session {'de cette branche' if pick.get('branch') == branch else 'du projet'} ({pick.get('date', '?')}, {pick.get('branch', '?')}{flags}) :")
        body = pick["body"] or "Fermée sans journal. " + " ".join(l[2:] for l in open(pick["path"], encoding="utf-8").read().split("## Faits", 1)[-1].splitlines() if l.startswith("- "))
        lines += ["  " + l for l in body.splitlines()[:BODY_LINES]]
        rest = [e for e in entries if e is not pick][:2]
        if rest:
            lines.append("Sessions précédentes :")
            lines += [f"  - {e.get('date', '?')} · {e.get('branch', '?')} · {_first(e)}" for e in rest]
    lines.append(f"État actuel : branche {branch or '?'}, {dirty} fichier(s) non committé(s).")
    if waiting:
        lines.append(f"En attente : {waiting} note(s) d'apprentissage (`python3 .claude/kwa/bin/kwa-memory pending`, puis /kwa-learn, jamais appliqué sans accord).")
    lines.append("Si l'utilisateur reprend ce travail, partir du « Reste à faire » ; ne pas relire tout le journal "
                 "(`python3 .claude/kwa/bin/kwa-memory journal --last 5` au besoin).")
    text = "\n".join(lines)
    return text if len(text) <= BUDGET else text[:BUDGET - 1].rstrip() + "…"
