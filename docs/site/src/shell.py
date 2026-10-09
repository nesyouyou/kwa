"""Coquille commune du site : barre du haut et barre latérale de navigation, identiques sur toutes les pages."""
from __future__ import annotations

import html

SIDE = [  # (groupe, couleur du repère, [(libellé, cible)])
    ("Kwa", "blue", [("Présentation", "index.html#top"), ("Pourquoi ce projet", "index.html#pourquoi"), ("Arborescence", "index.html#arborescence"),
                     ("Démarrer", "index.html#demarrer")]),
    ("Explorer", "violet", [("Carte des skills", "skill-map.html"), ("Workflow d'une demande", "board.html"), ("Terminal", "terminal.html"),
                            ("Skills", "skills.html"), ("Gardes en action", "gardes.html"), ("Mémoire", "memoire.html")]),
    ("Apprendre", "green", [("Les trois parcours", "parcours.html"), ("1 · Culture IA générative", "parcours-culture.html"),
                            ("2 · Context engineering", "parcours-contexte.html"), ("3 · Harness", "parcours-harness.html")]),
    ("Référence", "amber", [("Méthode", "methode.html"), ("Remplacer l'existant", "migrer.html"), ("Limites et suite", "limites.html"),
                            ("Crédits", "credits.html")]),
]
ICONS = {  # tracés Lucide-like, 24x24, trait seul
    "Kwa": '<path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M10 20v-6h4v6"/>',
    "Explorer": '<circle cx="12" cy="12" r="9"/><path d="m15.5 8.5-2 5-5 2 2-5z"/>',
    "Apprendre": '<path d="M2 9l10-5 10 5-10 5z"/><path d="M6 11.5V16c0 1.2 2.7 3 6 3s6-1.8 6-3v-4.5"/>',
    "Référence": '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
}
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
        out.append(f'<div class="kd-sg"><h2><svg class="kd-ico" style="--dot:var(--kd-{color})" viewBox="0 0 24 24" aria-hidden="true">{ICONS[group]}</svg>{html.escape(group)}</h2><ul>')
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
