"""Apprentissage continu : journal des sessions, reprise au démarrage, signaux, filet de fermeture, worktrees."""
import json
import os
import re
import sys
import tempfile
import time
import unittest

from helpers import HOOKS
from test_tools import BIN, KWA, git_repo, sh

MEM = os.path.join(BIN, "kwa-memory")
# faux secrets assemblés à l'exécution : aucun jeton d'apparence réelle n'est écrit dans ce fichier
FAKE_GH = "gh" + "p_" + "abcdefghijklmnopqrstuvwxyz0123"
FAKE_SK = "s" + "k-" + "abcdefghijklmnop1234"
FAKE_PW = "password" + " = " + "hunter2xyz"


def committed_repo(files=None, branch="main"):
    d = git_repo({"README.md": "x", **(files or {})}, branch=branch)
    sh("git", "-C", d, "add", "-A")
    sh("git", "-C", d, "commit", "-qm", "init")
    return d


def hook(name, repo, payload=None, env=None):
    p = {"session_id": "sess-A", "cwd": repo, **(payload or {})}
    return sh(sys.executable, os.path.join(HOOKS, name), input=json.dumps(p), env={"CLAUDE_PROJECT_DIR": repo, **(env or {})})


def local(repo):
    return os.path.join(repo, ".claude", "kwa", "local")


def entries(repo):
    d = os.path.join(local(repo), "journal")
    return sorted(os.path.join(d, n) for n in os.listdir(d)) if os.path.isdir(d) else []


def memory(repo, *args, env=None):
    return sh(sys.executable, MEM, *args, cwd=repo, env={"CLAUDE_PROJECT_DIR": repo, **(env or {})})


def start(repo, **payload):
    return hook("memory-context.py", repo, payload)


def context(result):
    return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"] if result.stdout.strip() else ""


class Scrub(unittest.TestCase):
    def test_secrets_are_masked(self):
        sys.path.insert(0, HOOKS)
        import _journal

        for raw, leaked in [(f"le mot de passe est {FAKE_PW}", "hunter2xyz"),
                            (f"token {FAKE_GH}", FAKE_GH[:14]),
                            ("curl https://user:" + "s3cretpw@db.example.test/x", "s3cretpw"),
                            ("Authorization: " + "Bearer " + "abcdefghijklmnopqrstuvwx", "abcdefghijklmnop"),
                            (f"clé {FAKE_SK}", FAKE_SK[:12])]:
            with self.subTest(leaked=leaked):
                self.assertNotIn(leaked, _journal.scrub(raw))
        self.assertEqual(_journal.scrub("-----BEGIN RSA PRIVATE" + " KEY-----\nabc"), "[secret masqué]")
        self.assertEqual(_journal.scrub("Utiliser pnpm migrate:create avant pnpm migrate"), "Utiliser pnpm migrate:create avant pnpm migrate")


