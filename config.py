import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "imageviewer")
os.makedirs(CONFIG_DIR, exist_ok=True)
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
    """Lädt die gesamte Konfiguration als Dictionary."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Speichert die Konfiguration."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except IOError:
        print(f"Fehler beim Speichern der Konfiguration in {CONFIG_FILE}")

# ===== Kompatibilitätsfunktionen für alte Aufrufe =====
# (falls image_loader.select_initial_directory noch den alten Stil erwartet)

def get_last_directory():
    """Gibt das zuletzt verwendete Verzeichnis zurück."""
    return load_config().get("last_directory", "")

def set_last_directory(directory):
    """Setzt das zuletzt verwendete Verzeichnis."""
    config = load_config()
    config["last_directory"] = directory
    save_config(config)

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
    config = load_config()
    config["recent_directories"] = []
    save_config(config)

# Alte Funktionsnamen (für Rückwärtskompatibilität)
def save_config_legacy(directory, config_file=None):
    set_last_directory(directory)

def load_config_legacy(config_file=None):
    return get_last_directory()