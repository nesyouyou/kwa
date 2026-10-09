#!/usr/bin/env python3
"""Génère index.html : le gabarit + des données RÉELLES (gardes exécutés, manifeste, détection, tests).
    python3 docs/site/build.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.realpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(PACK, "tests"))
from helpers import BASH_GUARDS, HOOKS, RANK, make_repo  # noqa: E402

POLICY = os.path.join(PACK, "examples", "expo-monorepo.policy.json")

import importlib.machinery, importlib.util  # noqa: E402
_loader = importlib.machinery.SourceFileLoader("kwa_cli", os.path.join(PACK, "bin", "kwa"))
_spec = importlib.util.spec_from_loader("kwa_cli", _loader)
kwa = importlib.util.module_from_spec(_spec)
_loader.exec_module(kwa)


def verdict(guard, tool, tool_input, cwd, env=None):
    # GH=false : le garde ne doit jamais interroger le vrai GitHub, sinon la page dépend de l'état d'un dépôt réel
    e = {**os.environ, "GH": "false", "CLAUDE_PROJECT_DIR": cwd, **(env or {})}
    p = subprocess.run([sys.executable, os.path.join(HOOKS, guard)], input=json.dumps(
        {"tool_name": tool, "tool_input": tool_input, "cwd": cwd}), capture_output=True, text=True, env=e)
    if not p.stdout.strip():
        return "allow", ""
    o = json.loads(p.stdout)["hookSpecificOutput"]
    return o["permissionDecision"], o["permissionDecisionReason"].replace("Kwa — ", "")


def worst(cmd, cwd, env=None):
    best = ("allow", "")
    for g in BASH_GUARDS:
        v = verdict(g, "Bash", {"command": cmd}, cwd, env)
        if RANK[v[0]] > RANK[best[0]]:
            best = v
    return best


def examples():
    feat = make_repo(POLICY, branch="feat/12-filtre")
    main = make_repo(POLICY, branch="main")
    bash_cases = [
        ("Secrets", feat, "cat .env"), ("Secrets", feat, "cat .env.backup"), ("Secrets", feat, "bash -c 'cat .env'"),
        ("Secrets", feat, "env A=1 cat .env"), ("Secrets", feat, "cat .e''nv"), ("Secrets", feat, "gh auth token"),
        ("Secrets", feat, "cat .env.example"),
        ("Git", feat, "git push -u origin feat/12-filtre"), ("Git", feat, "git push --force origin feat/12-filtre"),
        ("Git", feat, "git push --force-with-lease origin feat/12-filtre"), ("Git", main, "git commit -m 'wip'"),
        ("Git", main, "git push origin main"), ("Git", feat, "git push origin HEAD:main"),
        ("Git", feat, "git reset --hard"), ("Git", feat, "gh pr merge 12 --squash"),
        ("Suppression", feat, "rm -rf build"), ("Suppression", feat, "rm -rf /usr/local/x"),
        ("Suppression", feat, "bash -c 'rm -rf /usr/local/x'"), ("Suppression", feat, "rm -rf .git"),
        ("Suppression", feat, "git clean -fd"), ("Suppression", feat, "rm -rf $(pwd)/../x"),
        ("Politique", feat, "npx prisma migrate reset"), ("Politique", feat, "npx prisma db push"),
        ("Politique", feat, "gh workflow run deploy.yml -f target=prod"), ("Politique", feat, "scw container container update abc image=x"),
        ("Politique", feat, "npx eas-cli submit --platform ios --latest"), ("Politique", feat, "grep -rn PROD_RESET_TOKEN docs/"),
        ("Politique", feat, "cat > note.md <<'EOF'\nun `prisma migrate reset` cité en doc\nEOF"),
        ("Politique", feat, "bash <<'EOF'\nnpx prisma migrate reset\nEOF"),
        ("Circuit PR", feat, "gh pr create --title t --body 'rien'"), ("Circuit PR", feat, "gh pr create --title t --body 'Closes #12'"),
    ]
    out = []
    for cat, repo, cmd in bash_cases:
        d, why = worst(cmd, repo)
        out.append({"cat": cat, "tool": "Bash", "input": cmd, "branch": "main" if repo == main else "feat/12-filtre", "decision": d, "why": why})
    write_cases = [
        ("Écriture", feat, "src/.env", None, "Edit"), ("Écriture", feat, "packages/db/prisma/migrations/2026_x/migration.sql", None, "Edit"),
        ("Écriture", main, "apps/web/page.tsx", None, "Edit"), ("Écriture", feat, "apps/web/page.tsx", None, "Edit"),
        ("Écriture", feat, "src/pay.ts", "const k = 'sk_live_" + "a" * 24 + "'", "Write"),
        ("Écriture", feat, "src/db.ts", "const url = 'postgres://app:s3cretpw@db.internal/x'", "Write"),
        ("Écriture", feat, ".claude/settings.json", None, "Edit"),
    ]
    for cat, repo, rel, content, tool in write_cases:
        ti = {"file_path": os.path.join(repo, rel), **({"content": content} if content else {"new_string": "x"})}
        d, why = verdict("guard-write.py", tool, ti, repo)
        shown = rel if not content else f"{rel} ← {content.replace('a' * 24, '…').replace('s3cretpw', '…')}"
        out.append({"cat": cat, "tool": tool, "input": shown, "branch": "main" if repo == main else "feat/12-filtre", "decision": d, "why": why})
    return out


def tests_count():
    r = subprocess.run([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
                       cwd=PACK, capture_output=True, text=True)
    m = re.search(r"Ran (\d+) tests", r.stderr)
    ok = "OK" in r.stderr.splitlines()[-1] if r.stderr.strip() else False
    return int(m.group(1)) if m else 0, ok


PARCOURS_TAIL = """<div class="pc-check"><h2>Vous avez compris si vous savez</h2><ul>
<li>dire pourquoi un fichier d'instructions ne contraint pas, et nommer ce qui contraint ;</li>
<li>prédire le verdict d'une commande, puis relier un garde à son entrée dans <code>settings.json</code> ;</li>
<li>ajouter une règle de projet et montrer qu'elle change un verdict ;</li>
<li>écrire l'en-tête d'une skill et lire l'échec d'un test ;</li>
<li>dire ce qu'aucun de ces garde-fous ne garantit, et quelle barrière complète.</li></ul>
<p class="kd-note" style="margin-top:18px">Pour les consignes de chaque outil, les documentations officielles font foi : <a href="https://code.claude.com/docs/en/memory">mémoire et instructions</a>, <a href="https://code.claude.com/docs/en/hooks">hooks</a>, <a href="https://code.claude.com/docs/en/settings">réglages</a>. Les commandes et les noms de réglages évoluent avec les versions : vérifiez avant une séance.</p></div>"""


def main():
    man = json.load(open(os.path.join(PACK, "manifest.json")))["modules"]
    mods = []
    for name, m in man.items():
        mods.append({"name": name, "about": m["about"], "always": bool(m.get("always")),
                     "files": [s["dest"] for _, s in kwa.module_files(m)],
                     "seeds": [s["dest"] for _, s in kwa.module_files(m) if s.get("seed")],
                     "hooks": [f"{ev}{' ' + e['matcher'] if e.get('matcher') else ''}" for ev, es in m.get("hooks", {}).items() for e in es],
                     "policy": list(m.get("policy", {}).keys())})
    n_tests, ok = tests_count()
    term = json.load(open(os.path.join(HERE, "src", "terminal-data.json"), encoding="utf-8"))
    detect = term["scenarios"][0]["steps"][0]["output"] if isinstance(term, dict) and "scenarios" in term else ""
    skills = sorted({s["dest"].split("/")[2] for m in man.values() for _, s in kwa.module_files(m)
                     if s["dest"].startswith(".claude/skills/")})
    catalog = []
    for d in sorted(os.listdir(os.path.join(PACK, "core", "skills"))):
        f = os.path.join(PACK, "core", "skills", d, "SKILL.md")
        if os.path.isfile(f):
            m = re.search(r"^description:\s*(.+)$", open(f, encoding="utf-8").read(), re.M)
            catalog.append({"id": d, "description": (m.group(1).strip().strip('"') if m else "")})
    data = {"credits": json.load(open(os.path.join(PACK, "credits.json"))), "catalog": catalog, "version": open(os.path.join(PACK, "VERSION")).read().strip(), "modules": mods, "examples": examples(),
            "tests": n_tests, "tests_ok": ok, "detect": detect, "skills": skills,
            "policy": json.load(open(POLICY)), "guards": sorted(f[:-3] for f in os.listdir(HOOKS) if f.startswith("guard-"))}
    src = os.path.join(HERE, "src")
    term_path = os.path.join(src, "terminal-data.json")
    data["terminal"] = json.load(open(term_path, encoding="utf-8")) if os.path.exists(term_path) else None
    sys.path.insert(0, src)
    import mapdata  # noqa: E402
    data["map"] = mapdata.build(sorted(os.listdir(os.path.join(PACK, "core", "skills"))) and
                                [d for d in sorted(os.listdir(os.path.join(PACK, "core", "skills")))
                                 if os.path.isfile(os.path.join(PACK, "core", "skills", d, "SKILL.md"))], data["credits"], {})
    open(os.path.join(HERE, "data.js"), "w", encoding="utf-8").write("window.KWA=" + json.dumps(data, ensure_ascii=False) + ";")

    def assets(names):
        css = "".join(f'<link rel="stylesheet" href="src/{n}.css">' for n in names if os.path.exists(os.path.join(src, n + ".css")))
        js = "".join(f'<script src="src/{n}.js"></script>' for n in names if os.path.exists(os.path.join(src, n + ".js")))
        return css, js

    tpl = open(os.path.join(HERE, "template.html"), encoding="utf-8").read()
    css, js = assets(["map", "board", "circuit", "terminal"])
    sys.path.insert(0, src)
    import shell, tree, pictos  # noqa: E402
    files = tree.project_files(man, kwa.module_files, {c["id"]: c["description"] for c in catalog})
    shown = [m for m in man if any(m in f["modules"] for f in files)]
    tpl = pictos.fill_placeholders(tpl).replace("/*PICTOS*/{}", pictos.as_json())
    index_html = (tpl.replace("<!--EXTRA_CSS-->", css).replace("<!--EXTRA_JS-->", js).replace("<!--TOPBAR-->", shell.topbar())
                  .replace("<!--SIDEBAR-->", shell.sidebar("index.html")).replace("<!--TREE-->", tree.section(files, shown, {m: man[m]["about"] for m in shown})))
    open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(index_html)

    # pages plein écran : même coquille (barre, thème, logo, pied) autour d'un seul widget
    head = re.search(r"<style>.*?</style>", tpl, re.S).group(0)
    foot = re.search(r"<footer.*?</footer>", tpl, re.S).group(0)
    theme_js = re.search(r"/\* thème : clair par défaut.*?/\* fin du bloc thème \*/\n", tpl, re.S).group(0)
    pages = {
        "skill-map.html": ("Carte des skills", "Carte interactive", "map", '<div id="map" data-deeplink></div>',
                           "DATA.map && KwaMap.mount($('#map'), DATA.map);"),
        "board.html": ("Le circuit", "Une demande, de bout en bout", "board+circuit", '<div id="board-root"></div>', "KwaCircuit.mount($('#board-root'));"),
        "terminal.html": ("Le terminal", "Comment on l'utilise", "terminal", '<div id="term-root"></div>', "KwaTerminal.mount($('#term-root'), DATA.terminal);"),
    }
    sys.path.insert(0, src)
    import parcours  # noqa: E402
    stages = parcours.collect(PACK, verdict, worst, make_repo, POLICY)[0]
    import parcours_pages  # noqa: E402
    pages["parcours.html"] = ("Parcours d'apprentissage", "Trois parcours, du modèle au harness", "parcours", parcours_pages.hub(), "")
    pages["parcours-culture.html"] = ("Parcours 1 : Culture IA générative", "Comprendre le modèle", "parcours", parcours_pages.culture(), "")
    pages["parcours-contexte.html"] = ("Parcours 2 : Context engineering", "Donner le bon contexte", "parcours", parcours_pages.contexte(), "")
    pages["parcours-harness.html"] = ("Parcours 3 : Harness", "Encadrer l'agent", "parcours", parcours_pages.harness(parcours.render(stages) + PARCOURS_TAIL), "")
    for fname, (title, eyebrow, widget, mount_html, mount_js) in pages.items():
        wcss, wjs = assets(widget.split('+'))
        html = f"""<!doctype html>
