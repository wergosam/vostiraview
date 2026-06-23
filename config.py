import os
import json
import logging

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "imageviewer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "last_directory": "",
    "slideshow_interval": 3000,
    "sort_criterion": "name",
    "sort_order": "asc",
    "watch_directory": True,
    "thumbnail_size": 200,
    "window_width": 1280,
    "window_height": 800,
    "trash_directory": "",      # leer = Standardpfad (siehe modules/trash.py)
    "trash_max_files": 100,     # 0 = unbegrenzt
    "overwrite_on_edit": False, # Bearbeitungen direkt im Original speichern
    "export_quality": 95,       # Qualität (1–100) für JPEG/WebP beim Speichern
    "recent_directories": [],   # zuletzt verwendete Bildordner (neueste zuerst)
    "language": "de"            # Oberflächensprache (de, en)
}


def load_config():
    """Lädt die gesamte Konfiguration als Dictionary.

    Fehlende Keys werden automatisch mit den Default-Werten ergänzt,
    damit ältere config.json-Dateien nach Updates nicht zu KeyErrors führen.
    """
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                config.update(loaded)
            else:
                logger.warning("config.json hat kein gültiges Format, verwende Defaults.")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Konfiguration konnte nicht geladen werden (%s), verwende Defaults.", e)

    return config


def save_config(config):
    """Speichert die Konfiguration atomar (schreibt erst in eine temporäre
    Datei und ersetzt damit anschließend die eigentliche config.json).
    So bleibt die Datei auch bei einem Absturz während des Schreibens intakt.
    """
    os.makedirs(CONFIG_DIR, exist_ok=True)
    tmp_file = CONFIG_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        os.replace(tmp_file, CONFIG_FILE)
    except IOError as e:
        logger.error("Fehler beim Speichern der Konfiguration in %s: %s", CONFIG_FILE, e)
        if os.path.exists(tmp_file):
            try:
                os.remove(tmp_file)
            except OSError:
                pass


def update_config(**kwargs):
    """Lädt die Konfiguration, aktualisiert beliebig viele Keys auf einmal
    und speichert sie wieder. Vermeidet mehrfaches Laden/Speichern bei
    mehreren Änderungen gleichzeitig.

    Beispiel: update_config(last_directory="/pfad", thumbnail_size=250)
    """
    config = load_config()
    config.update(kwargs)
    save_config(config)
    return config


# ===== Kompatibilitätsfunktionen für alte Aufrufe =====
# (falls image_loader.select_initial_directory noch den alten Stil erwartet)

def get_last_directory():
    """Gibt das zuletzt verwendete Verzeichnis zurück."""
    return load_config().get("last_directory", "")


def set_last_directory(directory):
    """Setzt das zuletzt verwendete Verzeichnis."""
    update_config(last_directory=directory)


# ===== Zuletzt verwendete Verzeichnisse =====

def get_recent_directories():
    """Liste der zuletzt verwendeten Bildordner (neueste zuerst)."""
    recents = load_config().get("recent_directories", [])
    return recents if isinstance(recents, list) else []


def add_recent_directory(directory, max_entries=10):
    """Fügt ein Verzeichnis vorne in die Verlaufsliste ein (ohne Duplikate)."""
    if not directory:
        return
    config = load_config()
    recents = config.get("recent_directories", [])
    if not isinstance(recents, list):
        recents = []
    recents = [d for d in recents if d != directory]
    recents.insert(0, directory)
    config["recent_directories"] = recents[:max_entries]
    save_config(config)


def clear_recent_directories():
    """Leert die Liste der zuletzt verwendeten Verzeichnisse."""
    update_config(recent_directories=[])


# Alte Funktionsnamen (für Rückwärtskompatibilität)
def save_config_legacy(directory, config_file=None):
    set_last_directory(directory)


def load_config_legacy(config_file=None):
    return get_last_directory()
