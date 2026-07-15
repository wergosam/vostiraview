import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QSpinBox,
                             QDialogButtonBox, QGroupBox, QFileDialog,
                             QLineEdit, QPushButton, QHBoxLayout, QCheckBox,
                             QTabWidget, QWidget, QComboBox, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from config import load_config, save_config
from modules.trash import default_trash_dir, move_trash_contents, _enforce_limit
from i18n import tr, available_languages


class SettingsDialog(QDialog):
    """Einstellungsdialog für VostiraView (mit Tabs)."""

    # Auswahl-Reihenfolge der Sortier-Dropdowns -> Config-Werte
    SORT_CRITERIA = [("Name", "name"), ("Datum", "date"), ("Größe", "size")]
    SORT_ORDERS = [("Aufsteigend", "asc"), ("Absteigend", "desc")]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Einstellungen"))
        self.setMinimumSize(520, 440)

        # Config laden
        self.config = load_config()

        layout = QVBoxLayout(self)

        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), tr("Allgemein"))
        tabs.addTab(self._build_view_tab(), tr("Ansicht"))
        tabs.addTab(self._build_slideshow_tab(), tr("Slideshow"))
        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ================= Tabs =================
    def _build_general_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        # Sprache
        self.lang_combo = QComboBox()
        for code, name in available_languages():
            self.lang_combo.addItem(name, code)
        self._select_combo(self.lang_combo, self.config.get("language", "de"))
        form.addRow(tr("Sprache:"), self.lang_combo)

        # Bildverzeichnis
        self.dir_edit = QLineEdit()
        self.dir_edit.setText(self.config.get("last_directory", ""))
        self.dir_edit.setReadOnly(True)
        browse_btn = QPushButton(tr("Durchsuchen..."))
        browse_btn.clicked.connect(self.browse_directory)
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow(tr("Bildverzeichnis:"), dir_layout)

        # Automatische Verzeichnis-Überwachung
        self.watch_check = QCheckBox(tr("Ordner automatisch auf neue/gelöschte Bilder überwachen"))
        self.watch_check.setChecked(self.config.get("watch_directory", True))
        form.addRow(tr("Auto-Aktualisierung:"), self.watch_check)

        # Papierkorb-Ordner (leer in der Config => Standardpfad anzeigen)
        self.trash_dir_edit = QLineEdit()
        self.trash_dir_edit.setText(self.config.get("trash_directory", "") or default_trash_dir())
        self.trash_dir_edit.setReadOnly(True)
        trash_browse_btn = QPushButton(tr("Durchsuchen..."))
        trash_browse_btn.clicked.connect(self.browse_trash_directory)
        trash_dir_layout = QHBoxLayout()
        trash_dir_layout.addWidget(self.trash_dir_edit)
        trash_dir_layout.addWidget(trash_browse_btn)
        form.addRow(tr("Papierkorb-Ordner:"), trash_dir_layout)

        # Maximale Anzahl Dateien im Papierkorb (0 = unbegrenzt)
        self.trash_max_spin = QSpinBox()
        self.trash_max_spin.setRange(0, 100000)
        self.trash_max_spin.setSuffix(" " + tr("Dateien"))
        self.trash_max_spin.setSpecialValueText(tr("Unbegrenzt"))
        self.trash_max_spin.setValue(int(self.config.get("trash_max_files", 100)))
        form.addRow(tr("Papierkorb-Limit:"), self.trash_max_spin)

        # Bearbeitungen direkt im Original speichern (mit Sicherheitsabfrage)
        self.overwrite_check = QCheckBox(
            tr("Bearbeitungen (Drehen/Zuschneiden/Größe) direkt im Original speichern"))
        self.overwrite_check.setChecked(self.config.get("overwrite_on_edit", False))
        self.overwrite_check.setToolTip(tr(
            "Ohne Speichern-Dialog. Vor jedem Überschreiben erfolgt eine "
            "Sicherheitsabfrage; das Original wird im Papierkorb gesichert."))
        form.addRow(tr("Schnellbearbeitung:"), self.overwrite_check)

        return tab

    def _build_view_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        # Thumbnail-Größe
        self.thumb_spin = QSpinBox()
        self.thumb_spin.setRange(80, 400)
        self.thumb_spin.setSingleStep(10)
        self.thumb_spin.setSuffix(" px")
        self.thumb_spin.setValue(int(self.config.get("thumbnail_size", 200)))
        form.addRow(tr("Thumbnail-Größe:"), self.thumb_spin)

        # Standard-Sortierung
        self.sort_criterion_combo = QComboBox()
        for label, value in self.SORT_CRITERIA:
            self.sort_criterion_combo.addItem(tr(label), value)
        self._select_combo(self.sort_criterion_combo, self.config.get("sort_criterion", "name"))

        self.sort_order_combo = QComboBox()
        for label, value in self.SORT_ORDERS:
            self.sort_order_combo.addItem(tr(label), value)
        self._select_combo(self.sort_order_combo, self.config.get("sort_order", "asc"))

        sort_layout = QHBoxLayout()
        sort_layout.addWidget(self.sort_criterion_combo)
        sort_layout.addWidget(self.sort_order_combo)
        form.addRow(tr("Standard-Sortierung:"), sort_layout)

        # Start-Fenstergröße
        self.win_width_spin = QSpinBox()
        self.win_width_spin.setRange(400, 10000)
        self.win_width_spin.setSuffix(" px")
        self.win_width_spin.setValue(int(self.config.get("window_width", 1280)))

        self.win_height_spin = QSpinBox()
        self.win_height_spin.setRange(300, 10000)
        self.win_height_spin.setSuffix(" px")
        self.win_height_spin.setValue(int(self.config.get("window_height", 800)))

        win_layout = QHBoxLayout()
        win_layout.addWidget(self.win_width_spin)
        win_layout.addWidget(QLabel("×"))
        win_layout.addWidget(self.win_height_spin)
        form.addRow(tr("Start-Fenstergröße:"), win_layout)

        # Export-Qualität für verlustbehaftete Formate (JPEG/WebP)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setValue(int(self.config.get("export_quality", 95)))
        self.quality_spin.setToolTip(tr("Wirkt beim Speichern als JPEG oder WebP."))
        form.addRow(tr("Speicherqualität (JPEG/WebP):"), self.quality_spin)

        return tab

    def _build_slideshow_tab(self):
        tab = QWidget()
        form = QFormLayout(tab)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 60)
        self.interval_spin.setSuffix(" " + tr("Sekunden"))
        self.interval_spin.setValue(self.config.get("slideshow_interval", 3000) // 1000)
        form.addRow(tr("Intervall:"), self.interval_spin)

        return tab

    # ================= Helfer =================
    @staticmethod
    def _select_combo(combo, value):
        index = combo.findData(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _browse_directory(self, title, line_edit):
        """Öffnet einen Verzeichnis-Dialog und setzt den gewählten Pfad ins line_edit."""
        start_dir = line_edit.text() or os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, title, start_dir, QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            line_edit.setText(directory)

    def browse_directory(self):
        self._browse_directory(tr("Bildverzeichnis auswählen"), self.dir_edit)

    def browse_trash_directory(self):
        self._browse_directory(tr("Papierkorb-Ordner auswählen"), self.trash_dir_edit)

    def _resolved_trash_dir(self):
        """Gibt den effektiven Papierkorb-Pfad zurück (Config oder Standardpfad)."""
        return self.config.get("trash_directory", "") or default_trash_dir()
    def save_and_accept(self):
        """Speichert die Einstellungen und wendet sie (wo möglich) sofort an."""
        criterion = self.sort_criterion_combo.currentData()
        order = self.sort_order_combo.currentData()
        interval_ms = self.interval_spin.value() * 1000
        thumb_size = self.thumb_spin.value()

        self.config["last_directory"] = self.dir_edit.text()
        self.config["watch_directory"] = self.watch_check.isChecked()
        self.config["slideshow_interval"] = interval_ms
        self.config["thumbnail_size"] = thumb_size
        self.config["sort_criterion"] = criterion
        self.config["sort_order"] = order
        self.config["window_width"] = self.win_width_spin.value()
        self.config["window_height"] = self.win_height_spin.value()

        # Papierkorb: Standardpfad als leeren Wert speichern
        old_trash_dir = self._resolved_trash_dir()
        new_trash_dir = self.trash_dir_edit.text()
        dir_changed = os.path.abspath(old_trash_dir) != os.path.abspath(new_trash_dir)
        self.config["trash_directory"] = "" if new_trash_dir == default_trash_dir() else new_trash_dir
        self.config["trash_max_files"] = self.trash_max_spin.value()
        self.config["overwrite_on_edit"] = self.overwrite_check.isChecked()
        self.config["export_quality"] = self.quality_spin.value()

        # Sprache
        old_lang = self.config.get("language", "de")
        new_lang = self.lang_combo.currentData()
        lang_changed = new_lang != old_lang
        self.config["language"] = new_lang

        save_config(self.config)

        if lang_changed:
            QMessageBox.information(
                self, tr("Sprache geändert"),
                tr("Bitte starten Sie das Programm neu, damit die neue Sprache wirksam wird."))

        # Bei Ordnerwechsel: vorhandene Dateien mitverschieben und den
        # Rückgängig-/Wiederholen-Stapel leeren (er verweist auf die alten Pfade)
        parent = self.parent()
        if dir_changed:
            try:
                moved = move_trash_contents(old_trash_dir, new_trash_dir)
            except OSError as e:
                QMessageBox.warning(
                    self, tr("Papierkorb-Ordner geändert"),
                    tr("Der Ordner wurde gewechselt, aber vorhandene Dateien konnten nicht "
                       "automatisch verschoben werden:") + f"\n{e}")
                moved = 0

            had_history = False
            if parent and hasattr(parent, "undo_manager"):
                had_history = parent.undo_manager.can_undo() or parent.undo_manager.can_redo()
                parent.undo_manager.clear()

            lines = [tr("Der Papierkorb-Ordner wurde geändert.")]
            if moved:
                lines.append(f"{moved} " + tr("Datei(en) wurden in den neuen Ordner verschoben."))
            if had_history:
                lines.append(tr("Der Rückgängig-/Wiederholen-Verlauf wurde geleert, "
                                "da er auf den alten Ordner verwies."))
            QMessageBox.information(self, tr("Papierkorb-Ordner geändert"), "\n".join(lines))

        # Neues Limit sofort anwenden (z. B. wenn es verkleinert wurde)
        _enforce_limit()

        self._apply_to_parent(criterion, order, interval_ms, thumb_size)
        self.accept()

    def _apply_to_parent(self, criterion, order, interval_ms, thumb_size):
        """Wendet die Einstellungen auf die laufende Anwendung an."""
        parent = self.parent()
        if not parent:
            return

        # Slideshow-Intervall
        if hasattr(parent, 'slideshow_handler'):
            parent.slideshow_handler.set_interval(interval_ms)

        # Verzeichnis-Watcher
        if getattr(parent, 'directory_watcher', None) is not None:
            parent.directory_watcher.set_enabled(self.watch_check.isChecked())

        # Verzeichniswechsel (falls geändert)
        if hasattr(parent, 'image_loader'):
            new_dir = self.dir_edit.text()
            if new_dir and os.path.exists(new_dir) and new_dir != parent.image_loader.image_directory:
                parent.image_loader.change_directory(new_dir)

        # Thumbnail-Größe live übernehmen (alten Cache verwerfen)
        if hasattr(parent, 'gallery_widget') and parent.gallery_widget.THUMBNAIL_SIZE != thumb_size:
            parent.gallery_widget.THUMBNAIL_SIZE = thumb_size
            parent.gallery_widget.thumbnail_cache.clear()

        # Sortierung live anwenden (baut Galerie + Liste neu auf – auch für
        # eine geänderte Thumbnail-Größe). Fällt zurück auf reines Setzen der
        # Attribute, falls (noch) keine Bilder geladen sind.
        if hasattr(parent, 'file_ops') and getattr(parent, 'image_loader', None) \
                and parent.image_loader.image_paths:
            parent.file_ops.sort_images(criterion, order)
        else:
            parent.current_sort_criterion = criterion
            parent.current_sort_order = order
