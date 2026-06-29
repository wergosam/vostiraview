import os
from PyQt6.QtCore import QObject, QTimer, QFileSystemWatcher

from config import load_config


class DirectoryWatcher(QObject):
    """Beobachtet das aktuelle Bildverzeichnis mit QFileSystemWatcher.

    Änderungen (neue/gelöschte/umbenannte Dateien) lösen ein
    `directoryChanged`-Signal aus. Diese Events werden über einen
    Single-Shot-Timer entprellt (Debounce), damit ein Event-Sturm
    beim Kopieren mehrerer/großer Dateien nur einen einzigen Refresh
    auslöst – und nicht auf halb geschriebene Dateien reagiert wird.
    """

    DEBOUNCE_MS = 400

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._watched_dir = ""

        self.watcher = QFileSystemWatcher(self)
        self.watcher.directoryChanged.connect(self._on_directory_changed)

        # Debounce-Timer: bündelt Event-Stürme
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(self.DEBOUNCE_MS)
        self._debounce.timeout.connect(self._refresh)

        # Einstellung aus Config (Standard: aktiv)
        self.enabled = bool(load_config().get("watch_directory", True))

    # ---------------------------------------------------------------
    def set_directory(self, directory):
        """Beim Verzeichniswechsel aufrufen – beobachtet den neuen Ordner."""
        self._rearm(directory)

    def set_enabled(self, enabled):
        """Aktiviert/deaktiviert die Überwachung zur Laufzeit."""
        self.enabled = bool(enabled)
        if self.enabled:
            self._rearm(self.app.image_loader.image_directory)
        else:
            self._debounce.stop()
            self._unwatch()

    # ---------------------------------------------------------------
    def _unwatch(self):
        if self._watched_dir:
            self.watcher.removePath(self._watched_dir)
            self._watched_dir = ""

    def _rearm(self, directory):
        """Entfernt den alten Pfad und beobachtet (falls aktiv) den neuen."""
        self._unwatch()
        if self.enabled and directory and os.path.isdir(directory):
            self.watcher.addPath(directory)
            self._watched_dir = directory

    def _on_directory_changed(self, _path):
        if not self.enabled:
            return
        # Debounce: Timer neu starten, bis die Änderungen zur Ruhe kommen
        self._debounce.start()

    def _refresh(self):
        # QFileSystemWatcher verliert den Pfad gelegentlich (z. B. wenn der
        # Ordner kurzzeitig ersetzt wird) – sicherheitshalber neu beobachten.
        if self._watched_dir and self._watched_dir not in self.watcher.directories():
            if os.path.isdir(self._watched_dir):
                self.watcher.addPath(self._watched_dir)
        self.app.refresh_current_directory_from_watcher()
