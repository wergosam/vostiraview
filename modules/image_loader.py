import os
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QTimer

from config import get_last_directory, set_last_directory, add_recent_directory
from i18n import tr


class ImageLoader:
    """Lädt und verwaltet Bilder, Navigation und Verzeichnis."""

    def __init__(self, parent):
        self.parent = parent
        self.image_directory = ""
        self.image_paths = []
        self.current_index = -1
        self._original_pixmap = None
        self._pixmap = None

    def select_initial_directory(self):
        """Wählt das zuletzt verwendete Verzeichnis aus der Config."""
        saved_dir = get_last_directory()
        if saved_dir and os.path.exists(saved_dir):
            self.change_directory(saved_dir)
        else:
            # Fallback: ~/Bilder oder ~/Pictures
            home = os.path.expanduser("~")
            pics = os.path.join(home, "Bilder")
            if os.path.exists(pics):
                self.change_directory(pics)
            else:
                # alternativ: ~/Pictures
                pics2 = os.path.join(home, "Pictures")
                if os.path.exists(pics2):
                    self.change_directory(pics2)
                else:
                    self.change_directory(home)

    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

    def change_directory(self, directory):
        """Wechselt das Bildverzeichnis und lädt die Bildliste."""
        if not directory or not os.path.isdir(directory):
            return
        self.image_directory = directory
        set_last_directory(directory)   # in Config speichern
        add_recent_directory(directory)  # in Verlaufsliste aufnehmen
        self.update_directory(directory)
        # Verzeichnis-Watcher (falls vorhanden) auf den neuen Ordner umstellen
        watcher = getattr(self.parent, 'directory_watcher', None)
        if watcher is not None:
            watcher.set_directory(directory)

    def _scan_directory(self, directory):
        """Scannt ein Verzeichnis nach unterstützten Bildern und gibt eine
        sortierte Liste vollständiger Pfade zurück."""
        paths = []
        if os.path.exists(directory):
            for f in os.listdir(directory):
                ext = os.path.splitext(f)[1].lower()
                if ext in self.SUPPORTED_FORMATS:
                    paths.append(os.path.join(directory, f))
        self._sort_paths(paths)
        return paths

    def _sort_paths(self, paths):
        """Sortiert eine Pfadliste gemäß der aktuellen Sortiereinstellung."""
        criterion = getattr(self.parent, 'current_sort_criterion', 'name')
        order = getattr(self.parent, 'current_sort_order', 'asc')
        reverse = (order == 'desc')
        try:
            if criterion == 'date':
                paths.sort(key=lambda x: os.path.getmtime(x), reverse=reverse)
            elif criterion == 'size':
                paths.sort(key=lambda x: os.path.getsize(x), reverse=reverse)
            else:
                paths.sort(key=lambda x: os.path.basename(x).lower(), reverse=reverse)
        except OSError:
            # Falls eine Datei während des Sortierens verschwindet, fällt
            # die Sortierung auf den robusten Namensschlüssel zurück.
            paths.sort(key=lambda x: os.path.basename(x).lower())

    def update_directory(self, directory):
        """Aktualisiert die Bildliste aus dem Verzeichnis (ohne Config zu speichern)."""
        self.image_directory = directory
        self.image_paths = self._scan_directory(directory)
        # Index zurücksetzen
        self.current_index = -1
        if self.image_paths:
            self.current_index = 0
            self.load_image(self.image_paths[0])
        else:
            self.parent.clear_image_display()
            self.parent.statusBar.showMessage(tr("Keine Bilder in diesem Ordner"), 3000)

    def refresh_directory_preserving_state(self):
        """Re-Scan des aktuellen Verzeichnisses unter Beibehaltung des
        gerade angezeigten Bildes (für den DirectoryWatcher).

        Gibt ein Tupel (hinzugefügt, entfernt) zurück. (0, 0) bedeutet,
        dass sich an den Bildern nichts Relevantes geändert hat.
        """
        directory = self.image_directory
        if not directory or not os.path.isdir(directory):
            return (0, 0)

        # Aktuell angezeigtes Bild merken
        current_path = None
        if 0 <= self.current_index < len(self.image_paths):
            current_path = self.image_paths[self.current_index]

        old_set = set(self.image_paths)
        new_paths = self._scan_directory(directory)
        new_set = set(new_paths)
        if new_set == old_set:
            return (0, 0)   # keine bildrelevante Änderung -> kein Refresh

        added = len(new_set - old_set)
        removed = len(old_set - new_set)
        self.image_paths = new_paths

        if current_path and current_path in new_set:
            # Bild existiert weiterhin -> nur neuen Index übernehmen
            self.current_index = self.image_paths.index(current_path)
        elif current_path:
            # Angezeigtes Bild wurde gelöscht -> Nachbarbild anzeigen
            if self.image_paths:
                self.current_index = min(self.current_index, len(self.image_paths) - 1)
                self.load_image(self.image_paths[self.current_index])
            else:
                self.current_index = -1
                self.parent.clear_image_display()
        else:
            # Vorher war kein Bild angezeigt
            self.current_index = 0 if self.image_paths else -1

        return (added, removed)

    def load_image(self, image_path):
        """Lädt ein Bild und zeigt es im Viewer an."""
        if not image_path or not os.path.exists(image_path):
            return
        # Pixmap laden
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.warning(self.parent, tr("Fehler"), tr("Konnte Bild nicht laden:") + f" {os.path.basename(image_path)}")
            return
        self._original_pixmap = pixmap
        self._pixmap = pixmap
        # Index aktualisieren
        if image_path in self.image_paths:
            self.current_index = self.image_paths.index(image_path)
        else:
            self.image_paths.append(image_path)
            self.current_index = len(self.image_paths) - 1
        # Anzeigen
        self.parent._display_pixmap()
        self.parent.update_image_info(image_path)
        self.parent.statusBar.showMessage(tr("Bild geladen:") + f" {os.path.basename(image_path)}", 3000)
        # Falls in Galerie oder Liste, aktualisieren wir die Auswahl (optional)
        if hasattr(self.parent, 'gallery_widget'):
            self.parent.gallery_widget.clear_selection()
            self.parent.gallery_widget.toggle_selection(image_path)
        if hasattr(self.parent, 'list_view_widget'):
            # Auswahl in Listenansicht setzen (nur wenn sichtbar)
            pass

    def navigate_image(self, step):
        """Navigiert step Bilder vor oder zurück."""
        if not self.image_paths:
            return
        new_index = self.current_index + step
        if new_index < 0:
            new_index = len(self.image_paths) - 1
        elif new_index >= len(self.image_paths):
            new_index = 0
        self.current_index = new_index
        self.load_image(self.image_paths[self.current_index])

    def open_file(self):
        """Öffnet einen Datei-Dialog zum Laden eines einzelnen Bildes."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.parent,
            "Bild öffnen",
            self.image_directory or "",
            "Bilddateien (*.png *.jpg *.jpeg *.gif *.bmp *.webp)"
        )
        if file_path:
            # Bild anzeigen, ohne das aktuelle Bildverzeichnis zu wechseln.
            # load_image() setzt den Index bzw. hängt das Bild an, falls es
            # (noch) nicht in der aktuellen Liste enthalten ist.
            self.load_image(file_path)

    def sort_images(self, criterion, order):
        """Sortiert die Bildliste und aktualisiert die Ansichten."""
        reverse = (order == 'desc')
        if criterion == 'name':
            self.image_paths.sort(key=lambda x: os.path.basename(x).lower(), reverse=reverse)
        elif criterion == 'date':
            self.image_paths.sort(key=lambda x: os.path.getmtime(x), reverse=reverse)
        elif criterion == 'size':
            self.image_paths.sort(key=lambda x: os.path.getsize(x), reverse=reverse)
        # Aktuellen Index beibehalten
        if self.current_index >= 0 and self.current_index < len(self.image_paths):
            current_image = self.image_paths[self.current_index]
            if current_image in self.image_paths:
                self.current_index = self.image_paths.index(current_image)
            else:
                self.current_index = 0
        # Ansichten aktualisieren (wird von file_operations.sort_images aufgerufen)
        # Hier nur die interne Liste sortiert, die Galerie/Liste werden extern aktualisiert