class Journal(unittest.TestCase):
    def test_start_is_silent_and_registers_the_session(self):
        d = committed_repo()
        r = start(d)
        self.assertEqual((r.returncode, r.stdout.strip()), (0, ""))
        self.assertTrue(os.path.isfile(os.path.join(local(d), "sessions", "sess-A.json")))

    def test_journal_entry_has_facts_and_body(self):
        d = committed_repo()
        start(d)
        open(os.path.join(d, "a.ts"), "w").write("x")
        sh("git", "-C", d, "add", "-A")
        sh("git", "-C", d, "commit", "-qm", "feat: a")
        open(os.path.join(d, "b.ts"), "w").write("y")
        r = memory(d, "journal", "Objectif : ajouter a\nFait : a et b\nReste à faire : tests")
        self.assertEqual(r.returncode, 0, r.stderr)
        text = open(entries(d)[0]).read()
        self.assertIn("auto: false", text)
        self.assertIn("## Faits", text)
        self.assertIn("Commits de la session : 1", text)
        self.assertIn("feat: a", text)
        self.assertRegex(text, r"Fichiers touchés : 2 \(.*a\.ts.*b\.ts")
        self.assertIn("Non committé : 1", text)
        self.assertIn("## Journal\nObjectif : ajouter a", text)

    def test_body_is_limited_cleaned_and_replaceable(self):
        d = committed_repo()
        start(d)
        too_long = memory(d, "journal", "\n".join(f"ligne {i}" for i in range(9)))
        self.assertEqual(too_long.returncode, 2)
        self.assertEqual(entries(d), [])
        memory(d, "journal", f"Fait : voir {FAKE_PW}")
        self.assertNotIn("hunter2xyz", open(entries(d)[0]).read())
        memory(d, "journal", "Fait : version finale")
        self.assertEqual(len(entries(d)), 1)
        self.assertIn("version finale", open(entries(d)[0]).read())

    def test_last_list_prune_and_disabled(self):
        d = committed_repo()
        start(d)
        memory(d, "journal", "Objectif : un")
        self.assertIn("Objectif : un", memory(d, "journal", "--last").stdout)
        self.assertIn("Objectif : un", memory(d, "journal", "--list").stdout)
        old = time.time() - 120 * 86400
        os.utime(entries(d)[0], (old, old))
        self.assertIn("1 entrée", memory(d, "journal", "--prune", "90").stdout)
        self.assertEqual(entries(d), [])
        off = memory(d, "journal", "Objectif : x", env={"KWA_JOURNAL": "0"})
        self.assertIn("désactivé", off.stdout)
        self.assertEqual(entries(d), [])

    def test_journal_without_a_registered_session_creates_a_manual_one(self):
        d = committed_repo()
        self.assertEqual(memory(d, "journal", "Objectif : sans hook").returncode, 0)
        self.assertEqual(len(entries(d)), 1)

    def test_session_end_safety_net(self):
        d = committed_repo()
        start(d)
        self.assertEqual(hook("journal-end.py", d).returncode, 0)
        self.assertEqual(entries(d), [], "une session sans trace n'écrit rien")
        open(os.path.join(d, "a.ts"), "w").write("x")
        t0 = time.time()
        self.assertEqual(hook("journal-end.py", d).returncode, 0)
        self.assertLess(time.time() - t0, 1.5, "SessionEnd dispose d'1,5 s")
        text = open(entries(d)[0]).read()
        self.assertIn("auto: true", text)
        self.assertNotIn("## Journal", text)
        memory(d, "journal", "Objectif : raconté")
        hook("journal-end.py", d)
        self.assertIn("auto: false", open(entries(d)[0]).read(), "le filet ne redevient pas automatique")
        self.assertIn("Objectif : raconté", open(entries(d)[0]).read())

    def test_session_end_without_a_start_record_writes_nothing(self):
        d = committed_repo({"a.ts": "x"})
        open(os.path.join(d, "b.ts"), "w").write("y")
        hook("journal-end.py", d)
        self.assertEqual(entries(d), [])

    def test_pre_compact_saves_facts_and_keeps_the_body(self):
        d = committed_repo()
        start(d)
        open(os.path.join(d, "a.ts"), "w").write("x")
        hook("journal-compact.py", d)
        self.assertIn("Fichiers touchés : 1", open(entries(d)[0]).read())
        memory(d, "journal", "Objectif : garde-moi")
        hook("journal-compact.py", d)
        self.assertIn("Objectif : garde-moi", open(entries(d)[0]).read())

    def test_hooks_never_fail_on_garbage_input(self):
        d = committed_repo()
        for name in ("memory-context.py", "journal-compact.py", "journal-end.py", "signal-prompt.py"):
            r = sh(sys.executable, os.path.join(HOOKS, name), input="pas du json", env={"CLAUDE_PROJECT_DIR": d})
            self.assertEqual(r.returncode, 0, name)

    def test_custom_journal_dir_from_policy(self):
        d = committed_repo()
        os.makedirs(os.path.join(d, ".claude"))
        json.dump({"memory": {"journal_dir": "docs/journal"}}, open(os.path.join(d, ".claude", "kwa.policy.json"), "w"))
        start(d)
        memory(d, "journal", "Objectif : partagé")
        self.assertTrue(os.listdir(os.path.join(d, "docs", "journal")))


