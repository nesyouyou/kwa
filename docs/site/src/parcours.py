"""Parcours d'apprentissage : comprendre un harness en lisant et en cassant un vrai.

Chaque étape lance ses commandes pour de bon (dépôt jetable, gardes réels, tests réels) et vérifie le résultat attendu :
si une affirmation de la page cesse d'être vraie, le build échoue. Rien de ce qui est affiché n'est écrit à la main
sauf les consignes et les réponses expliquées.
"""
from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


def sh(cmd: list[str], cwd: str, env: dict | None = None, inp: str | None = None) -> str:
    p = subprocess.run(cmd, cwd=cwd, input=inp, capture_output=True, text=True, env={**os.environ, **(env or {})})
    return (p.stdout + p.stderr).strip()


def clean(text: str, tmp: str) -> str:
    """Retire le dossier temporaire des sorties affichées : le lecteur voit des chemins relatifs à son projet."""
    for base in sorted({tmp, os.path.realpath(tmp)}, key=len, reverse=True):  # le chemin réel d'abord : il contient l'autre
        text = text.replace(base + "/", "").replace(base, ".")
    return re.sub(r"\b[0-9a-f]{7}\b", "abc1234", text)  # empreintes git : elles changent à chaque génération


def expect(cond: bool, what: str) -> None:
    if not cond:
        sys.exit(f"parcours : l'affirmation « {what} » n'est plus vraie, corriger src/parcours.py")


