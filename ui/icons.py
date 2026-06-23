"""
Inline SVG Icons für VostiraView.
Alle Icons 24×24, flacher Stil, einheitliche Farbpalette.
"""
from functools import lru_cache

from PyQt6.QtCore import QByteArray, Qt
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer


def _icon_from_svg(svg: str, size: int = 24) -> QIcon:
    """Rendert einen SVG-String zu einem QIcon."""
    renderer = QSvgRenderer(QByteArray(svg.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


# ── Farb-Palette ──────────────────────────────────────────────────────────────
# Blau    #4A90D9  Navigation, Ansicht
# Grün    #5CB85C  Bestätigen, Speichern
# Orange  #F0A500  Bearbeitung
# Rot     #D94A4A  Löschen, Warnung
# Lila    #8B5CF6  Slideshow, Zoom
# Grau    #6B7280  Neutral, Sort

@lru_cache(maxsize=None)
def icon_prev():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="11" fill="#4A90D9" opacity="0.15"/>
  <polyline points="14,7 9,12 14,17" fill="none" stroke="#4A90D9" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_next():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="11" fill="#4A90D9" opacity="0.15"/>
  <polyline points="10,7 15,12 10,17" fill="none" stroke="#4A90D9" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_slideshow_play():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="11" fill="#8B5CF6" opacity="0.15"/>
  <polygon points="9,7 19,12 9,17" fill="#8B5CF6"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_slideshow_stop():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="12" cy="12" r="11" fill="#8B5CF6" opacity="0.15"/>
  <rect x="8" y="7" width="3" height="10" rx="1" fill="#8B5CF6"/>
  <rect x="13" y="7" width="3" height="10" rx="1" fill="#8B5CF6"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_fullscreen():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="2" y="2" width="20" height="20" rx="2" fill="#4A90D9" opacity="0.12"/>
  <polyline points="8,3 3,3 3,8"   fill="none" stroke="#4A90D9" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="16,3 21,3 21,8"  fill="none" stroke="#4A90D9" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="3,16 3,21 8,21"  fill="none" stroke="#4A90D9" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="21,16 21,21 16,21" fill="none" stroke="#4A90D9" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_viewer():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="2" y="3" width="20" height="16" rx="2" fill="#4A90D9" opacity="0.15"
        stroke="#4A90D9" stroke-width="1.5"/>
  <circle cx="9" cy="10" r="3" fill="none" stroke="#4A90D9" stroke-width="1.8"/>
  <path d="M14 14 l5 4" stroke="#4A90D9" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="14" y1="8" x2="19" y2="8" stroke="#4A90D9" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="14" y1="11" x2="17" y2="11" stroke="#4A90D9" stroke-width="1.5" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_gallery():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="2"  y="2"  width="9" height="9" rx="1.5" fill="#4A90D9" opacity="0.7"/>
  <rect x="13" y="2"  width="9" height="9" rx="1.5" fill="#4A90D9" opacity="0.5"/>
  <rect x="2"  y="13" width="9" height="9" rx="1.5" fill="#4A90D9" opacity="0.5"/>
  <rect x="13" y="13" width="9" height="9" rx="1.5" fill="#4A90D9" opacity="0.3"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_list_view():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="2" y="4"  width="4" height="4" rx="1" fill="#4A90D9"/>
  <line x1="9" y1="6"  x2="22" y2="6"  stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
  <rect x="2" y="10" width="4" height="4" rx="1" fill="#4A90D9"/>
  <line x1="9" y1="12" x2="22" y2="12" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
  <rect x="2" y="16" width="4" height="4" rx="1" fill="#4A90D9"/>
  <line x1="9" y1="18" x2="22" y2="18" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_search():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="10" cy="10" r="7" fill="none" stroke="#6B7280" stroke-width="2"/>
  <line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#6B7280" stroke-width="2.5"
        stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_save_as():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="3" y="3" width="18" height="18" rx="2" fill="#5CB85C" opacity="0.15"
        stroke="#5CB85C" stroke-width="1.5"/>
  <rect x="7" y="3" width="10" height="6" rx="1" fill="#5CB85C" opacity="0.5"/>
  <rect x="6" y="13" width="12" height="7" rx="1" fill="#5CB85C" opacity="0.4"/>
  <line x1="12" y1="10" x2="12" y2="16" stroke="#5CB85C" stroke-width="2" stroke-linecap="round"/>
  <polyline points="9,13 12,16 15,13" fill="none" stroke="#5CB85C" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_rename():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="3" y="14" width="13" height="6" rx="1.5" fill="#F0A500" opacity="0.2"
        stroke="#F0A500" stroke-width="1.5"/>
  <path d="M14 3 l7 7 -9 9 H5 v-7 Z" fill="#F0A500" opacity="0.25"
        stroke="#F0A500" stroke-width="1.5" stroke-linejoin="round"/>
  <line x1="12" y1="5" x2="19" y2="12" stroke="#F0A500" stroke-width="1.5"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_copy():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="8" y="2" width="13" height="15" rx="2" fill="#6B7280" opacity="0.15"
        stroke="#6B7280" stroke-width="1.5"/>
  <rect x="3" y="7" width="13" height="15" rx="2" fill="white"
        stroke="#6B7280" stroke-width="1.5"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_cut():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="6"  cy="18" r="3" fill="none" stroke="#6B7280" stroke-width="1.8"/>
  <circle cx="18" cy="18" r="3" fill="none" stroke="#6B7280" stroke-width="1.8"/>
  <line x1="12" y1="12" x2="3"  y2="3"  stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
  <line x1="12" y1="12" x2="21" y2="3"  stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
  <line x1="9"  y1="15" x2="6"  y2="15.5" stroke="#6B7280" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="15" y1="15" x2="18" y2="15.5" stroke="#6B7280" stroke-width="1.8" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_delete():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <polyline points="3,6 5,6 21,6" stroke="#D94A4A" stroke-width="1.8"
            stroke-linecap="round"/>
  <path d="M19 6 L18 20 a1 1 0 0 1-1 1 H7 a1 1 0 0 1-1-1 L5 6"
        fill="#D94A4A" opacity="0.15" stroke="#D94A4A" stroke-width="1.8"
        stroke-linejoin="round"/>
  <path d="M9 6 V4 a1 1 0 0 1 1-1 h4 a1 1 0 0 1 1 1 v2"
        fill="none" stroke="#D94A4A" stroke-width="1.8" stroke-linejoin="round"/>
  <line x1="10" y1="11" x2="10" y2="17" stroke="#D94A4A" stroke-width="1.8" stroke-linecap="round"/>
  <line x1="14" y1="11" x2="14" y2="17" stroke="#D94A4A" stroke-width="1.8" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_crop():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <polyline points="6,2 6,18 22,18" fill="none" stroke="#F0A500" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="2,6 18,6 18,22" fill="none" stroke="#F0A500" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
  <rect x="6" y="6" width="12" height="12" fill="#F0A500" opacity="0.1"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_resize():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="3" y="3" width="10" height="10" rx="1" fill="#F0A500" opacity="0.3"
        stroke="#F0A500" stroke-width="1.5"/>
  <rect x="11" y="11" width="10" height="10" rx="1" fill="#F0A500" opacity="0.6"
        stroke="#F0A500" stroke-width="1.5"/>
  <line x1="13" y1="3" x2="21" y2="3" stroke="#F0A500" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="21" y1="3" x2="21" y2="11" stroke="#F0A500" stroke-width="1.5" stroke-linecap="round"/>
  <line x1="13" y1="3" x2="21" y2="11" stroke="#F0A500" stroke-width="1.8" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_rotate():
    # Hinweis: identisch zu icon_rotate_right (gleiche Drehrichtung).
    # Als Alias definiert statt den SVG-Code zu duplizieren - falls icon_rotate()
    # eigentlich ein neutrales/richtungsloses Dreh-Icon zeigen soll, einfach
    # wieder einen eigenen SVG-String hier einsetzen.
    return icon_rotate_right()

@lru_cache(maxsize=None)
def icon_batch():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="7" y="7" width="13" height="13" rx="2" fill="#6B7280" opacity="0.15" stroke="#6B7280" stroke-width="1.6"/>
  <rect x="4" y="4" width="13" height="13" rx="2" fill="#fff" stroke="#6B7280" stroke-width="1.8"/>
  <polyline points="7,10 9.5,12.5 14,8" fill="none" stroke="#6B7280" stroke-width="1.8"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_move_folder():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M3 6 h6 l2 2 h10 v11 H3 Z" fill="#4A90D9" opacity="0.15" stroke="#4A90D9" stroke-width="1.5" stroke-linejoin="round"/>
  <line x1="9" y1="14" x2="16" y2="14" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
  <polyline points="13,11 16,14 13,17" fill="none" stroke="#4A90D9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_copy_folder():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M3 6 h6 l2 2 h10 v11 H3 Z" fill="#4A90D9" opacity="0.15" stroke="#4A90D9" stroke-width="1.5" stroke-linejoin="round"/>
  <line x1="13" y1="11" x2="13" y2="17" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
  <line x1="10" y1="14" x2="16" y2="14" stroke="#4A90D9" stroke-width="2" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_adjust():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <line x1="3" y1="7"  x2="21" y2="7"  stroke="#F0A500" stroke-width="2" stroke-linecap="round"/>
  <circle cx="9" cy="7" r="2.6" fill="#fff" stroke="#F0A500" stroke-width="2"/>
  <line x1="3" y1="13" x2="21" y2="13" stroke="#F0A500" stroke-width="2" stroke-linecap="round"/>
  <circle cx="15" cy="13" r="2.6" fill="#fff" stroke="#F0A500" stroke-width="2"/>
  <line x1="3" y1="19" x2="21" y2="19" stroke="#F0A500" stroke-width="2" stroke-linecap="round"/>
  <circle cx="7" cy="19" r="2.6" fill="#fff" stroke="#F0A500" stroke-width="2"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_rotate_left():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M3 12 a9 9 0 1 0 3-6.7" fill="none" stroke="#F0A500" stroke-width="2"
        stroke-linecap="round"/>
  <polyline points="3 3 3 9 9 9" fill="none" stroke="#F0A500" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_rotate_right():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <path d="M21 12 a9 9 0 1 1-3-6.7" fill="none" stroke="#F0A500" stroke-width="2"
        stroke-linecap="round"/>
  <polyline points="21 3 21 9 15 9" fill="none" stroke="#F0A500" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_flip_h():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <line x1="12" y1="2" x2="12" y2="22" stroke="#F0A500" stroke-width="1.5" stroke-dasharray="2 2"/>
  <polygon points="10,6 10,18 3,12" fill="#F0A500" opacity="0.7"/>
  <polygon points="14,6 14,18 21,12" fill="#F0A500" opacity="0.35"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_flip_v():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <line x1="2" y1="12" x2="22" y2="12" stroke="#F0A500" stroke-width="1.5" stroke-dasharray="2 2"/>
  <polygon points="6,10 18,10 12,3" fill="#F0A500" opacity="0.7"/>
  <polygon points="6,14 18,14 12,21" fill="#F0A500" opacity="0.35"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_zoom():
    # Hinweis: identisch zu icon_zoom_in (gleiches Lupe-mit-Plus-Symbol).
    # Als Alias definiert statt den SVG-Code zu duplizieren - falls icon_zoom()
    # eigentlich eine neutrale Lupe ohne Plus zeigen soll, einfach wieder
    # einen eigenen SVG-String hier einsetzen.
    return icon_zoom_in()

@lru_cache(maxsize=None)
def icon_undo():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <polyline points="9,7 4,12 9,17" fill="none" stroke="#6B7280" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M4 12 H14 a5 5 0 0 1 0 10 H11" fill="none" stroke="#6B7280" stroke-width="2.2"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_redo():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <polyline points="15,7 20,12 15,17" fill="none" stroke="#6B7280" stroke-width="2.2"
            stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M20 12 H10 a5 5 0 0 0 0 10 H13" fill="none" stroke="#6B7280" stroke-width="2.2"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_zoom_in():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="10" cy="10" r="7" fill="#8B5CF6" opacity="0.12" stroke="#8B5CF6" stroke-width="1.8"/>
  <line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="7" y1="10" x2="13" y2="10" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round"/>
  <line x1="10" y1="7"  x2="10" y2="13" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_zoom_out():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <circle cx="10" cy="10" r="7" fill="#8B5CF6" opacity="0.12" stroke="#8B5CF6" stroke-width="1.8"/>
  <line x1="15.5" y1="15.5" x2="21" y2="21" stroke="#8B5CF6" stroke-width="2.5" stroke-linecap="round"/>
  <line x1="7" y1="10" x2="13" y2="10" stroke="#8B5CF6" stroke-width="2" stroke-linecap="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_zoom_fit():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="3" y="3" width="18" height="18" rx="2" fill="#8B5CF6" opacity="0.1" stroke="#8B5CF6" stroke-width="1.5"/>
  <polyline points="8,5 5,5 5,8" fill="none" stroke="#8B5CF6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="16,5 19,5 19,8" fill="none" stroke="#8B5CF6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="8,19 5,19 5,16" fill="none" stroke="#8B5CF6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
  <polyline points="16,19 19,19 19,16" fill="none" stroke="#8B5CF6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_zoom_actual():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <rect x="4" y="4" width="16" height="16" rx="2" fill="none" stroke="#8B5CF6" stroke-width="1.8"/>
  <rect x="9" y="9" width="6" height="6" fill="#8B5CF6" opacity="0.7"/>
</svg>''')

@lru_cache(maxsize=None)
def icon_sort():
    return _icon_from_svg('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
  <line x1="3" y1="6"  x2="21" y2="6"  stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
  <line x1="3" y1="12" x2="15" y2="12" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
  <line x1="3" y1="18" x2="9"  y2="18" stroke="#6B7280" stroke-width="2" stroke-linecap="round"/>
  <polyline points="17,10 21,14 17,18" fill="none" stroke="#6B7280" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round"/>
</svg>''')