<html lang="fr" data-theme="dark"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" type="image/svg+xml" href="assets/favicon.svg">
<title>{title} | Kwa</title>
<script>try{{if(localStorage.getItem('kwa-docs-theme')==='light')document.documentElement.dataset.theme='light'}}catch(e){{}}</script>
<link rel="stylesheet" href="style/fonts.css"><link rel="stylesheet" href="style/tokens.css"><link rel="stylesheet" href="style/base.css"><link rel="stylesheet" href="src/shell.css">{wcss}
{head}</head>
<body class="kw">
{shell.topbar()}
<div class="kd-layout">{shell.sidebar(fname, parcours_pages.TOC.get(fname))}<div class="kd-main">
<main class="kw-container pc-wrap" data-acc="{fname.replace('parcours-','').replace('.html','')}" style="padding-top:32px">
  <div class="kd-eyebrow">{eyebrow}</div>
  <h1 class="kw-page-title">{title}</h1>
  {mount_html}
</main>
</div></div>
{foot}
<script src="data.js"></script>{wjs}<script src="src/shell.js"></script>
<script>
const DATA = window.KWA;
const $ = (s, r=document) => r.querySelector(s);
{theme_js}
$('#ver2').textContent = DATA.version; $('#tests').textContent = `${{DATA.tests}} tests ${{DATA.tests_ok ? 'au vert' : 'en échec'}}`;
{mount_js}
</script></body></html>"""
        open(os.path.join(HERE, fname), "w", encoding="utf-8").write(html)
    # contrôle de syntaxe des scripts inline des pages générées (une apostrophe oubliée casse toute la page)
    import shutil, tempfile
    if shutil.which("node"):
        for page in ["index.html", "skill-map.html", "board.html", "terminal.html", "parcours.html", "parcours-culture.html", "parcours-contexte.html", "parcours-harness.html"]:
            for i, code in enumerate(re.findall(r"<script>(.*?)</script>", open(os.path.join(HERE, page), encoding="utf-8").read(), re.S)):
                with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
                    f.write(code)
                r = subprocess.run(["node", "--check", f.name], capture_output=True, text=True)
                os.unlink(f.name)
                if r.returncode != 0:
                    sys.exit(f"erreur de syntaxe JS dans {page} (script {i}) :\n{r.stderr[:400]}")
    d = data["examples"]
    print(f"index.html — {len(mods)} modules, {len(skills)} skills, {len(d)} exemples réels "
          f"({sum(x['decision']=='deny' for x in d)} refus, {sum(x['decision']=='ask' for x in d)} demandes, "
          f"{sum(x['decision']=='allow' for x in d)} passages), {n_tests} tests {'OK' if ok else 'EN ÉCHEC'}")


if __name__ == "__main__":
    main()