def collect(pack: str, verdict, worst, make_repo, policy_example: str) -> list[dict]:
    kwa = os.path.join(pack, "bin", "kwa")
    tmp = tempfile.mkdtemp(prefix="kwa-parcours-")
    try:
        demo = os.path.join(tmp, "mon-projet")
        os.makedirs(demo)
        sh(["git", "init", "-q", "-b", "main"], demo)
        sh(["git", "config", "user.email", "demo@example.org"], demo)
        sh(["git", "config", "user.name", "demo"], demo)
        open(os.path.join(demo, "README.md"), "w").write("# mon-projet\n")
        open(os.path.join(demo, "package.json"), "w").write('{"name":"mon-projet","scripts":{"test":"echo ok"}}\n')
        sh(["git", "add", "-A"], demo)
        sh(["git", "commit", "-qm", "init"], demo)
        remote = os.path.join(tmp, "origin.git")
        sh(["git", "init", "-q", "--bare", remote], tmp)
        sh(["git", "remote", "add", "origin", remote], demo)
        sh(["git", "push", "-q", "origin", "main"], demo)
        installed = sh([sys.executable, kwa, "install", ".", "--modules", "core,memory,craft,issue-flow"], demo)
        expect("AGENTS.md : créé" in installed, "l'installation crée AGENTS.md")
        claude_md = open(os.path.join(demo, "CLAUDE.md")).read().strip()
        agents = open(os.path.join(demo, "AGENTS.md")).read().splitlines()
        block = [l for l in agents if l.strip()][:9]
        expect(claude_md == "@AGENTS.md", "CLAUDE.md est un pointeur vers AGENTS.md")

        hooks_dir = os.path.join(demo, ".claude", "kwa", "hooks")
        payload = {"tool_name": "Bash", "tool_input": {"command": "git commit -m wip"}, "cwd": "."}
        by_hand = sh([sys.executable, os.path.join(hooks_dir, "guard-git.py")], demo,
                     env={"CLAUDE_PROJECT_DIR": demo}, inp=json.dumps(payload))
        expect('"permissionDecision": "deny"' in by_hand, "un commit sur main est refusé par le garde")

        # étape 2 : prédire
        feat = make_repo(policy_example, branch="feat/12-filtre")
        main = make_repo(policy_example, branch="main")
        quiz = []
        for cwd, label, cmd in [(feat, "branche de travail", "cat .env"), (feat, "branche de travail", "cat .env.example"),
                                (feat, "branche de travail", "git push --force origin feat/12-filtre"),
                                (feat, "branche de travail", "rm -rf build"), (main, "branche main", "git commit -m 'wip'")]:
            d, why = worst(cmd, cwd)
            quiz.append({"where": label, "cmd": cmd, "decision": d, "reason": why})
        got = {q["cmd"]: q["decision"] for q in quiz}
        expect(got["cat .env"] == "deny" and got["cat .env.example"] == "allow" and got["rm -rf build"] == "allow",
               "les cinq cas du quiz ont les verdicts annoncés")

        # étape 3 : le branchement
        settings = json.load(open(os.path.join(demo, ".claude", "settings.json")))
        entry = next(e for e in settings["hooks"]["PreToolUse"] if any("guard-git.py" in h["command"] for h in e["hooks"]))
        entry_txt = json.dumps({"hooks": {"PreToolUse": [{"matcher": entry["matcher"], "hooks": [h for h in entry["hooks"] if "guard-git.py" in h["command"]]}]}}, indent=2, ensure_ascii=False)
        doctor_ok = sh([sys.executable, kwa, "doctor", "."], demo)
        for e in settings["hooks"]["PreToolUse"]:
            e["hooks"] = [h for h in e["hooks"] if "guard-git.py" not in h["command"]]
        sp = os.path.join(demo, ".claude", "settings.json")
        saved = open(sp).read()
        json.dump(settings, open(sp, "w"), indent=2)
        doctor_broken = sh([sys.executable, kwa, "doctor", "."], demo)
        by_hand_after = sh([sys.executable, os.path.join(hooks_dir, "guard-git.py")], demo,
                           env={"CLAUDE_PROJECT_DIR": demo}, inp=json.dumps(payload))
        open(sp, "w").write(saved)
        expect("non branchés" in doctor_broken and "conforme" in doctor_ok, "doctor détecte un garde non branché")
        expect('"deny"' in by_hand_after, "le script refuse toujours quand on l'appelle à la main")

        # étape 4 : la politique
        before = verdict("guard-policy.py", "Bash", {"command": "npm run deploy:prod"}, demo)
        pol_path = os.path.join(demo, ".claude", "kwa.policy.json")
        pol = json.load(open(pol_path))
        rule = {"id": "deploy-prod", "reason": "Le déploiement de production passe par la PR, pas par ce script.", "all": ["npm run deploy:prod"]}
        pol.setdefault("bash", {}).setdefault("deny", []).append(rule)
        json.dump(pol, open(pol_path, "w"), indent=2, ensure_ascii=False)
        after = verdict("guard-policy.py", "Bash", {"command": "npm run deploy:prod"}, demo)
        expect(before[0] == "allow" and after[0] == "deny", "une règle ajoutée à la politique change le verdict")

        # étape 5 : casser une skill
        copy = os.path.join(tmp, "pack")
        shutil.copytree(pack, copy, ignore=shutil.ignore_patterns(".git", "docs", "node_modules", "__pycache__"))
        bad = os.path.join(copy, "core", "skills", "demo")
        os.makedirs(bad)
        open(os.path.join(bad, "SKILL.md"), "w").write(
            "---\nname: kwa-demo\ndescription: Faire une démonstration. À lancer quand : on le demande.\n---\n\n# Démo\n")
        lint = sh([sys.executable, "-W", "ignore", "-m", "unittest", "tests.test_skills.Lint", "-q"], copy)
        lines = [l for l in lint.splitlines() if l.strip()]
        fail = [l for l in lines if l.startswith(("FAIL", "ERROR", "AssertionError", "AssertionError:")) or "AssertionError" in l]
        lint_out = "\n".join(fail[:3] + [lines[-1]]) if fail else "\n".join(lines[-4:])
        expect("FAILED" in lint or "Error" in lint, "une skill au frontmatter piégé fait échouer la suite")
        head = open(os.path.join(pack, "core", "skills", "rephrase", "SKILL.md")).read().split("---")[1].strip()

        # étape 6 : la mémoire
        mem = os.path.join(demo, ".claude", "kwa", "bin", "kwa-memory")
        sh([sys.executable, mem, "capture", "gotcha", "Les tests d'intégration ont besoin du fichier d'environnement local"], demo)
        pending = sh([sys.executable, mem, "pending"], demo)
        expect("tests d'intégration" in pending, "une note capturée apparaît dans les notes en attente")

        # étape 7 : le circuit
        start = os.path.join(demo, ".claude", "kwa", "bin", "kwa-start")
        started = sh([sys.executable, start, "feat", "status-filter", "Ajouter un filtre de statut", "--no-issue"], demo)
        trees = clean(sh(["git", "worktree", "list"], demo), tmp)
        expect("feat/status-filter" in started + trees, "kwa-start crée la branche dans un worktree")
        started = clean(started, tmp)

        # étape 8 : les limites
        holes = []
        for cmd in ["cat $(echo .e)nv", "cat .e*", "python3 -c \"print(open('.e" + "nv').read())\""]:
            d, _ = worst(cmd, feat)
            holes.append({"cmd": cmd, "decision": d})
        expect(all(h["decision"] == "allow" for h in holes), "les trois contournements passent bien (limite assumée)")

        return [{
            "installed": clean("\n".join(installed.splitlines()[:5]), tmp), "claude_md": claude_md, "block": "\n".join(block), "by_hand": by_hand,
            "quiz": quiz, "payload": json.dumps(payload), "entry": entry_txt, "doctor_ok": doctor_ok, "doctor_broken": doctor_broken,
            "by_hand_after": by_hand_after, "rule": json.dumps(rule, indent=2, ensure_ascii=False), "before": before, "after": after,
            "lint": lint_out, "skill_head": head, "pending": pending, "started": started, "trees": trees, "holes": holes,
        }]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def code(t: str) -> str:
    return f'<pre class="kd-code">{esc(t)}</pre>'