class Resume(unittest.TestCase):
    def previous(self, d, branch, body, sid, days_ago=0):
        """Fabrique l'entrée d'une session passée, comme l'aurait écrite le journal."""
        hook("memory-context.py", d, {"session_id": sid})
        sh("git", "-C", d, "checkout", "-q", "-B", branch)
        memory(d, "journal", body)
        p = entries(d)[-1]
        if days_ago:
            text = open(p).read()
            old = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() - days_ago * 86400))
            open(p, "w").write(re.sub(r"^date: .*$", f"date: {old}", text, flags=re.M))
        return p

    def test_resume_prefers_the_current_branch_and_lists_two_titles(self):
        d = committed_repo()
        self.previous(d, "feat/a", "Objectif : sujet A\nReste à faire : le test A", "s1")
        self.previous(d, "feat/b", "Objectif : sujet B", "s2")
        self.previous(d, "feat/c", "Objectif : sujet C", "s3")
        self.previous(d, "feat/d", "Objectif : sujet D", "s4")
        sh("git", "-C", d, "checkout", "-q", "feat/a")
        out = context(start(d, session_id="nouvelle"))
        self.assertIn("Dernière session de cette branche", out)
        self.assertIn("Reste à faire : le test A", out)
        self.assertEqual(len(re.findall(r"^  - ", out, re.M)), 2, out)

    def test_resume_fits_the_budget_and_never_repeats_the_current_session(self):
        d = committed_repo()
        self.previous(d, "feat/a", "\n".join(f"Fait {i} : " + "x" * 400 for i in range(8)), "s1")
        out = context(start(d, session_id="s2"))
        self.assertLessEqual(len(out), 2000)
        self.assertIn("Kwa, reprise de session", out)
        self.assertEqual(context(start(d, session_id="s1")), "", "la session en cours n'est pas sa propre reprise")

    def test_resume_flags_old_entries_and_gone_branches(self):
        d = committed_repo()
        self.previous(d, "feat/a", "Objectif : ancien", "s1", days_ago=30)
        sh("git", "-C", d, "checkout", "-q", "main")
        sh("git", "-C", d, "branch", "-D", "feat/a")
        out = context(start(d, session_id="s2"))
        self.assertIn("ancienne : 30 jours", out)
        self.assertIn("branche supprimée ou fusionnée", out)

    def test_resume_shows_automatic_entries_without_inventing_a_story(self):
        d = committed_repo()
        start(d, session_id="s1")
        open(os.path.join(d, "a.ts"), "w").write("x")
        hook("journal-end.py", d, {"session_id": "s1"})
        out = context(start(d, session_id="s2"))
        self.assertIn("Fermée sans journal", out)
        self.assertIn("Fichiers touchés : 1", out)

    def test_pending_notes_are_reminded_and_journal_can_be_disabled(self):
        d = committed_repo()
        memory(d, "capture", "pref", "x")
        self.assertIn("/kwa-learn", context(start(d)))
        off = context(hook("memory-context.py", d, {"session_id": "z"}, env={"KWA_JOURNAL": "0"}))
        self.assertIn("1 note(s)", off)
        self.assertFalse(os.path.exists(os.path.join(local(d), "sessions", "z.json")))


