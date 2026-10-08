"""Politique d'exemple (monorepo web + API + mobile Expo) : cas représentatifs d'un harnais de garde-fous réel,
rejoués contre Kwa. Un push direct sur main est refusé (un outillage maison se contentait de demander)."""
import json
import os
import stat
import tempfile
import unittest

from helpers import call, chain, make_repo

POLICY = os.path.join(os.path.dirname(__file__), "..", "examples", "expo-monorepo.policy.json")


class Bash(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = make_repo(POLICY, branch="feat/12-x")

    def check(self, cmd, expected):
        self.assertEqual(chain(cmd, self.repo), expected, cmd)

    def test_deny(self):
        for cmd in ["pnpm --filter @myapp/db exec prisma migrate reset", "npx prisma db push",
                    "curl -X POST https://api/reprise/prod-reset -H 'x-token: t'",
                    "PROD_RESET_TOKEN=abc curl https://api/reprise/prod-reset",
                    "git push origin main -f", "git push --force origin feat/x",
                    "docker push registry.example.org/myapp-prod/api:abc",
                    "curl -X DELETE https://app.example.org/api/users/1"]:
            with self.subTest(cmd=cmd):
                self.check(cmd, "deny")

    def test_ask(self):
        for cmd in ["gh workflow run deploy.yml -f target=prod -f confirm=deploy-prod",
                    "scw container container update abc image=x", "npx eas-cli submit --platform ios --latest"]:
            with self.subTest(cmd=cmd):
                self.check(cmd, "ask")

    def test_main_push_is_stricter(self):
        self.check("git push origin main", "deny")

    def test_no_false_positive(self):
        for cmd in ["grep -rn PROD_RESET_TOKEN docs/", "grep -rn myapp-prod docs/", "pnpm db:migrate",
                    "pnpm --filter @myapp/api test", "gh workflow run deploy.yml -f target=recette",
                    "curl -fsS https://app.example.org/health", "git push -u origin feat/claude-setup",
                    "npx eas-cli build --platform ios --profile preview"]:
            with self.subTest(cmd=cmd):
                self.check(cmd, "allow")

    def test_heredoc_body_is_data_unless_executed(self):
        self.check("cat > s.md <<'EOF'\nUn `grep myapp-prod docs/` doit passer, un `prisma migrate reset` non.\nEOF", "allow")
        self.check("git commit -F - <<'MSG'\nchore: garde-fous — bloque prisma migrate reset et le push vers myapp-prod\nMSG", "allow")
        self.check("bash <<'EOF'\nnpx prisma migrate reset\nEOF", "deny")
        self.check("python3 - <<'PY'\nos.system('git push --force origin main')\nPY", "deny")
        self.check("sh <<'EOF'\ndocker push registry.example.org/myapp-prod/api:x\nEOF", "deny")


class GitHubCircuit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = make_repo(POLICY, branch="feat/12-x")
        cls.tmp = tempfile.mkdtemp()
        stub = os.path.join(cls.tmp, "gh")
        open(stub, "w").write('#!/bin/sh\ncase "$1 $2" in\n  "pr view") printf \'%s\' "$FAKE_PR" ;;\n  "issue view") printf \'%s\' "$FAKE_ISSUE" ;;\nesac\n')
        os.chmod(stub, os.stat(stub).st_mode | stat.S_IEXEC)
        open(os.path.join(cls.tmp, "avec.md"), "w").write("Closes #12\n\ncorps\n")
        open(os.path.join(cls.tmp, "sans.md"), "w").write("corps sans lien\n")

    def g(self, cmd, expected, pr="", issue=""):
        env = {"GH": os.path.join(self.tmp, "gh"), "FAKE_PR": pr, "FAKE_ISSUE": issue}
        self.assertEqual(chain(cmd, self.repo, env, ["guard-github.py"]), expected, cmd)

    def test_pr_create(self):
        self.g("gh pr create --title t --body 'rien'", "deny")
        self.g("gh pr create --title t --body 'Closes #12'", "allow")
        self.g("gh pr create --title t --body 'fixes #3 et le reste'", "allow")
        self.g(f"gh pr create --title t --body-file {self.tmp}/avec.md", "allow")
        self.g(f"gh pr create --title t --body-file {self.tmp}/sans.md", "deny")
        self.g(f"gh pr create -t t -F {self.tmp}/avec.md", "allow")
        self.g("gh pr view 12", "allow")

    def test_pr_merge(self):
        linked = '{"body":"Closes #5","comments":[],"closingIssuesReferences":[{"number":5}]}'
        self.g("gh pr merge 12 --squash", "deny", pr='{"body":"x","comments":[],"closingIssuesReferences":[]}')
        self.g("gh pr merge 12 --squash", "deny", pr=linked, issue="texte")
        self.g("gh pr merge 12", "deny", issue="",
               pr=json.dumps({"body": "Closes #5\n## Preuve\n<!-- modèle -->\n## Vérifications", "comments": [], "closingIssuesReferences": [{"number": 5}]}))
        self.g("gh pr merge 12 --squash", "allow", pr=linked, issue="![a](https://github.com/user-attachments/assets/0000)")
        self.g("gh pr merge 12", "allow", issue="",
               pr=json.dumps({"body": "Closes #5\n## Preuve\nTest rouge puis vert : 3 passed", "comments": [], "closingIssuesReferences": [{"number": 5}]}))


class Write(unittest.TestCase):
    def w(self, repo, rel, expected):
        self.assertEqual(call("guard-write.py", "Edit", {"file_path": os.path.join(repo, rel), "new_string": "x"}, repo), expected, rel)

    def test_paths(self):
        repo = make_repo(POLICY, branch="feat/12-x")
        self.w(repo, "packages/db/prisma/migrations/20260818_x/migration.sql", "deny")
        self.w(repo, "apps/api/.env", "deny")
        self.w(repo, ".env.example", "allow")
        self.w(repo, "packages/db/prisma/schema.prisma", "allow")
        self.w(repo, "apps/api/src/auth/email.service.ts", "allow")

    def test_no_code_on_main(self):
        repo = make_repo(POLICY, branch="main")
        os.makedirs(os.path.join(repo, "apps", "web"))
        os.makedirs(os.path.join(repo, "docs"))
        self.w(repo, "apps/web/page.tsx", "deny")
        self.w(repo, "packages/neuf/index.ts", "deny")
        self.w(repo, "docs/note.md", "allow")
        import subprocess
        subprocess.run(["git", "-C", repo, "checkout", "-q", "-b", "feat/12-my-portfolio-filter"], check=True)
        self.w(repo, "apps/web/page.tsx", "allow")


if __name__ == "__main__":
    unittest.main()