def cmd(t: str) -> str:
    return f'<pre class="kd-code"><span class="p">$</span> {esc(t)}</pre>'


def reveal(summary: str, body: str) -> str:
    return f'<details class="pc-reveal"><summary>{esc(summary)}</summary><div>{body}</div></details>'


def pill(d: str) -> str:
    return f'<span class="kd-pill {d}">{ {"deny": "refusé", "ask": "demande", "allow": "passe"}[d] }</span>'


def render(c: dict) -> str:
    q = c["quiz"]
    skill_block = code("---\n" + c["skill_head"] + "\n---")
    mem_cmd = cmd('kwa-memory capture gotcha "Les tests d\'intégration ont besoin du fichier d\'environnement local"')
    start_cmd = cmd('kwa-start feat status-filter "Ajouter un filtre de statut" --no-issue')
    echo_cmd = cmd("echo '" + c["payload"] + "' | python3 .claude/kwa/hooks/guard-git.py")
    quiz_rows = "".join(
        f'<tr><td><code>{esc(x["cmd"])}</code><br><small>{esc(x["where"])}</small></td>'
        f'<td>{reveal("Mon pronostic", pill(x["decision"]) + (" <small>" + esc(x["reason"]) + "</small>" if x["reason"] else ""))}</td></tr>'
        for x in q)
    holes = "".join(f'<tr><td><code>{esc(h["cmd"])}</code></td><td>{pill(h["decision"])}</td></tr>' for h in c["holes"])
    stages = [
        ("1", "Instructions et contrainte", "Ce que l'agent lit, et ce qui l'oblige.",
         f"""<p>Installez Kwa dans un dépôt jetable. Regardez ce qui est écrit pour l'agent, puis demandez-vous : quelle ligne l'empêche de committer sur <code>main</code> ?</p>
{cmd("kwa install ./mon-projet --modules core,memory,craft,issue-flow")}{code(c["installed"])}
<p><code>CLAUDE.md</code> contient une ligne, un pointeur vers le fichier commun :</p>{code(c["claude_md"])}
<p>Début du bloc géré de <code>AGENTS.md</code> :</p>{code(c["block"])}
{reveal("Réponse", "<p>Aucune ligne ne l'empêche. Un fichier d'instructions est du <strong>contexte</strong> : l'agent le lit et peut s'en écarter. Ce qui contraint, c'est un hook qui s'exécute avant l'outil. Voici le même commit, tenté sur <code>main</code>, quand le garde est appelé :</p>" + code(c["by_hand"]))}""",
         "Dire pourquoi une règle écrite ne suffit pas, et nommer ce qui la fait respecter.",
         "Le dossier <code>hooks/</code> ne fait rien tout seul : un hook n'existe que s'il est branché dans <code>settings.json</code> (étape 3)."),
        ("2", "Un garde, de la commande au verdict", "Un hook reçoit du JSON et répond refuse, demande ou laisse passer.",
         f"""<p>Un garde est un petit programme. Claude Code lui envoie ce que l'agent s'apprête à faire, il répond sur la sortie standard. Appelez-le à la main :</p>
{echo_cmd}
<p>Pas de sortie veut dire « laisse passer ». Avant de regarder les réponses, <strong>faites votre pronostic</strong> pour chaque commande, puis ouvrez :</p>
<table class="pc-table"><thead><tr><th>Commande</th><th>Verdict réel</th></tr></thead><tbody>{quiz_rows}</tbody></table>
<p class="kd-note">Verdicts calculés en exécutant les gardes à chaque génération de la page.</p>""",
         "Prédire le verdict d'une commande avant de l'exécuter, et lire la raison donnée.",
         "<code>.env.example</code> reste lisible : un garde trop large se fait contourner par agacement."),
        ("3", "Le branchement", "settings.json relie un événement à un script. Sans lui, rien n'est appelé.",
         f"""<p>Voici l'entrée qui relie le garde git à l'événement <code>PreToolUse</code> pour l'outil <code>Bash</code> :</p>{code(c["entry"])}
<p>Vérifiez l'état de l'installation :</p>{cmd("kwa doctor ./mon-projet")}{code(c["doctor_ok"])}
<p><strong>Cassez-le</strong> : supprimez cette entrée de <code>settings.json</code> sans toucher au script, puis relancez le diagnostic.</p>{code(c["doctor_broken"])}
{reveal("Que fait le script maintenant ?", "<p>Il refuse toujours quand on l'appelle à la main, mais plus personne ne l'appelle. Un garde qui existe sans être branché protège de rien.</p>" + code(c["by_hand_after"]))}""",
         "Suivre la chaîne événement, filtre d'outil, commande, trace, et repérer un garde non branché.",
         "Le chemin <code>$CLAUDE_PROJECT_DIR</code> se résout à la racine du projet ; ne pas recopier tel quel une variable propre aux plugins."),
        ("4", "La politique du projet", "Ce qui change d'un projet à l'autre tient dans un fichier, pas dans un script.",
         f"""<p>Les gardes sont communs, la politique est locale (<code>.claude/kwa.policy.json</code>). Dans le dépôt jetable, la commande <code>npm run deploy:prod</code> n'est pas gardée : {pill(c["before"][0])}</p>
<p>Ajoutez cette règle dans <code>bash.deny</code> :</p>{code(c["rule"])}
<p>Même commande, même garde, nouveau verdict : {pill(c["after"][0])}</p>{code(c["after"][1])}""",
         "Ajouter une règle de projet et prouver qu'elle change un verdict.",
         "Le refus l'emporte toujours sur la demande. Une politique trop stricte se contourne, une règle utile est précise."),
        ("5", "Une skill, et comment la casser", "Une procédure que l'agent déclenche ou que vous tapez.",
         f"""<p>Une skill est un fichier <code>SKILL.md</code> : un en-tête qui dit quand l'appeler, un corps qui dit comment. Celui de <code>/kwa-rephrase</code> :</p>{skill_block}
<p>Créez une skill dont la description contient « : » (un piège YAML qui tronque l'en-tête sans bruit), puis lancez la suite de contrôle des skills. Elle échoue deux fois : le premier échec est le piège YAML, le second rappelle qu'une skill doit être déclarée dans <code>manifest.json</code>.</p>{cmd("python3 -m unittest tests.test_skills.Lint")}{code(c["lint"])}
{reveal("Pourquoi ce test existe", "<p>Une description mal formée ne plante rien : la skill devient simplement introuvable. Un test qui échoue vaut mieux qu'une skill invisible.</p>")}""",
         "Écrire l'en-tête d'une skill et lire l'échec qui signale une erreur.",
         "Une description dit quand invoquer la skill, pas son déroulé : un agent qui lit les étapes saute le corps (voir <code>/kwa-agent-docs</code>)."),
        ("6", "La mémoire qui s'enrichit", "Noter pendant, trier à la fin, valider soi-même.",
         f"""<p>Capturez un piège rencontré pendant le travail, sans rien écrire dans la documentation :</p>
{mem_cmd}
{cmd("kwa-memory pending")}{code(c["pending"])}
<p>En fin de session, <code>/kwa-learn</code> propose où chaque note devrait vivre (documentation, politique, mémoire de l'agent). <strong>Rien n'est appliqué sans votre accord.</strong></p>""",
         "Capturer une note et dire qui décide de son destin.",
         "Les notes locales ne sont pas versionnées : elles sont exclues via <code>.git/info/exclude</code>."),
        ("7", "Le circuit complet", "Une demande, une branche, une preuve, une PR.",
         f"""<p>Démarrez un changement : une branche dans son propre worktree, à côté du dépôt, jamais sur <code>main</code>.</p>
{start_cmd}{code(c["started"])}{code(c["trees"])}
<p>La suite se joue avec les skills : <code>/kwa-brainstorm</code>, <code>/kwa-plan</code>, <code>/kwa-tdd</code>, <code>/kwa-verify</code>, <code>/kwa-review</code>, <code>/kwa-ship</code>. La page <a href="board.html">Board</a> déroule ce circuit sur une demande réelle, et le <a href="terminal.html">Terminal</a> montre les commandes.</p>""",
         "Conduire un petit changement jusqu'à une PR, avec une preuve que quelqu'un d'autre peut rejouer.",
         "Versionner n'est pas publier, et un commit n'est pas un déploiement. Chaque étape reste une décision."),
        ("8", "Les limites, sans maquillage", "Un garde est un filet contre la bévue, pas une frontière de sécurité.",
         f"""<p>Essayez de contourner le garde des secrets. Ces trois commandes lisent le même fichier d'environnement ; seule la forme change :</p>
<table class="pc-table"><thead><tr><th>Commande</th><th>Verdict réel</th></tr></thead><tbody>{holes}</tbody></table>
<p>Le garde lit le <strong>texte</strong> de la commande, il ne l'exécute pas : un nom calculé, un glob ou un interpréteur lui échappent.</p>
{reveal("Alors, à quoi ça sert, et que mettre en plus ?", "<p>À arrêter l'erreur honnête, pas l'attaque. Pour une vraie barrière : la protection de branche GitHub, et les règles <code>permissions.deny</code> de Claude Code, qui portent sur le fichier lui-même. Savoir ce qu'un outil ne garantit pas fait partie du métier.</p>")}""",
         "Trouver un contournement, et dire quelle barrière complète le garde.",
         "Ne jamais présenter un hook comme une garantie. Un contournement trouvé en séance est un bon résultat."),
    ]
    return "\n".join(stage(*st) for st in stages)


def stage(n: str, title: str, tag: str, body: str, proof: str, pitfall: str) -> str:
    return (f'<section class="pc-stage" id="etape-{n}"><div class="pc-num">{n}</div><div class="pc-main">'
            f'<h2 class="pc-h">{esc(title)}</h2><p class="pc-tag">{esc(tag)}</p>{body}'
            f'<div class="pc-proof"><div><b>Preuve attendue</b><p>{proof}</p></div><div><b>Piège</b><p>{pitfall}</p></div></div></div></section>')