class Signals(unittest.TestCase):
    def prompt(self, d, text, env=None):
        return hook("signal-prompt.py", d, {"prompt": text}, env)

    def inbox(self, d):
        try:
            return open(os.path.join(local(d), "inbox.md")).read()
        except OSError:
            return ""

    def test_explicit_marker_and_corrections_are_captured_silently(self):
        d = committed_repo()
        r = self.prompt(d, "retiens : le port de dev est 3100")
        self.assertEqual((r.returncode, r.stdout.strip(), r.stderr.strip()), (0, "", ""), "rien ne doit entrer dans le contexte")
        self.prompt(d, "non, utilise pnpm plutôt que npm")
        self.prompt(d, "ne fais pas de commit sans que je le demande")
        text = self.inbox(d)
        self.assertIn("[rule] le port de dev est 3100", text)
        self.assertIn("[pref] non, utilise pnpm", text)
        self.assertIn("[pref] ne fais pas de commit", text)

    def test_everything_else_is_ignored(self):
        d = committed_repo()
        for text in ["peux-tu regarder le fichier a.ts ?", "/kwa-learn", "<system-reminder>retiens : x</system-reminder>",
                     "non, " + "utilise " + "y" * 400, ""]:
            self.prompt(d, text)
        self.assertEqual(self.inbox(d), "")

    def test_secrets_are_masked_and_duplicates_dropped(self):
        d = committed_repo()
        self.prompt(d, f"retiens : la clé est {FAKE_PW}")
        self.prompt(d, f"retiens : la clé est {FAKE_PW}")
        text = self.inbox(d)
        self.assertNotIn("hunter2xyz", text)
        self.assertEqual(len(text.splitlines()), 1)

    def test_disabled(self):
        d = committed_repo()
        self.prompt(d, "retiens : x", env={"KWA_JOURNAL": "0"})
        self.assertEqual(self.inbox(d), "")

    def install_marker(self, d):
        os.makedirs(os.path.join(d, ".claude", "kwa"), exist_ok=True)
        open(os.path.join(d, ".claude", "kwa", "state.json"), "w").write("{}")

    def refuse(self, d, n=1):
        self.install_marker(d)
        payload = {"session_id": "sess-A", "cwd": d, "tool_name": "Bash", "tool_input": {"command": "git commit -m wip"}}
        out = None
        for _ in range(n):
            out = sh(sys.executable, os.path.join(HOOKS, "guard-git.py"), input=json.dumps(payload), env={"CLAUDE_PROJECT_DIR": d})
        return out

    def test_a_guard_refusal_leaves_a_signal(self):
        d = committed_repo({".claude/kwa.policy.json": json.dumps({"protected_branches": ["main"]})})
        self.assertIn('"deny"', self.refuse(d).stdout)
        rec = [json.loads(x) for x in open(os.path.join(local(d), "signals.jsonl"))]
        self.assertEqual((rec[0]["kind"], rec[0]["session"]), ("refus", "sess-A"))
        self.assertIn("main", rec[0]["key"])
        self.assertIn("git commit", rec[0]["text"])

    def test_a_refusal_outside_an_installation_leaves_nothing(self):
        d = committed_repo({".claude/kwa.policy.json": json.dumps({"protected_branches": ["main"]})})
        payload = {"session_id": "sess-A", "cwd": d, "tool_name": "Bash", "tool_input": {"command": "git commit -m wip"}}
        r = sh(sys.executable, os.path.join(HOOKS, "guard-git.py"), input=json.dumps(payload), env={"CLAUDE_PROJECT_DIR": d})
        self.assertIn('"deny"', r.stdout, "le garde refuse toujours")
        self.assertFalse(os.path.exists(os.path.join(local(d), "signals.jsonl")))

    def test_an_allowed_command_leaves_nothing(self):
        d = committed_repo()
        self.install_marker(d)
        payload = {"session_id": "sess-A", "cwd": d, "tool_name": "Bash", "tool_input": {"command": "git status"}}
        sh(sys.executable, os.path.join(HOOKS, "guard-git.py"), input=json.dumps(payload), env={"CLAUDE_PROJECT_DIR": d})
        self.assertFalse(os.path.exists(os.path.join(local(d), "signals.jsonl")))

    def test_digest_groups_repeated_refusals(self):
        d = committed_repo({".claude/kwa.policy.json": json.dumps({"protected_branches": ["main"]})})
        self.refuse(d, 3)
        out = memory(d, "digest").stdout
        self.assertIn("refus x3", out)
        self.assertIn("répété", out)


