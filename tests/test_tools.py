"""kwa-start, kwa-hygiene, mémoire, modules et détection de l'installeur."""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest

from helpers import HOOKS

PACK = os.path.join(os.path.dirname(__file__), "..")
KWA = os.path.join(PACK, "bin", "kwa")
BIN = os.path.join(PACK, "core", "bin")


def sh(*cmd, cwd=None, env=None, input=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={**os.environ, **(env or {})}, input=input)


def git_repo(files=None, branch="main"):
    d = os.path.realpath(tempfile.mkdtemp())
    sh("git", "init", "-q", "-b", branch, d)
    sh("git", "-C", d, "config", "user.email", "t@example.test")
    sh("git", "-C", d, "config", "user.name", "t")
    for rel, text in (files or {}).items():
        p = os.path.join(d, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w").write(text)
    return d


class Start(unittest.TestCase):
    def setUp(self):
        base = os.path.realpath(tempfile.mkdtemp())
        self.origin = os.path.join(base, "origin.git")
        sh("git", "init", "-q", "--bare", "-b", "main", self.origin)
        self.repo = os.path.join(base, "proj")
        sh("git", "clone", "-q", self.origin, self.repo)
        for k, v in (("user.email", "t@example.test"), ("user.name", "t")):
            sh("git", "-C", self.repo, "config", k, v)
        os.makedirs(os.path.join(self.repo, ".claude"))
        json.dump({"start": {"install": ["touch installed.flag"]}}, open(os.path.join(self.repo, ".claude", "kwa.policy.json"), "w"))
        open(os.path.join(self.repo, "a.txt"), "w").write("a")
        sh("git", "-C", self.repo, "add", "-A")
        sh("git", "-C", self.repo, "commit", "-q", "-m", "init")
        sh("git", "-C", self.repo, "push", "-q", "origin", "main")
        stub = os.path.join(base, "gh")
        open(stub, "w").write('#!/bin/sh\ncase "$1 $2" in\n  "issue create") echo called >> "$(dirname "$0")/gh-issue-create.log"; echo "https://github.com/o/r/issues/7" ;;\n  "issue view") echo "{}" ;;\nesac\n')
        os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)
        self.env = {"PATH": base + os.pathsep + os.environ["PATH"]}
        self.base = base

    def test_creates_issue_branch_worktree_and_installs(self):
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "my-filter", "Un filtre", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = os.path.join(self.base, "proj-wt-7-my-filter")
        self.assertTrue(os.path.isdir(wt))
        self.assertTrue(os.path.exists(os.path.join(wt, "installed.flag")))
        self.assertEqual(sh("git", "-C", wt, "symbolic-ref", "--short", "HEAD").stdout.strip(), "feat/7-my-filter")
        self.assertEqual(sh("git", "-C", self.repo, "symbolic-ref", "--short", "HEAD").stdout.strip(), "main", "main reste propre")

    def issue_calls(self):
        log = os.path.join(self.base, "gh-issue-create.log")
        return len(open(log).read().split()) if os.path.exists(log) else 0

    def set_flow(self, **flow):
        p = os.path.join(self.repo, ".claude", "kwa.policy.json")
        d = json.load(open(p))
        d["flow"] = flow
        json.dump(d, open(p, "w"))

    def test_issue_is_created_automatically_by_default(self):
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "auto-one", "Auto", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.issue_calls(), 1)
        self.assertTrue(os.path.isdir(os.path.join(self.base, "proj-wt-7-auto-one")))

    def test_auto_issue_false_makes_only_a_branch(self):
        self.set_flow(auto_issue=False)
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "no-issue-here", "Sans issue", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.issue_calls(), 0, "aucune issue ne doit être créée")
        wt = os.path.join(self.base, "proj-wt-no-issue-here")
        self.assertTrue(os.path.isdir(wt))
        self.assertEqual(sh("git", "-C", wt, "symbolic-ref", "--short", "HEAD").stdout.strip(), "feat/no-issue-here")

    def test_no_issue_flag_overrides_policy(self):
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "fix", "flag-only", "Flag", "--no-issue", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.issue_calls(), 0)
        self.assertTrue(os.path.isdir(os.path.join(self.base, "proj-wt-flag-only")))

    def test_explicit_issue_still_wins_when_auto_issue_is_false(self):
        self.set_flow(auto_issue=False)
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "fix", "reuse", "Reprise", "--issue", "9", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(os.path.join(self.base, "proj-wt-9-reuse")))

    def test_start_link_symlinks_local_files_instead_of_copying(self):
        open(os.path.join(self.repo, "secret.local"), "w").write("VALEUR=1\n")  # fichier local, non suivi par git
        p = os.path.join(self.repo, ".claude", "kwa.policy.json")
        d = json.load(open(p))
        d["start"]["link"] = ["secret.local", "../dehors", "a.txt", "absent.local"]
        json.dump(d, open(p, "w"))
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "linked", "Lien", "--no-issue", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        wt = os.path.join(self.base, "proj-wt-linked")
        link = os.path.join(wt, "secret.local")
        self.assertTrue(os.path.islink(link), "le fichier local est relié, pas copié")
        self.assertEqual(os.path.realpath(link), os.path.realpath(os.path.join(self.repo, "secret.local")))
        self.assertFalse(os.path.islink(os.path.join(wt, "a.txt")), "un fichier suivi par git n'est jamais remplacé")
        self.assertFalse(os.path.lexists(os.path.join(self.base, "dehors")), "un chemin hors du projet est ignoré")
        self.assertIn("hors du projet", r.stderr)
        self.assertFalse(os.path.lexists(os.path.join(wt, "absent.local")), "un fichier absent n'est pas relié")

    def test_base_option_starts_from_another_branch(self):
        sh("git", "-C", self.repo, "switch", "-q", "-c", "dev")
        open(os.path.join(self.repo, "dev-only.txt"), "w").write("d")
        sh("git", "-C", self.repo, "add", "-A")
        sh("git", "-C", self.repo, "commit", "-q", "-m", "dev")
        sh("git", "-C", self.repo, "push", "-q", "origin", "dev")
        sh("git", "-C", self.repo, "switch", "-q", "main")
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "from-dev", "Depuis dev", "--no-issue", "--base", "dev", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.base, "proj-wt-from-dev", "dev-only.txt")))
        r2 = sh(sys.executable, os.path.join(BIN, "kwa-start"), "feat", "from-main", "Depuis main", "--no-issue", cwd=self.repo, env=self.env)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.base, "proj-wt-from-main", "dev-only.txt")), "sans --base, on part de main")

    def test_existing_issue_and_bad_slug(self):
        r = sh(sys.executable, os.path.join(BIN, "kwa-start"), "fix", "x-y", "t", "--issue", "9", cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(os.path.isdir(os.path.join(self.base, "proj-wt-9-x-y")))
        bad = sh(sys.executable, os.path.join(BIN, "kwa-start"), "fix", "Bad Slug", "t", cwd=self.repo, env=self.env)
        self.assertEqual(bad.returncode, 2)


class FormatBoundary(unittest.TestCase):
    """Le formateur ne touche qu'aux fichiers du projet : jamais à ceux d'un autre dépôt ou d'un worktree voisin."""

    def setUp(self):
        self.base = os.path.realpath(tempfile.mkdtemp())
        self.log = os.path.join(self.base, "npx.log")
        stub = os.path.join(self.base, "bin")
        os.makedirs(stub)
        open(os.path.join(stub, "npx"), "w").write(
            '#!/bin/sh\ncase "$*" in\n  *--version*) exit 0 ;;\n  *--write*) echo "$*" >> "%s" ;;\nesac\n' % self.log)
        os.chmod(os.path.join(stub, "npx"), 0o755)
        self.env = {"PATH": stub + os.pathsep + os.environ["PATH"]}
        self.project = os.path.join(self.base, "project")
        self.other = os.path.join(self.base, "autre-depot")
        for d in (self.project, self.other):
            os.makedirs(d)
            sh("git", "init", "-q", "-b", "main", d)

    def run_hook(self, path):
        open(path, "w").write("# titre\n")
        return sh(sys.executable, os.path.join(HOOKS, "format-after-edit.py"), env={**self.env, "CLAUDE_PROJECT_DIR": self.project},
                  input=json.dumps({"tool_name": "Write", "tool_input": {"file_path": path}, "cwd": self.project}))

    def calls(self):
        return open(self.log).read().count("--write") if os.path.exists(self.log) else 0

    def test_new_file_inside_the_project_is_formatted(self):
        self.assertEqual(self.run_hook(os.path.join(self.project, "note.md")).returncode, 0)
        self.assertEqual(self.calls(), 1)

    def test_file_of_another_repository_is_left_alone(self):
        self.assertEqual(self.run_hook(os.path.join(self.other, "note.md")).returncode, 0)
        self.assertEqual(self.calls(), 0, "un fichier hors du projet ne doit jamais être formaté")

    def test_tracked_file_inside_the_project_is_not_rewritten(self):
        p = os.path.join(self.project, "suivi.md")
        open(p, "w").write("# a\n")
        sh("git", "-C", self.project, "add", "suivi.md")
        self.run_hook(p)
        self.assertEqual(self.calls(), 0, "un fichier déjà suivi n'est pas reformaté (seulement signalé)")


class Hygiene(unittest.TestCase):
    def run_h(self, files, extra=None, *args):
        d = git_repo(files)
        if extra:
            os.makedirs(os.path.join(d, ".claude"), exist_ok=True)
            for rel, text in extra.items():
                open(os.path.join(d, rel), "w").write(text)
        sh("git", "-C", d, "add", "-A")
        return sh(sys.executable, os.path.join(BIN, "kwa-hygiene"), "--root", d, *args)

    def test_secret_blocks(self):
        r = self.run_h({"src/a.ts": 'const password = "abcdefghijklmnopqrstuv1234"\n'})
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_placeholder_and_env_reference_pass(self):
        r = self.run_h({"src/a.ts": 'const password = process.env.PW; const token = "changeme-changeme-changeme"\n'})
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_personal_account_blocks_and_is_masked(self):
        r = self.run_h({"src/a.ts": "const admin = 'jean.dupont@gmail.com'\n"})
        self.assertEqual(r.returncode, 1)
        self.assertNotIn("jean.dupont", r.stdout)

    def test_docs_and_tests_out_of_scope(self):
        r = self.run_h({"docs/n.md": "contact x@gmail.com", "src/a.spec.ts": 'password = "abcdefghijklmnopqrstuv1234"'})
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_name_is_warning_then_strict_fails(self):
        files = {"src/a.ts": "// écrit par Jeanne\n"}
        extra = {".claude/kwa.policy.json": json.dumps({"hygiene": {"names": ["Jeanne"]}})}
        self.assertEqual(self.run_h(files, extra).returncode, 0)
        self.assertEqual(self.run_h(files, extra, "--strict").returncode, 1)

    def test_allow_list_defers_and_is_shown(self):
        files = {"src/a.ts": "const a = 'x@gmail.com'\n"}
        extra = {".claude/kwa.hygiene.allow": "PERSONNEL\tsrc/a.ts\tà passer en variable d'env avant la remise\n"}
        r = self.run_h(files, extra)
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("avant la remise", r.stdout)


class Memory(unittest.TestCase):
    def nudge(self, repo, payload=None, env=None):
        p = {"session_id": "s1", "cwd": repo, **(payload or {})}
        return sh(sys.executable, os.path.join(HOOKS, "memory-nudge.py"), input=json.dumps(p), env={"CLAUDE_PROJECT_DIR": repo, **(env or {})})

    def test_capture_pending_clear(self):
        d = git_repo()
        mem = os.path.join(BIN, "kwa-memory")
        self.assertEqual(sh(sys.executable, mem, "capture", "gotcha", "le boot est lent", cwd=d).returncode, 0)
        self.assertIn("1 note(s)", sh(sys.executable, mem, "pending", cwd=d).stdout)
        self.assertEqual(sh(sys.executable, mem, "capture", "nimporte", "x", cwd=d).returncode, 2)
        sh(sys.executable, mem, "clear", cwd=d)
        self.assertIn("0 note(s)", sh(sys.executable, mem, "pending", cwd=d).stdout)

    def test_nudge_once_when_substantial(self):
        d = git_repo({f"src/f{i}.ts": "x" for i in range(4)})
        self.assertEqual(self.nudge(d).returncode, 2)
        self.assertEqual(self.nudge(d).returncode, 0, "une seule invitation par session")

    def test_nudge_quiet_cases(self):
        small = git_repo({"src/a.ts": "x"})
        self.assertEqual(self.nudge(small).returncode, 0)
        docs = git_repo({f"docs/d{i}.md": "x" for i in range(5)})
        self.assertEqual(self.nudge(docs).returncode, 0, "la doc ne déclenche pas")
        big = git_repo({f"src/f{i}.ts": "x" for i in range(4)})
        self.assertEqual(self.nudge(big, {"stop_hook_active": True}).returncode, 0)
        self.assertEqual(self.nudge(big, env={"KWA_MEMORY_NUDGE": "0"}).returncode, 0)

    def test_nudge_only_asks_for_what_is_missing(self):
        d = git_repo({f"src/f{i}.ts": "x" for i in range(4)})
        sh(sys.executable, os.path.join(HOOKS, "memory-context.py"), input=json.dumps({"session_id": "s1", "cwd": d}), env={"CLAUDE_PROJECT_DIR": d})
        sh(sys.executable, os.path.join(BIN, "kwa-memory"), "capture", "decision", "x", cwd=d)
        r = self.nudge(d)
        self.assertEqual(r.returncode, 2, "le journal manque encore")
        self.assertIn("journal", r.stderr)
        self.assertNotIn("/kwa-learn", r.stderr, "des notes ont déjà été captées pendant la session")

    def test_session_start_context(self):
        d = git_repo()
        quiet = sh(sys.executable, os.path.join(HOOKS, "memory-context.py"), input=json.dumps({"cwd": d}), env={"CLAUDE_PROJECT_DIR": d})
        self.assertEqual(quiet.stdout.strip(), "")
        sh(sys.executable, os.path.join(BIN, "kwa-memory"), "capture", "pref", "x", cwd=d)
        out = sh(sys.executable, os.path.join(HOOKS, "memory-context.py"), input=json.dumps({"cwd": d}), env={"CLAUDE_PROJECT_DIR": d})
        self.assertIn("/kwa-learn", json.loads(out.stdout)["hookSpecificOutput"]["additionalContext"])


class Modules(unittest.TestCase):
    def project(self):
        d = git_repo({"package.json": json.dumps({"scripts": {"typecheck": "tsc", "lint": "eslint", "db:generate": "x"}}),
                      "pnpm-lock.yaml": "", "apps/web/page.tsx": "x", ".github/workflows/deploy.yml": "run: scw container deploy"})
        return d

    def kwa(self, *args, env=None):
        return sh(sys.executable, KWA, *args, env={"KWA_HOME": tempfile.mkdtemp(), **(env or {})})

    def test_auto_detection_and_policy(self):
        d = self.project()
        r = self.kwa("install", d)
        self.assertEqual(r.returncode, 0, r.stderr)
        state = json.load(open(os.path.join(d, ".claude/kwa/state.json")))
        for m in ("core", "memory", "issue-flow", "verify", "stack-scaleway", "deploy"):
            self.assertIn(m, state["modules"])
        pol = json.load(open(os.path.join(d, ".claude/kwa.policy.json")))
        self.assertEqual(pol["verify"]["commands"], ["pnpm typecheck", "pnpm lint"])
        self.assertEqual(pol["start"]["install"], ["pnpm install --frozen-lockfile", "pnpm db:generate"])
        self.assertEqual(pol["write"]["no_code_on_main"], ["apps/"])
        self.assertTrue(os.path.exists(os.path.join(d, ".github/pull_request_template.md")))
        self.assertTrue(os.path.exists(os.path.join(d, ".claude/skills/kwa-learn/SKILL.md")))
        self.assertEqual(self.kwa("doctor", d).returncode, 0, self.kwa("doctor", d).stdout)

    def test_detection_proposes_linking_the_local_environment_file(self):
        d = self.project()
        open(os.path.join(d, ".env"), "w").write("A=1\n")
        self.kwa("install", d)
        pol = json.load(open(os.path.join(d, ".claude/kwa.policy.json")))
        self.assertEqual(pol["start"]["link"], [".env"])
        sans = self.project()
        self.kwa("install", sans)
        self.assertNotIn("link", json.load(open(os.path.join(sans, ".claude/kwa.policy.json")))["start"])

    def test_policy_and_seeds_belong_to_project(self):
        d = self.project()
        self.kwa("install", d)
        pol_path = os.path.join(d, ".claude/kwa.policy.json")
        pol = json.load(open(pol_path))
        pol["bash"]["deny"].append({"id": "mine", "reason": "r", "any": ["x"]})
        json.dump(pol, open(pol_path, "w"))
        open(os.path.join(d, ".github/pull_request_template.md"), "w").write("mon gabarit\n")
        r = self.kwa("install", d)
        self.assertIn("conservée", r.stdout)
        self.assertIn("mine", [x["id"] for x in json.load(open(pol_path))["bash"]["deny"]])
        self.assertEqual(open(os.path.join(d, ".github/pull_request_template.md")).read(), "mon gabarit\n")

    def test_git_exclude_and_no_commit(self):
        d = self.project()
        self.kwa("install", d)
        self.assertIn(".claude/kwa/local/", open(os.path.join(d, ".git/info/exclude")).read())
        self.assertNotEqual(sh("git", "-C", d, "log", "--oneline").returncode, 0)
        self.assertEqual(sh("git", "-C", d, "diff", "--cached", "--name-only").stdout, "")

    def test_git_exclude_is_written_for_a_worktree(self):
        d = self.project()
        sh("git", "-C", d, "-c", "user.name=t", "-c", "user.email=t@example.org", "commit", "-q", "--allow-empty", "-m", "init")
        wt = d + "-wt"
        self.assertEqual(sh("git", "-C", d, "worktree", "add", "-q", wt, "-b", "wt-branch").returncode, 0)
        try:
            r = self.kwa("install", wt)
            self.assertNotIn("pas de dépôt git", r.stdout)
            self.assertIn(".claude/kwa/local/", open(os.path.join(d, ".git/info/exclude")).read())
        finally:
            sh("git", "-C", d, "worktree", "remove", "--force", wt)

    def test_codex_parity(self):
        d = self.project()
        self.kwa("install", d, "--codex")
        self.assertTrue(os.path.islink(os.path.join(d, ".agents/skills/kwa-commit")))
        hooks = json.load(open(os.path.join(d, ".codex/hooks.json")))
        cmds = [h["command"] for e in hooks["hooks"]["PreToolUse"] for h in e["hooks"]]
        self.assertTrue(all(c.startswith('cd "$(git rev-parse --show-toplevel)" && python3 .claude/kwa/hooks/') for c in cmds))

    def test_unknown_module_and_with(self):
        d = self.project()
        self.assertEqual(self.kwa("install", d, "--with", "nope").returncode, 2)
        self.assertEqual(self.kwa("install", d, "--modules", "core", "--with", "client-handover").returncode, 0)
        self.assertTrue(os.path.exists(os.path.join(d, ".claude/kwa/bin/kwa-hygiene")))

    def test_doctor_flags_project_overlap(self):
        d = self.project()
        os.makedirs(os.path.join(d, ".claude/hooks"))
        open(os.path.join(d, ".claude/hooks/guard-bash.sh"), "w").write("#!/bin/sh\n")
        self.kwa("install", d)
        self.assertIn("fait doublon", self.kwa("doctor", d).stdout)

    def test_recommend_reports_presence(self):
        d = git_repo({"package.json": json.dumps({"dependencies": {"expo": "1"}})})
        home = tempfile.mkdtemp()
        os.makedirs(os.path.join(home, ".claude", "skills", "aso"))
        r = sh(sys.executable, KWA, "recommend", d, env={"KWA_HOME": home})
        self.assertRegex(r.stdout, r"✓ présente\s+aso")
        self.assertRegex(r.stdout, r"✗ à installer\s+eas-app-stores")


if __name__ == "__main__":
    unittest.main()
