"""Einfacher Papierkorb für gelöschte Bilder.

Statt Dateien endgültig mit os.remove() zu entfernen, werden sie in ein
verstecktes Papierkorb-Verzeichnis verschoben. Dadurch lässt sich das
Löschen rückgängig machen (siehe UndoManager). Jede Datei erhält dort einen
eindeutigen Präfix, damit gleichnamige Dateien nicht kollidieren.
"""

import os
import shutil
import uuid
import json
import datetime

from config import load_config

# Name der Index-Datei (merkt sich Originalpfad + Löschzeitpunkt je Datei)
_INDEX_NAME = ".trash_index.json"


def default_trash_dir():
    """Der Standard-Papierkorbpfad, wenn in den Einstellungen keiner gesetzt ist."""
    return os.path.join(
        os.path.expanduser("~"), ".local", "share", "vostiraview", "trash")


def get_trash_dir():
    """Liefert das konfigurierte Papierkorb-Verzeichnis und legt es bei Bedarf an."""
    configured = load_config().get("trash_directory", "")
    d = configured if configured else default_trash_dir()
    os.makedirs(d, exist_ok=True)
    return d


def get_max_files():
    """Maximale Anzahl Dateien im Papierkorb (0 = unbegrenzt)."""
    try:
        return int(load_config().get("trash_max_files", 100))
    except (TypeError, ValueError):
        return 100


# ----------------------------------------------------------------------------
# Index: merkt sich zu jeder Papierkorb-Datei den Originalpfad + Löschdatum
# ----------------------------------------------------------------------------
def _index_path():
    return os.path.join(get_trash_dir(), _INDEX_NAME)


