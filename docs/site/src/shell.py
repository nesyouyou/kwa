"""Coquille commune du site : barre du haut et barre latérale de navigation, identiques sur toutes les pages."""
from __future__ import annotations

import html

SIDE = [  # (groupe, couleur du repère, [(libellé, cible)])
    ("Kwa", "blue", [("Présentation", "index.html#top"), ("Pourquoi ce projet", "index.html#pourquoi"), ("Arborescence", "index.html#arborescence")]),
    ("Explorer", "violet", [("Carte des skills", "skill-map.html"), ("Circuit d'une demande", "board.html"), ("Terminal", "terminal.html")]),
    ("Apprendre", "green", [("Les trois parcours", "parcours.html"), ("1 · Culture IA générative", "parcours-culture.html"),
                            ("2 · Context engineering", "parcours-contexte.html"), ("3 · Harness", "parcours-harness.html")]),
    ("Référence", "amber", [("Démarrer", "index.html#demarrer"), ("Skills", "index.html#skills"), ("Gardes en action", "index.html#gardes"),
                            ("Mémoire", "index.html#memoire"), ("Méthode", "index.html#superpowers"), ("Remplacer l'existant", "index.html#migrer"),
                            ("Limites et suite", "index.html#limites"), ("Crédits", "index.html#credits")]),
]
PAGES = [t.split("#")[0] for _, _, items in SIDE for _, t in items]

# bouton de thème : icône seule (lune en clair, soleil en sombre, choisie en CSS)
THEME_BUTTON = '<button type="button" class="kd-theme" id="theme" aria-label="Passer en thème clair" title="Changer de thème"><svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M18.7 5.3l-1.6 1.6M6.9 17.1l-1.6 1.6"/></svg><svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.2 14.6A8.4 8.4 0 0 1 9.4 3.8a8.4 8.4 0 1 0 10.8 10.8z"/></svg></button>'



def topbar(theme_button: str = THEME_BUTTON) -> str:
    return ('<header class="kd-top"><button type="button" class="kd-menu" id="menu" aria-label="Ouvrir la navigation" aria-expanded="false" aria-controls="side">'
            '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button>'
            '<a class="kd-brand" href="index.html" aria-label="Kwa, accueil"><b class="kd-word">kwa</b><span>/ harness</span></a>'
            f'<span class="kd-spacer"></span>{theme_button}</header>')


def sidebar(current: str, toc: list[tuple[str, str]] | None = None) -> str:
    """current : nom du fichier de la page (index.html, board.html…). toc : (ancre, libellé) affichés sous l'entrée courante."""
    out = ['<aside class="kd-side" id="side" aria-label="Navigation"><nav>']
    for group, color, items in SIDE:
        out.append(f'<div class="kd-sg"><h2><i class="kd-dot" style="--dot:var(--kd-{color})"></i>{html.escape(group)}</h2><ul>')
        for label, target in items:
            page, _, frag = target.partition("#")
            same = page == current
            href = f"#{frag}" if same and frag else target
            active = same and not frag
            attrs = ' aria-current="page"' if active else ""
            spy = f' data-spy="{html.escape(frag)}"' if same and frag else ""
            out.append(f'<li><a href="{html.escape(href)}"{attrs}{spy}>{html.escape(label)}</a>')
            if active and toc:
                out.append('<ul class="kd-toc">' + "".join(f'<li><a href="#{html.escape(a)}" data-spy="{html.escape(a)}">{html.escape(t)}</a></li>' for a, t in toc) + "</ul>")
            out.append("</li>")
        out.append("</ul></div>")
    out.append('</nav></aside><div class="kd-scrim" id="scrim"></div>')
    return "".join(out)
