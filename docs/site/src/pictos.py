"""Pictogrammes des grands concepts : garde (bouclier), skill (épée), agent (petite tête pixel), hook.

Un seul jeu, partagé par l'accueil, l'arborescence et les cartes de skills. Tracés propres à Kwa, sans dépendance.
"""
from __future__ import annotations

import json

PICTOS = {  # nom -> (style, contenu SVG sur une grille 24x24 ou 16x16)
    "shield": ("stroke", "24", '<path d="M12 3l7.5 3v5.2c0 4.6-3.1 8.2-7.5 9.8-4.4-1.6-7.5-5.2-7.5-9.8V6z"/><path d="m8.8 12 2.3 2.3 4.2-4.6"/>'),
    "sword": ("stroke", "24", '<path d="M21 3 10.2 16.2 7.8 13.8z"/><path d="M5.5 11.5l7 7"/><path d="M9 15l-3.5 3.5"/><circle cx="4.6" cy="19.4" r="1.1"/>'),
    "hook": ("stroke", "24", '<path d="M12 3v11"/><path d="M6 14a6 6 0 0 0 12 0"/><circle cx="12" cy="5" r="1.6"/>'),
    # petite tête d'agent en pixels : antenne, grosses joues, yeux et sourire en creux
    "agent": ("fill", "16", '<path fill-rule="evenodd" d="M7 1h2v3h4v1h1v1h1v4h-1v1h-1v1H3v-1H2v-1H1V6h1V5h1V4h4z'
                             'M5 6h2v3H5zM9 6h2v3H9zM7 10h2v1H7zM3 9h1v1H3zM12 9h1v1h-1z"/>'),
}


def svg(name: str, cls: str = "") -> str:
    style, grid, inner = PICTOS[name]
    return (f'<svg class="kd-pic p-{name}{" pic-fill" if style == "fill" else ""}{(" " + cls) if cls else ""}" '
            f'viewBox="0 0 {grid} {grid}" aria-hidden="true">{inner}</svg>')


def fill_placeholders(text: str) -> str:
    for name in PICTOS:
        text = text.replace("{{pic:%s}}" % name, svg(name))
    return text


def as_json() -> str:
    return json.dumps({n: svg(n) for n in PICTOS}, ensure_ascii=False)
