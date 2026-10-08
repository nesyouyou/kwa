import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.join(os.path.dirname(__file__), "..", "core", "hooks")
BASH_GUARDS = ["guard-secrets.py", "guard-git.py", "guard-delete.py", "guard-policy.py", "guard-github.py"]
RANK = {"allow": 0, "ask": 1, "deny": 2}


def call(hook, tool, tool_input, cwd, env=None):
    e = {**os.environ, "CLAUDE_PROJECT_DIR": cwd, **(env or {})}
    p = subprocess.run([sys.executable, os.path.join(HOOKS, hook)], input=json.dumps(
        {"tool_name": tool, "tool_input": tool_input, "cwd": cwd}), capture_output=True, text=True, env=e)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "allow"


def chain(cmd, cwd, env=None, guards=BASH_GUARDS):
    """Décision la plus sévère de la chaîne de gardes Bash (comme Claude Code les enchaîne)."""
    worst = "allow"
    for g in guards:
        d = call(g, "Bash", {"command": cmd}, cwd, env)
        if RANK[d] > RANK[worst]:
            worst = d
    return worst


def make_repo(policy=None, branch="main"):
    d = os.path.realpath(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", "-b", branch, d], check=True)
    if policy:
        os.makedirs(os.path.join(d, ".claude"), exist_ok=True)
        shutil.copy(policy, os.path.join(d, ".claude", "kwa.policy.json"))
    return d
