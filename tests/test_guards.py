"""Gardes Kwa : cas nominaux + contournements confirmés par l'audit de super-board."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HOOKS = os.path.join(os.path.dirname(__file__), "..", "core", "hooks")


def run(hook, tool, tool_input, cwd=None, env=None):
    payload = {"tool_name": tool, "tool_input": tool_input, "cwd": cwd or os.getcwd()}
    e = {**os.environ, **(env or {})}
    e.pop("CLAUDE_PROJECT_DIR", None)
    if cwd:
        e["CLAUDE_PROJECT_DIR"] = cwd
    p = subprocess.run([sys.executable, os.path.join(HOOKS, hook)], input=json.dumps(payload),
                       capture_output=True, text=True, env=e)
    assert p.returncode == 0, p.stderr
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"] if p.stdout.strip() else "allow"


def bash(hook, cmd, **kw):
    return run(hook, "Bash", {"command": cmd}, **kw)


class Secrets(unittest.TestCase):
    def test_denied(self):
        for cmd in ["cat .env", "cat .env.local", "cat .env.backup", "cat config/prod.env", "cat .e''nv",
                    "bash -c 'cat .env'", "env A=1 cat .env", "KEY=1\ncat .env", "printenv",
                    "gh auth token", "cat ~/.netrc", "cat ~/.config/gh/hosts.yml", "cat id_rsa",
                    "scw config get secret-key", "echo ok; cat .env", "cat < .env", "nice -n 5 cat .env"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(bash("guard-secrets.py", cmd), "deny")

    def test_allowed(self):
        for cmd in ["cat .env.example", "ls -la", "git status", "cat README.md", "env FOO=1 ls"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(bash("guard-secrets.py", cmd), "allow")

    def test_code_identifiers_are_not_files(self):
        """`process.env`, `self.env`, `config.env` sont des identifiants de code, pas des fichiers : pas de faux positif."""
        d = tempfile.mkdtemp()
        for cmd in ["grep -rn process.env src/", "node -e \"console.log(process.env.HOME)\"", "python3 -c 'print(self.env)'",
                    "grep -rn config.env docs/"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(bash("guard-secrets.py", cmd, cwd=d), "allow")

    def test_dotted_name_that_exists_as_a_file_is_denied(self):
        d = tempfile.mkdtemp()
        open(os.path.join(d, "prod.env"), "w").write("X=1\n")
        self.assertEqual(bash("guard-secrets.py", "cat prod.env", cwd=d), "deny")
        self.assertEqual(bash("guard-secrets.py", "cat ./prod.env", cwd=d), "deny")

    def test_read_tool(self):
        self.assertEqual(run("guard-secrets.py", "Read", {"file_path": "/x/.env"}), "deny")
        self.assertEqual(run("guard-secrets.py", "Read", {"file_path": "/x/.env.example"}), "allow")


class Heredocs(unittest.TestCase):
    """Un corps de heredoc est une donnée, sauf si la commande qui le porte est un interpréteur."""

    def setUp(self):
        self.d = tempfile.mkdtemp()

    def secrets(self, cmd):
        return bash("guard-secrets.py", cmd, cwd=self.d)

    def test_data_even_when_another_command_on_the_line_is_an_interpreter(self):
        self.assertEqual(self.secrets("python3 build.py; git commit -q -F - <<'EOF'\nmessage qui cite cat .env\nEOF"), "allow")
        self.assertEqual(self.secrets("node build.js && cat > note.md <<'EOF'\nne jamais faire cat .env\nEOF"), "allow")

    def test_executed_when_the_carrier_is_an_interpreter(self):
        self.assertEqual(self.secrets("bash <<'EOF'\ncat .env\nEOF"), "deny")
        self.assertEqual(self.secrets("echo ok; sh <<'EOF'\ncat .env\nEOF"), "deny")
        self.assertEqual(self.secrets("python3 - <<'PY'\ncat .env\nPY"), "deny")

    def test_executed_when_piped_to_an_interpreter(self):
        self.assertEqual(self.secrets("cat <<'EOF' | bash\ncat .env\nEOF"), "deny")
        self.assertEqual(self.secrets("cat <<'EOF' | sudo sh\ncat .env\nEOF"), "deny")


class Git(unittest.TestCase):
    def setUp(self):
        self.repo = tempfile.mkdtemp()
        subprocess.run(["git", "init", "-q", "-b", "main", self.repo], check=True)

    def branch(self, name):
        subprocess.run(["git", "-C", self.repo, "checkout", "-q", "-B", name], check=True)

    def test_main_protected(self):
        for cmd in ["git commit -m x", "git push origin main", "git push", "bash -c 'git push origin main'",
                    "env A=1 git push origin main", "ls && git push origin HEAD:main", "git -C . push origin main",
                    "git push -f origin feat/x:main", "git push --force origin main"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(bash("guard-git.py", cmd, cwd=self.repo), "deny")

    def test_feature_branch(self):
        self.branch("feat/x")
        self.assertEqual(bash("guard-git.py", "git commit -m x", cwd=self.repo), "allow")
        self.assertEqual(bash("guard-git.py", "git push -u origin feat/x", cwd=self.repo), "ask")
        self.assertEqual(bash("guard-git.py", "git push --force-with-lease origin feat/x", cwd=self.repo), "ask")
        self.assertEqual(bash("guard-git.py", "git push origin main", cwd=self.repo), "deny")
        self.assertEqual(bash("guard-git.py", "gh pr merge 3", cwd=self.repo), "ask")
        self.assertEqual(bash("guard-git.py", "git reset --hard", cwd=self.repo), "ask")
        self.assertEqual(bash("guard-git.py", "git status", cwd=self.repo), "allow")

    def test_escape_hatch(self):
        self.assertEqual(bash("guard-git.py", "git commit -m x", cwd=self.repo, env={"KWA_ALLOW_MAIN": "1"}), "allow")


class Delete(unittest.TestCase):
    def setUp(self):
        self.root = os.path.realpath(tempfile.mkdtemp())
        os.makedirs(os.path.join(self.root, "build"))
        os.symlink("/etc", os.path.join(self.root, "link"))

    def test_denied(self):
        for cmd in ["rm -rf /", "rm -rf ~", "rm -rf ../../../../../../../usr/x", "rm -rf /usr/local/x", "bash -c 'rm -rf /usr/x'",
                    "env rm -rf /usr/x", "nice -n 1 rm -rf /usr/x", "rm -rf .git", "rm -rf .claude/kwa",
                    "rm -rf link/x", "true && rm -rf /usr/x", "find / -delete", "(cd /tmp && rm -rf /usr/x)", "echo $(rm -rf /usr/x)"]:
            with self.subTest(cmd=cmd):
                self.assertEqual(bash("guard-delete.py", cmd, cwd=self.root), "deny")

    def test_ask_or_allowed(self):
        self.assertEqual(bash("guard-delete.py", "rm -rf $(pwd)/../x", cwd=self.root), "ask")
        self.assertEqual(bash("guard-delete.py", "git clean -fd", cwd=self.root), "ask")
        self.assertEqual(bash("guard-delete.py", "rsync -a --delete a/ b/", cwd=self.root), "ask")
        self.assertEqual(bash("guard-delete.py", "rm -rf build", cwd=self.root), "allow")
        self.assertEqual(bash("guard-delete.py", "rm -rf /tmp/kwa-x", cwd=self.root), "allow")


class Write(unittest.TestCase):
    def test_secrets_in_content(self):
        samples = ["sk-ant-" + "a" * 30, "sk_live_" + "a" * 24, "AKIA" + "A" * 16, "ghp_" + "a" * 36,
                   "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghijk",
                   "postgres://app:s3cr3tpw@db.example.com/x", "-----BEGIN RSA PRIVATE KEY-----"]
        for s in samples:
            with self.subTest(s=s[:12]):
                self.assertEqual(run("guard-write.py", "Write", {"file_path": "/tmp/x.ts", "content": f"const k = '{s}'"}), "deny")

    def test_clean_and_marked(self):
        self.assertEqual(run("guard-write.py", "Write", {"file_path": "/tmp/x.ts", "content": "const a = process.env.KEY"}), "allow")
        self.assertEqual(run("guard-write.py", "Write", {"file_path": "/tmp/x.ts",
                            "content": "k = 'sk_live_" + "a" * 24 + "' // kwa:allow-secret"}), "allow")

    def test_config_protected(self):
        root = os.path.realpath(tempfile.mkdtemp())
        self.assertEqual(run("guard-write.py", "Edit", {"file_path": f"{root}/.claude/settings.json", "new_string": "{}"}, cwd=root), "ask")
        self.assertEqual(run("guard-write.py", "Edit", {"file_path": f"{root}/src/a.ts", "new_string": "x"}, cwd=root), "allow")


class FailClosed(unittest.TestCase):
    def test_bad_payload_does_not_crash(self):
        p = subprocess.run([sys.executable, os.path.join(HOOKS, "guard-git.py")], input="pas du json", capture_output=True, text=True)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
