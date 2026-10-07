"""Briques communes des gardes Kata. Bibliothèque standard uniquement.

Doctrine : ce sont des filets contre la bévue, pas une frontière de sécurité contre
un agent compromis. Ils échouent vers l'humain (« ask »), jamais en silence.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys

WRAPPERS = {"env", "nice", "nohup", "sudo", "time", "command", "builtin", "exec", "xargs", "timeout", "doas"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
SEP_RE = re.compile(r"\|\||&&|[;&|\n]")
SUBST_RE = re.compile(r"\$\(([^()]*)\)|`([^`]*)`")


def load_payload() -> dict:
    try:
        return json.load(sys.stdin)
    except ValueError:
        return {}


def decide(decision: str, reason: str) -> None:
    """decision: deny | ask. Sort avec le code 0 après avoir imprimé la décision."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": decision,
        "permissionDecisionReason": f"Kata — {reason}",
    }}, ensure_ascii=False))
    sys.exit(0)


def guarded(main) -> None:
    """Exécute le garde ; une erreur interne ouvre une demande humaine au lieu de laisser passer."""
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:  # noqa: BLE001
        decide("ask", f"le garde a échoué ({type(e).__name__}) ; valider à la main")


def segments(command: str, _depth: int = 0) -> list[list[str]]:
    """Découpe une commande shell en segments de mots, en dépliant bash -c / env / nice / sudo…
    Un guillemet cassé (ex. .e''nv) est recollé par shlex ; un échec de parsing renvoie le mot brut."""
    out: list[list[str]] = []
    if _depth == 0:
        command = strip_heredocs(command)
    if _depth < 4:  # substitutions $(…) et `…` : leur contenu est une commande à part entière
        for m in SUBST_RE.finditer(command):
            out += segments(m.group(1) or m.group(2) or "", _depth + 1)
    for raw in SEP_RE.split(command):
        raw = raw.strip()
        if not raw:
            continue
        try:
            words = shlex.split(raw, posix=True)
        except ValueError:
            words = raw.split()
        if words:
            words[0] = words[0].lstrip("({")
            words[-1] = words[-1].rstrip(")}") or words[-1]
            words = [w for w in words if w]
        # affectations VAR=val en tête, mots de contrôle shell
        while words and (re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or words[0] in {"then", "do", "else", "if", "while", "!"}):
            words = words[1:]
        while words and os.path.basename(words[0]) in WRAPPERS:
            words = words[1:]
            while words and (words[0].startswith("-") or re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", words[0]) or re.match(r"^\d+$", words[0])):
                words = words[1:]
        if not words:
            continue
        if os.path.basename(words[0]) in SHELLS and _depth < 4:
            if "-c" in words and words.index("-c") + 1 < len(words):
                out += segments(words[words.index("-c") + 1], _depth + 1)
                continue
        out.append(words)
    return out


def project_dir(payload: dict) -> str:
    return os.path.realpath(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())


# --- corps de heredoc : une DONNÉE (doc, message de commit citant un motif), sauf s'il est exécuté.
HEREDOC_RE = re.compile(r"<<-?[ \t]*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")
INTERP_RE = re.compile(r"(^|[ \t|;&(])(ba|z|k)?sh([ \t]|$)|python[0-9.]*|node|ruby|perl|eval|xargs")


def strip_heredocs(command: str) -> str:
    """Retire le corps des heredocs non exécutés. `bash <<EOF … EOF` reste inspecté en entier,
    sinon ce serait un contournement trivial."""
    out, delim = [], None
    for line in command.split("\n"):
        if delim is not None:
            if line.strip() == delim:
                delim = None
            continue
        out.append(line)
        m = HEREDOC_RE.search(line)
        if m and not INTERP_RE.search(line):
            delim = m.group(1)
    return "\n".join(out)


# --- politique projet : .claude/kata.policy.json, propriété du projet (jamais écrasée par kata)
def load_policy(payload: dict) -> dict:
    path = os.path.join(project_dir(payload), ".claude", "kata.policy.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def glob_match(path: str, pattern: str) -> bool:
    """`**` traverse les dossiers, `*` reste dans un dossier. Le motif est ancré sur la fin ou le chemin relatif."""
    rx, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            rx += "(?:.*/)?"; i += 3
        elif pattern.startswith("**", i):
            rx += ".*"; i += 2
        elif pattern[i] == "*":
            rx += "[^/]*"; i += 1
        elif pattern[i] == "?":
            rx += "[^/]"; i += 1
        else:
            rx += re.escape(pattern[i]); i += 1
    return re.search(rf"(^|/){rx}$", path) is not None


# --- fichiers de secrets (partagé par guard-secrets et guard-write)
SAFE_SUFFIX = re.compile(r"\.(example|sample|template|dist|defaults?)$", re.I)
SECRET_PATH = [
    re.compile(r"(^|/)\.env([._-].*)?$", re.I),
    re.compile(r"(^|/)[^/]+\.env$", re.I),
    re.compile(r"(^|/)\.envrc$", re.I),
    re.compile(r"(^|/)id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$"),
    re.compile(r"(^|/)\.ssh/"),
    re.compile(r"(^|/)\.(netrc|npmrc|pypirc|pgpass|git-credentials)$"),
    re.compile(r"(^|/)\.aws/(credentials|config)$"),
    re.compile(r"(^|/)\.config/(gh/hosts\.yml|scw/config\.yaml|gcloud/)"),
    re.compile(r"(^|/)\.docker/config\.json$"),
    re.compile(r"(^|/)credentials(\.json)?$"),
    re.compile(r"\.(pem|p12|pfx|key|keystore|jks)$", re.I),
    re.compile(r"service[-_]?account[^/]*\.json$", re.I),
]


def is_secret_path(p: str) -> bool:
    p = os.path.expanduser(p.strip().strip("'\""))
    return bool(p) and not SAFE_SUFFIX.search(p) and any(r.search(p) for r in SECRET_PATH)