def _load_index():
    p = _index_path()
    if os.path.exists(p):
        try:
            with open(p, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_index(idx):
    try:
        with open(_index_path(), "w") as f:
            json.dump(idx, f, indent=2)
    except Exception as e:
        print(f"Fehler beim Speichern des Papierkorb-Index: {e}")


def _record(trash_path, original_path):
    """Hinterlegt Originalpfad + Zeitstempel für eine Papierkorb-Datei."""
    idx = _load_index()
    idx[os.path.basename(trash_path)] = {
        "original": os.path.abspath(original_path),
        "deleted": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _save_index(idx)


def _drop_from_index(trash_path):
    idx = _load_index()
    if idx.pop(os.path.basename(trash_path), None) is not None:
        _save_index(idx)


def _prune_index():
    """Entfernt Index-Einträge, deren Datei nicht mehr existiert."""
    trash_dir = get_trash_dir()
    idx = _load_index()
    changed = False
    for name in list(idx.keys()):
        if not os.path.exists(os.path.join(trash_dir, name)):
            idx.pop(name, None)
            changed = True
    if changed:
        _save_index(idx)


def display_name(trash_path):
    """Ursprünglicher Dateiname ohne den eindeutigen Präfix."""
    name = os.path.basename(trash_path)
    return name.split("__", 1)[1] if "__" in name else name


def original_path_for(trash_path):
    """Gemerkter Originalpfad einer Papierkorb-Datei (oder None)."""
    return _load_index().get(os.path.basename(trash_path), {}).get("original")


def _enforce_limit():
    """Hält die Dateianzahl im Papierkorb unter dem konfigurierten Limit,
    indem die ältesten Dateien endgültig entfernt werden."""
    max_files = get_max_files()
    if max_files <= 0:
        return  # unbegrenzt
    files = list_trash()
    if len(files) <= max_files:
        return
    files.sort(key=lambda p: os.path.getmtime(p))  # älteste zuerst
    for p in files[:len(files) - max_files]:
        try:
            os.remove(p)
        except Exception as e:
            print(f"Fehler beim Begrenzen des Papierkorbs ({p}): {e}")
    _prune_index()


def move_to_trash(path):
    """Verschiebt eine Datei in den Papierkorb.

    Gibt den Pfad im Papierkorb zurück oder None, wenn die Datei nicht
    existiert. Überschreitet der Papierkorb danach das konfigurierte Limit,
    werden die ältesten Dateien entfernt.
    """
    if not path or not os.path.exists(path):
        return None
    trash_dir = get_trash_dir()
    token = uuid.uuid4().hex[:8]
    trash_path = os.path.join(trash_dir, f"{token}__{os.path.basename(path)}")
    shutil.move(path, trash_path)
    _record(trash_path, path)
    _enforce_limit()
    return trash_path


def copy_to_trash(path):
    """Legt eine Kopie der Datei im Papierkorb ab (Original bleibt erhalten).

    Wird für den Überschreiben-Modus genutzt, um vor dem Überschreiben eine
    Sicherung anzulegen. Gibt den Pfad der Kopie zurück oder None.
    """
    if not path or not os.path.exists(path):
        return None
    trash_dir = get_trash_dir()
    token = uuid.uuid4().hex[:8]
    trash_path = os.path.join(trash_dir, f"{token}__{os.path.basename(path)}")
    shutil.copy2(path, trash_path)
    _record(trash_path, path)
    _enforce_limit()
    return trash_path


def copy_from_trash(trash_path, target_path):
    """Kopiert eine Datei aus dem Papierkorb zurück an den Zielort (überschreibt).

    Die Papierkorb-Datei bleibt erhalten (im Gegensatz zu restore_from_trash),
    damit Rückgängig/Wiederholen mehrfach zwischen zwei Versionen wechseln kann.
    """
    if not trash_path or not os.path.exists(trash_path):
        return False
    target_dir = os.path.dirname(target_path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
    shutil.copy2(trash_path, target_path)
    return True


def move_trash_contents(old_dir, new_dir):
    """Verschiebt alle Dateien aus dem alten in den neuen Papierkorb-Ordner.

    Gibt die Anzahl verschobener Dateien zurück. Bei Namenskollisionen wird
    ein eindeutiges Suffix angehängt.
    """
    if not old_dir or not new_dir:
        return 0
    if os.path.abspath(old_dir) == os.path.abspath(new_dir) or not os.path.isdir(old_dir):
        return 0
    os.makedirs(new_dir, exist_ok=True)

    # Index des alten Ordners laden (für die Originalpfade)
    old_index_path = os.path.join(old_dir, _INDEX_NAME)
    old_idx = {}
    if os.path.exists(old_index_path):
        try:
            with open(old_index_path, "r") as f:
                old_idx = json.load(f)
        except Exception:
            old_idx = {}
    new_idx = _load_index()  # get_trash_dir() == new_dir (Config bereits aktualisiert)

    count = 0
    for name in os.listdir(old_dir):
        if name == _INDEX_NAME or name.startswith("."):
            continue
        src = os.path.join(old_dir, name)
        if not os.path.isfile(src):
            continue
        dst_name = name
        dst = os.path.join(new_dir, dst_name)
        if os.path.exists(dst):
            base, ext = os.path.splitext(name)
            dst_name = f"{base}_{uuid.uuid4().hex[:4]}{ext}"
            dst = os.path.join(new_dir, dst_name)
        try:
            shutil.move(src, dst)
            count += 1
            if name in old_idx:
                new_idx[dst_name] = old_idx[name]
        except Exception as e:
            print(f"Fehler beim Verschieben von {src} nach {new_dir}: {e}")

    _save_index(new_idx)
    try:
        if os.path.exists(old_index_path):
            os.remove(old_index_path)
    except Exception:
        pass
    return count


def list_trash():
    """Liefert die Pfade aller Dateien im Papierkorb (ohne Index-Datei)."""
    trash_dir = get_trash_dir()
    return [os.path.join(trash_dir, name) for name in os.listdir(trash_dir)
            if name != _INDEX_NAME and not name.startswith(".")
            and os.path.isfile(os.path.join(trash_dir, name))]


def list_trash_entries():
    """Liefert Detailinfos zu allen Papierkorb-Dateien (neueste zuerst).

    Jeder Eintrag: trash_path, name (Originalname), original (Originalpfad oder
    None), deleted (Zeitstempel oder None), size, mtime.
    """
    idx = _load_index()
    entries = []
    for p in list_trash():
        meta = idx.get(os.path.basename(p), {})
        try:
            st = os.stat(p)
        except OSError:
            continue
        entries.append({
            "trash_path": p,
            "name": display_name(p),
            "original": meta.get("original"),
            "deleted": meta.get("deleted"),
            "size": st.st_size,
            "mtime": st.st_mtime,
        })
    entries.sort(key=lambda e: e["mtime"], reverse=True)
    return entries


def restore_entry(trash_path, fallback_dir=None):
    """Stellt eine Papierkorb-Datei wieder her.

    Zielort ist der gemerkte Originalpfad; ist er unbekannt, wird `fallback_dir`
    genutzt. Existiert das Ziel bereits, wird ein Suffix angehängt (kein
    Überschreiben). Gibt den Zielpfad zurück oder None.
    """
    original = original_path_for(trash_path)
    if not original:
        if not fallback_dir:
            return None
        original = os.path.join(fallback_dir, display_name(trash_path))

    target = original
    if os.path.exists(target):
        base, ext = os.path.splitext(original)
        target = f"{base}_wiederhergestellt{ext}"
        i = 1
        while os.path.exists(target):
            target = f"{base}_wiederhergestellt_{i}{ext}"
            i += 1

    if restore_from_trash(trash_path, target):
        _drop_from_index(trash_path)
        return target
    return None


def delete_entry(trash_path):
    """Entfernt eine einzelne Datei endgültig aus dem Papierkorb."""
    try:
        os.remove(trash_path)
    except Exception as e:
        print(f"Fehler beim endgültigen Löschen ({trash_path}): {e}")
        return False
    _drop_from_index(trash_path)
    return True


def empty_trash():
    """Löscht alle Dateien im Papierkorb endgültig.

    Gibt die Anzahl der entfernten Dateien zurück.
    """
    count = 0
    for path in list_trash():
        try:
            os.remove(path)
            count += 1
        except Exception as e:
            print(f"Fehler beim Leeren des Papierkorbs ({path}): {e}")
    _save_index({})
    return count


def restore_from_trash(trash_path, original_path):
    """Stellt eine Datei aus dem Papierkorb am Originalort wieder her.

    Gibt True bei Erfolg zurück.
    """
    if not trash_path or not os.path.exists(trash_path):
        return False
    target_dir = os.path.dirname(original_path)
    if target_dir:
        os.makedirs(target_dir, exist_ok=True)
    shutil.move(trash_path, original_path)
    return True