class Nudge(unittest.TestCase):
    def test_a_strong_signal_is_enough_and_it_asks_for_both(self):
        d = committed_repo()
        start(d)
        hook("signal-prompt.py", d, {"prompt": "non, utilise pnpm plutôt que npm"})
        os.remove(os.path.join(local(d), "inbox.md"))  # les notes ne comptent pas comme « déjà captées » ici
        r = hook("memory-nudge.py", d)
        self.assertEqual(r.returncode, 2)
        self.assertIn("journal", r.stderr)
        self.assertIn("/kwa-learn", r.stderr)
        self.assertEqual(hook("memory-nudge.py", d).returncode, 0, "une seule invitation par session")

    def work(self):
        """Un dépôt avec 4 fichiers de code non committés : du travail substantiel."""
        d = committed_repo()
        for i in range(4):
            os.makedirs(os.path.join(d, "src"), exist_ok=True)
            open(os.path.join(d, "src", f"f{i}.ts"), "w").write("x")
        return d

    def test_each_ask_is_dropped_when_already_satisfied(self):
        d = self.work()
        self.assertEqual(hook("memory-nudge.py", self.work()).returncode, 2, "sans rien de fait, l'invitation part")
        start(d)
        memory(d, "journal", "Objectif : déjà écrit")
        memory(d, "capture", "gotcha", "déjà noté")
        self.assertEqual(hook("memory-nudge.py", d).returncode, 0, "journal écrit et notes captées : rien à demander")
        d2 = self.work()
        start(d2)
        memory(d2, "journal", "Objectif : déjà écrit")
        r = hook("memory-nudge.py", d2)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("journal", r.stderr)
        self.assertIn("/kwa-learn", r.stderr)

    def test_old_markers_are_cleaned_at_session_start(self):
        d = committed_repo()
        os.makedirs(local(d))
        marker = os.path.join(local(d), "nudged-vieille")
        open(marker, "w").close()
        old = time.time() - 40 * 86400
        os.utime(marker, (old, old))
        start(d)
        self.assertFalse(os.path.exists(marker))


class Worktrees(unittest.TestCase):
    def test_journal_and_notes_live_in_the_main_repository(self):
        d = committed_repo()
        wt = os.path.join(os.path.dirname(d), "wt-" + os.path.basename(d))
        sh("git", "-C", d, "worktree", "add", "-q", "-b", "feat/x", wt)
        wt = os.path.realpath(wt)
        start(wt)
        memory(wt, "journal", "Objectif : depuis le worktree")
        memory(wt, "capture", "gotcha", "noté depuis le worktree")
        self.assertTrue(entries(d), "l'entrée est dans le dépôt principal")
        self.assertFalse(os.path.exists(os.path.join(wt, ".claude", "kwa", "local")))
        sh("git", "-C", d, "worktree", "remove", "--force", wt)
        self.assertIn("depuis le worktree", open(entries(d)[0]).read(), "le journal survit au worktree")
        self.assertIn("noté depuis le worktree", open(os.path.join(local(d), "inbox.md")).read())
        self.assertIn("feat/x", open(entries(d)[0]).read())


class Install(unittest.TestCase):
    def test_new_hooks_are_installed_and_checked(self):
        d = committed_repo()
        env = {"KWA_HOME": tempfile.mkdtemp()}
        self.assertEqual(sh(sys.executable, KWA, "install", d, "--modules", "core,memory", env=env).returncode, 0)
        s = json.load(open(os.path.join(d, ".claude", "settings.json")))
        for event in ("SessionStart", "Stop", "PreCompact", "SessionEnd", "UserPromptSubmit"):
            self.assertIn(event, s["hooks"], event)
        for name in ("_journal.py", "journal-compact.py", "journal-end.py", "signal-prompt.py"):
            self.assertTrue(os.path.isfile(os.path.join(d, ".claude", "kwa", "hooks", name)), name)
        self.assertEqual(json.load(open(os.path.join(d, ".claude", "kwa.policy.json")))["memory"]["journal_days"], 90)
        self.assertEqual(sh(sys.executable, KWA, "doctor", d, env=env).returncode, 0)

    def test_installed_copy_runs_end_to_end(self):
        d = committed_repo()
        env = {"KWA_HOME": tempfile.mkdtemp()}
        sh(sys.executable, KWA, "install", d, "--modules", "core,memory", env=env)
        hooks = os.path.join(d, ".claude", "kwa", "hooks")
        payload = json.dumps({"session_id": "e2e", "cwd": d, "prompt": "retiens : test de bout en bout"})
        e = {"CLAUDE_PROJECT_DIR": d}
        sh(sys.executable, os.path.join(hooks, "memory-context.py"), input=payload, env=e)
        sh(sys.executable, os.path.join(hooks, "signal-prompt.py"), input=payload, env=e)
        mem = os.path.join(d, ".claude", "kwa", "bin", "kwa-memory")
        self.assertEqual(sh(sys.executable, mem, "journal", "Objectif : installé", cwd=d, env=e).returncode, 0)
        self.assertIn("test de bout en bout", sh(sys.executable, mem, "pending", cwd=d, env=e).stdout)
        self.assertTrue(entries(d))


if __name__ == "__main__":
    unittest.main()
