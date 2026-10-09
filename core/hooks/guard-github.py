#!/usr/bin/env python3
"""PreToolUse Bash — le workflow issue → PR → preuve, en garantie.

  gh pr create : refusé si le corps ne porte pas « Closes #N » (ou Fixes / Resolves).
  gh pr merge  : refusé si la PR n'est liée à aucune issue, ou si ni la PR ni ses issues ne portent de preuve
                 (une image, ou une section « Preuve » réellement remplie).

Actif seulement si la politique a flow.issue_required (défaut : vrai). `GH` remplace gh dans les tests.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _kwa import decide, guarded, load_payload, load_policy, project_dir, segments, strip_heredocs  # noqa: E402

CLOSES = re.compile(r"(close[sd]?|fix(e[sd])?|resolve[sd]?) +#[0-9]+", re.I)
IMAGE = re.compile(r"!\[[^\]]*\]\(|<img ")


def gh(*args: str) -> str | None:
    try:
        r = subprocess.run([os.environ.get("GH", "gh"), *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout if r.returncode == 0 else None


def has_proof(texts: str) -> bool:
    if IMAGE.search(texts):
        return True
    in_proof = in_comment = False
    for line in texts.split("\n"):
        if re.match(r"^#+ *Preuve", line):
            in_proof = True
            continue
        if re.match(r"^#+ ", line):
            in_proof = False
        if in_proof and "<!--" in line:
            in_comment = True
        if in_proof and not in_comment and line.strip():
            return True
        if in_comment and "-->" in line:
            in_comment = False
    return False


def body_file(words: list[str], root: str) -> str:
    for i, w in enumerate(words):
        f = None
        if w in {"--body-file", "-F"} and i + 1 < len(words):
            f = words[i + 1]
        elif w.startswith("--body-file="):
            f = w.split("=", 1)[1]
        if f:
            path = f if os.path.isabs(f) else os.path.join(root, f)
            try:
                return open(path, encoding="utf-8").read()
            except OSError:
                return ""
    return ""


def main() -> None:
    d = load_payload()
    if d.get("tool_name") != "Bash":
        return
    policy = load_policy(d)
    flow = policy.get("flow", {})
    if not flow.get("issue_required", True):
        return
    root = project_dir(d)
    raw = strip_heredocs((d.get("tool_input") or {}).get("command", ""))
    for words in segments(raw):
        if os.path.basename(words[0]) != "gh" or words[1:2] != ["pr"]:
            continue
        verb = words[2] if len(words) > 2 else ""
        if verb == "create":
            if CLOSES.search(raw) or CLOSES.search(body_file(words, root)):
                return
            decide("deny", "Une PR se rattache à son issue : le corps doit porter « Closes #N ». "
                           "Pas d'issue ? L'ouvrir d'abord (kwa-start-dev).")
        if verb == "merge":
            num = next((w for w in words[3:] if w.isdigit()), "")
            out = gh("pr", "view", *([num] if num else []), "--json", "body,comments,closingIssuesReferences")
            if out is None:
                decide("ask", "Impossible de lire la PR pour vérifier son issue et sa preuve. Fusionner quand même ?")
            pr = json.loads(out)
            issues = [str(i["number"]) for i in pr.get("closingIssuesReferences", [])]
            if not issues:
                decide("deny", "Cette PR n'est liée à aucune issue (« Closes #N » dans son corps). Rattacher l'issue avant de fusionner.")
            if not flow.get("proof_required_for_merge", True):
                return
            texts = pr.get("body", "") + "\n" + "\n".join(c.get("body", "") for c in pr.get("comments", []))
            for i in issues:
                texts += "\n" + (gh("issue", "view", i, "--json", "body,comments", "-q", ".body, (.comments[].body)") or "")
            if has_proof(texts):
                return
            decide("deny", f"Aucune preuve sur la PR ni sur ses issues ({' '.join(issues)}). Joindre les captures "
                           "(gh issue comment <n°> --attach …) ou remplir la section « Preuve » pour un changement sans interface.")


if __name__ == "__main__":
    guarded(main)
