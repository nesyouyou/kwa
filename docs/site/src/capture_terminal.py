#!/usr/bin/env python3
"""Capture des sorties RÉELLES de Kwa pour le widget « terminal » de la documentation.

    python3 docs/site/src/capture_terminal.py

Pour chaque scénario, des projets JETABLES sont créés dans un dossier temporaire ; les vraies commandes de Kwa
(bin/kwa, core/bin/*, core/hooks/*.py) y sont exécutées ; commandes et sorties sont écrites dans
docs/site/src/terminal-data.json. Le script est relançable et déterministe : chemins temporaires remplacés par
`~/mon-projet`, dates, horodatages et sauvegardes `.bak-…` normalisés. Aucun projet réel n'est touché, aucune action
git hors des dépôts jetables. Bibliothèque standard uniquement.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[2]
OUT = HERE / "terminal-data.json"
DAY = "2026-10-07"  # date figée dans les sorties (kwa-memory date ses notes du jour)

BASE_ENV = {k: v for k, v in os.environ.items() if k.startswith(("LC_", "LANG")) or k in {"PATH", "HOME"}}
BASE_ENV["GH"] = "false"  # jamais le vrai GitHub : la capture doit être la même partout
BASE_ENV.update({
    "GIT_AUTHOR_NAME": "Demo", "GIT_AUTHOR_EMAIL": "demo@example.test",
    "GIT_COMMITTER_NAME": "Demo", "GIT_COMMITTER_EMAIL": "demo@example.test",
    "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "PYTHONDONTWRITEBYTECODE": "1",
    "NO_COLOR": "1", "PYTHONUTF8": "1",
})


class Sandbox:
    """Un dossier temporaire contenant `mon-projet/` ; sait normaliser tout ce qui pourrait trahir la machine."""

    def __init__(self, extra_env: dict | None = None):
        self.base = Path(tempfile.mkdtemp(prefix="kwa-capture-")).resolve()
        self.proj = self.base / "mon-projet"
        self.proj.mkdir()
        self.home = self.base / "kwa-home"
        self.home.mkdir()
        self.env = {**BASE_ENV, "KWA_HOME": str(self.home), **(extra_env or {})}

    def put(self, files: dict[str, str]) -> None:
        for rel, text in files.items():
            p = self.proj / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.proj), *args], env=self.env, check=True, capture_output=True)

    def norm(self, text: str) -> str:
        roots = {str(self.base), str(self.base.resolve()), "/private" + str(self.base), str(self.base).replace("/private", "")}
        for r in sorted(roots, key=len, reverse=True):
            text = text.replace(r + "/mon-projet", "~/mon-projet").replace(r, "~")
        text = re.sub(r"\.bak-\d{8,14}", ".bak-AAAAMMJJHHMMSS", text)
        text = re.sub(r"\b\d{8}-\d{6}\b", "AAAAMMJJ-HHMMSS", text)
        text = re.sub(r"\[\d{4}-\d{2}-\d{2}\]", f"[{DAY}]", text)
        text = text.replace(str(PACK), "<pack-kwa>")
        return "\n".join(l.rstrip() for l in text.rstrip("\n").split("\n")) if text.strip() else ""

    def real(self, display: str) -> str:
        """Commande affichée -> commande exécutée (alias du pack, chemin du projet)."""
        cmd = display.replace("~/mon-projet", str(self.proj))
        cmd = re.sub(r"\bpython3 ", f"{sys.executable} ", cmd)
        cmd = re.sub(r"(^|&& )kwa-memory\b", rf"\1{sys.executable} {PACK}/core/bin/kwa-memory", cmd)
        cmd = re.sub(r"(^|&& )kwa-hygiene\b", rf"\1{sys.executable} {PACK}/core/bin/kwa-hygiene", cmd)
        cmd = re.sub(r"(^|&& )kwa\b", rf"\1{sys.executable} {PACK}/bin/kwa", cmd)
        return cmd.strip()

    def step(self, display: str, explain: dict, cwd: str = "parent", empty_note: str | None = None,
             env: dict | None = None) -> dict:
        workdir = self.base if cwd == "parent" else self.proj
        e = {**self.env, "CLAUDE_PROJECT_DIR": str(self.proj), **(env or {})}
        r = subprocess.run(self.real(display), shell=True, cwd=workdir, env=e, capture_output=True, text=True)
        out = self.norm(r.stdout + r.stderr)
        st = {"cwd": "~" if cwd == "parent" else "~/mon-projet", "cmd": display, "output": out, "code": r.returncode,
              "explain": explain}
        if empty_note and not out:
            st["empty_note"] = empty_note
        return st

    def setup(self, display: str, cwd: str = "project") -> None:
        subprocess.run(self.real(display), shell=True, cwd=self.proj if cwd == "project" else self.base,
                       env=self.env, check=True, capture_output=True)

    def close(self) -> None:
        shutil.rmtree(self.base, ignore_errors=True)


def ex(title: str, *body: str) -> dict:
    return {"title": title, "body": list(body)}


# --------------------------------------------------------------------------- scénario 1

def fake_monorepo(sb: Sandbox) -> None:
    sb.put({
        "package.json": json.dumps({"name": "mon-projet", "private": True, "workspaces": ["apps/*"],
                                    "scripts": {"typecheck": "tsc --noEmit", "lint": "eslint .", "test": "vitest run",
                                                "db:generate": "prisma generate"}}, indent=2),
        "pnpm-workspace.yaml": "packages:\n  - 'apps/*'\n",
        "pnpm-lock.yaml": "lockfileVersion: '9.0'\n",
        "apps/web/package.json": json.dumps({"name": "web", "dependencies": {"next": "15.0.0", "prisma": "6.0.0"}}),
        "apps/web/src/page.tsx": "export default function Page() { return null }\n",
        "apps/mobile/package.json": json.dumps({"name": "mobile", "dependencies": {"expo": "52.0.0"}}),
        "apps/mobile/eas.json": json.dumps({"build": {"development": {}, "preview": {}, "production-testflight": {}}}),
        "prisma/migrations/0001_init/migration.sql": "-- migration factice\n",
        ".github/workflows/deploy.yml": "name: deploy\non: push\njobs:\n  d:\n    runs-on: ubuntu-latest\n"
                                        "    steps:\n      - run: scw container deploy $SCW_CONTAINER_ID\n",
        ".claude/hooks/guard-bash.sh": "#!/bin/sh\n# garde maison, antérieur à Kwa\n",
    })
    sb.setup("git init -q -b main .")


def scenario_install() -> dict:
    sb = Sandbox()
    try:
        fake_monorepo(sb)
        steps = [
            sb.step("kwa detect ./mon-projet", ex(
                "Lire le projet, **sans rien écrire**",
                "`kwa detect` parcourt le dossier : gestionnaire de paquets (**pnpm**), monorepo, `eas.json`, "
                "dossier `prisma/migrations`, workflows GitHub qui parlent de Scaleway.",
                "Chaque indice allume un **module** (`verify`, `stack-expo`, `stack-prisma`, `deploy`…) et pré-remplit la "
                "**politique** du projet. Le module `client-handover` est seulement proposé : il dépend d'une intention, "
                "jamais d'une détection.")),
            sb.step("kwa install ./mon-projet --dry-run", ex(
                "**Simuler** avant de toucher",
                "Même calcul que l'installation, mais **rien n'est écrit**. On voit les fichiers qui seraient ajoutés, "
                "le bloc géré d'`AGENTS.md`, la politique créée, les hooks branchés dans `settings.json`.",
                "C'est le moment de relire : le préfixe `[simulation]` rappelle que le dépôt est intact.")),
            sb.step("kwa install ./mon-projet", ex(
                "Installer le **socle**",
                "Les gardes, règles et skills sont copiés dans `.claude/`. `AGENTS.md` reçoit un bloc balisé "
                "(`kwa:begin` / `kwa:end`) : rien en dehors des marqueurs n'est modifié. `CLAUDE.md` devient un "
                "pointeur vers `@AGENTS.md`.",
                "La politique `.claude/kwa.policy.json` est **créée une fois** puis appartient au projet : une "
                "réinstallation ne l'écrase jamais.",
                "La dernière ligne le dit : Kwa n'ajoute, ne commite et ne pousse rien.")),
            sb.step("kwa doctor ./mon-projet", ex(
                "Vérifier la **conformité**",
                "`doctor` contrôle le bloc `AGENTS.md`, les hooks, la politique, et signale les **doublons** avec "
                "l'outillage maison du projet.",
                "Ici, le `guard-bash.sh` préexistant fait doublon avec les gardes de Kwa : c'est une note, pas une "
                "erreur. Code de sortie 0 : la cible est conforme.")),
        ]
        return {"id": "install", "title": "Détecter et installer",
                "summary": "De `detect` à `doctor` : installer le socle sur un monorepo pnpm, sans rien committer.",
                "prep": "Projet jetable : monorepo pnpm (scripts typecheck / lint / test), `apps/web` Next + Prisma, "
                        "`apps/mobile` Expo avec `eas.json`, `prisma/migrations`, workflow de déploiement Scaleway, "
                        "un ancien garde `.claude/hooks/guard-bash.sh`. Dépôt git initialisé sur `main`.",
                "steps": steps}
    finally:
        sb.close()


# --------------------------------------------------------------------------- scénario 2

def payload(cmd: str) -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}, "cwd": "~/mon-projet"}, ensure_ascii=False)


def guard_step(sb: Sandbox, guard: str, cmd: str, explain: dict, pretty: bool = True) -> dict:
    display = f"echo '{payload(cmd)}' | python3 .claude/kwa/hooks/{guard}.py"
    if pretty:
        display += " | python3 -m json.tool --no-ensure-ascii"
    return sb.step(display, explain, cwd="project",
                   empty_note="(aucune sortie : le garde n'a pas d'objection, la commande passe)")


def scenario_guards() -> dict:
    sb = Sandbox()
    try:
        sb.put({"package.json": json.dumps({"name": "mon-projet", "scripts": {"lint": "eslint ."}}),
                "pnpm-lock.yaml": "", "src/index.ts": "export {}\n", ".env": "SECRET_TOKEN=valeur-factice\n",
                ".env.example": "SECRET_TOKEN=\n"})
        sb.setup("git init -q -b main .")
        sb.setup("kwa install ./mon-projet --modules core", cwd="parent")
        steps = [
            guard_step(sb, "guard-secrets", "cat .env", ex(
                "Un fichier de secrets : **refusé**",
                "Claude Code envoie à chaque appel d'outil une **charge utile JSON** sur l'entrée standard du garde. "
                "Ici : l'outil `Bash` veut lancer `cat .env`.",
                "`guard-secrets` reconnaît un fichier de secrets et répond **`deny`** avec une raison. "
                "L'agent ne voit jamais le contenu du fichier.")),
            guard_step(sb, "guard-git", "git push origin main", ex(
                "Pousser sur main : **refusé**",
                "`guard-git` lit la branche courante et la liste des branches protégées. Un push dont la cible est "
                "`main` est **`deny`** : le travail passe par une branche et une PR.",
                "L'exception existe (`KWA_ALLOW_MAIN=1`), mais elle doit être assumée par un humain.")),
            guard_step(sb, "guard-git", "git push origin feat/ma-branche", ex(
                "Pousser une branche : **on demande**",
                "Un push de branche n'est pas interdit, mais il **sort** de la machine. Le garde répond **`ask`** : "
                "Claude Code affiche la demande et l'humain tranche.",
                "Trois niveaux, donc : `allow` (silence), `ask` (confirmer), `deny` (bloqué).")),
            guard_step(sb, "guard-delete", "rm -rf /usr/local/x", ex(
                "Supprimer hors du projet : **refusé**",
                "`guard-delete` résout le chemin réel de chaque cible de `rm`. Hors du projet et hors des dossiers "
                "temporaires, c'est **`deny`**. Même verdict pour `/`, `~`, `.git` ou `.claude/kwa`.")),
            guard_step(sb, "guard-secrets", "cat .env.example", ex(
                "Un gabarit public : **autorisé**",
                "`.env.example` ne contient pas de secret, c'est un modèle. Le garde **ne dit rien**, et ce silence "
                "est la décision `allow`.",
                "Les gardes sont des filets contre la bévue, pas un mur : ils restent assez précis pour ne pas "
                "gêner le travail normal."), pretty=False),
        ]
        return {"id": "guards", "title": "Un garde en action",
                "summary": "Les vrais gardes, alimentés par la charge utile que leur envoie Claude Code.",
                "prep": "Projet jetable sur la branche `main`, avec un `.env` factice, après `kwa install --modules core`. "
                        "La variable `CLAUDE_PROJECT_DIR` (posée par Claude Code) désigne le projet ; elle n'apparaît pas à "
                        "l'écran. La sortie passe par `json.tool` pour rester lisible.",
                "steps": steps}
    finally:
        sb.close()


# --------------------------------------------------------------------------- scénario 3

def scenario_memory() -> dict:
    sb = Sandbox()
    try:
        sb.put({"src/index.ts": "export {}\n", "README.md": "# mon-projet\n"})
        sb.setup("git init -q -b main .")
        sb.setup("git add -A")
        sb.setup("git commit -q -m init")
        sb.setup("git switch -q -c feat/export")
        sb.put({"src/export.ts": "export const exporter = () => {}\n"})
        with open(sb.proj / ".git" / "info" / "exclude", "a", encoding="utf-8") as f:
            f.write(".claude/kwa/local/\n")  # ce que fait `kwa install`
        steps = [
            sb.step('kwa-memory capture gotcha "Le seed Prisma échoue si la base n\'est pas migrée"', ex(
                "Noter un **piège**, sans quitter le travail",
                "Une note rapide, rangée par type : `gotcha` (piège), `decision`, `rule`, `pref` ou `vault`. Elle est "
                "datée et ajoutée à `.claude/kwa/local/inbox.md`.",
                "Ce dossier est **local** : exclu de git par `kwa install`. Rien n'est écrit dans la documentation du "
                "projet à ce stade."), cwd="project"),
            sb.step('kwa-memory capture decision "Pagination par curseur plutôt que par offset"', ex(
                "Une **décision**, même principe",
                "On capture au fil de l'eau, en une ligne. Le tri se fait **à la fin**, pas pendant."), cwd="project"),
            sb.step("kwa-memory pending", ex(
                "Voir ce qui **attend**",
                "Le nombre de notes puis leur liste. Si la session a produit du travail substantiel et qu'aucune note "
                "n'existe, un hook propose **une seule fois** de faire le point en fin de session."), cwd="project"),
            sb.step("kwa-memory digest", ex(
                "Tout pour **/kwa-learn**",
                "Le digest réunit les notes, la branche, les commits et les fichiers modifiés, puis rappelle les "
                "**destinations** : décisions, pièges, politique.",
                "C'est `/kwa-learn` qui propose les écritures et l'humain qui valide. La base de connaissance de l'équipe n'est touchée "
                "que si `KWA_VAULT_INBOX` est défini."), cwd="project"),
            sb.step("kwa-memory clear", ex(
                "**Archiver** les notes traitées",
                "Les notes sont déplacées dans `archive/`, horodatées. On repart d'une boîte vide : `pending` "
                "ne les montre plus."), cwd="project"),
            sb.step("kwa-memory pending", ex(
                "**Boîte** vide", "Le cycle est bouclé : capturer, trier, archiver."), cwd="project"),
        ]
        return {"id": "memory", "title": "Mémoire de session",
                "summary": "Capturer les apprentissages en passant, les trier à la fin.",
                "prep": "Dépôt git jetable avec un commit, sur la branche `feat/export`, un fichier non commité. "
                        "Le dossier de notes est exclu de git, comme après `kwa install`.",
                "steps": steps}
    finally:
        sb.close()


# --------------------------------------------------------------------------- scénario 4

def scenario_hygiene() -> dict:
    sb = Sandbox()
    try:
        sb.put({
            "src/config.ts": 'export const apiKey = "demo_0123456789abcdefghij"\n',
            "src/admin.ts": "export const admin = 'jean.dupont@gmail.com'\n",
            "src/legacy.ts": "export const contact = 'support.perso@gmail.com'\n",
            "docs/notes.md": "contact : x@gmail.com\n",
        })
        sb.setup("git init -q -b main .")
        sb.setup("git add -A")
        steps = [
            sb.step("kwa-hygiene", ex(
                "Contrôler **avant** de remettre au client",
                "Le contrôle porte sur les fichiers **produit** suivis par git (hors tests, hors `docs/`, hors Kwa). "
                "Quatre familles : `SECRET`, `PERSONNEL`, `NOMINATIF`, `PÉRISSABLE`.",
                "Les deux premières sont **bloquantes** : un identifiant en dur, deux comptes gmail. Les adresses sont "
                "masquées dans le rapport lui-même. Code de sortie 1."), cwd="project"),
            sb.step("echo 'export const apiKey = process.env.API_KEY' > src/config.ts", ex(
                "Corriger le **secret**",
                "La valeur sort du code : le produit la lira dans l'environnement. Le contrôle ne se laisse pas "
                "tromper par `process.env`, ni par les valeurs `changeme` ou `example`."), cwd="project"),
            sb.step("mkdir -p .claude && printf \"PERSONNEL\\tsrc/legacy.ts\\tà passer en variable d'env avant la remise\\n\" "
                    "> .claude/kwa.hygiene.allow", ex(
                "Assumer une **exception**, par écrit",
                "Un cas que l'on ne peut pas régler tout de suite va dans `.claude/kwa.hygiene.allow` : famille, "
                "fichier, raison. Ce n'est pas un silence : la liste est **réaffichée à chaque exécution**."),
                    cwd="project"),
            sb.step("kwa-hygiene", ex(
                "**Relancer**",
                "Reste un compte personnel (`admin.ts`) : toujours bloquant. L'exception sur `legacy.ts` est "
                "reportée, et sa justification s'affiche en bas.",
                "La liste d'exceptions **est** la checklist de remise."), cwd="project"),
            sb.step("echo \"export const admin = 'admin@exemple-client.fr'\" > src/admin.ts && git add -A && kwa-hygiene", ex(
                "Remplacer le compte par une adresse **du client**",
                "Plus d'occurrence bloquante : code de sortie 0. Les exceptions assumées restent listées, pour que la "
                "remise ne les oublie pas.",
                "Avec `--strict`, les avertissements (personne nommée, mesure datée) deviendraient bloquants aussi."),
                    cwd="project"),
        ]
        return {"id": "hygiene", "title": "Hygiène de remise",
                "summary": "Rien de personnel ni de secret ne part chez le client, et chaque exception est écrite.",
                "prep": "Faux dépôt : une clé en dur dans `src/config.ts`, deux comptes gmail, et une note dans `docs/` "
                        "(hors périmètre). Les fichiers sont ajoutés à l'index git, que le contrôle lit.",
                "steps": steps}
    finally:
        sb.close()


# --------------------------------------------------------------------------- scénario 5

def scenario_recommend() -> dict:
    sb = Sandbox()
    try:
        fake_monorepo(sb)
        (sb.home / ".claude" / "skills" / "aso").mkdir(parents=True)
        (sb.home / ".claude" / "skills" / "impeccable").mkdir(parents=True)
        steps = [
            sb.step("kwa recommend ./mon-projet", ex(
                "Quelles **skills** tierces pour cette stack ?",
                "La stack détectée (Expo, Next…) fait remonter une courte liste de skills utiles, avec la raison. "
                "`✓ présente` : déjà trouvée dans le dossier de skills de l'utilisateur, du projet ou dans un plugin. "
                "`✗ à installer` : absente.",
                "Dans cette démonstration, `KWA_HOME` pointe vers un dossier jetable qui contient seulement `aso` et "
                "`impeccable`.",
                "Kwa **n'installe rien** : relire la source d'une skill, puis l'installer à la main.")),
        ]
        steps[0]["cmd"] = "kwa recommend ./mon-projet"
        return {"id": "recommend", "title": "Recommander des skills",
                "summary": "Des skills tierces utiles pour la stack, sans en installer aucune.",
                "prep": "Le monorepo du premier scénario. `KWA_HOME` désigne un dossier jetable où seules `aso` et "
                        "`impeccable` sont déjà présentes : cela contrôle ce qui s'affiche comme déjà installé.",
                "steps": steps}
    finally:
        sb.close()


def main() -> int:
    version = (PACK / "VERSION").read_text().strip()
    data = {"kwa_version": version,
            "scenarios": [scenario_install(), scenario_guards(), scenario_memory(), scenario_hygiene(),
                          scenario_recommend()]}
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    OUT.write_text(text, encoding="utf-8")
    n = sum(len(s["steps"]) for s in data["scenarios"])
    print(f"{OUT.relative_to(PACK)} : {len(data['scenarios'])} scénarios, {n} étapes (kwa v{version})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
