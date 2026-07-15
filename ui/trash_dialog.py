"""Papierkorb-Verwaltung: gelöschte Bilder ansehen, wiederherstellen oder
endgültig entfernen.
"""
import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget,
                             QTreeWidgetItem, QPushButton, QLabel, QMessageBox,
                             QAbstractItemView)
from PyQt6.QtCore import Qt

from modules import trash
from i18n import tr


def _fmt_size(b):
    if b < 1024:
        return f"{int(b)} B"
    size = float(b)
    for unit in ("KB", "MB", "GB"):
        size /= 1024
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}"
    return f"{size:.1f} GB"  # nicht erreichbar, sichert Rückgabetyp


class TrashDialog(QDialog):
    """Dialog zum Verwalten des Papierkorbs."""

    def __init__(self, app):
        super().__init__(app)
        self._app = app
        self.setWindowTitle(tr("Papierkorb verwalten"))
        self.setMinimumSize(640, 420)

        layout = QVBoxLayout(self)

        self.info = QLabel("")
        layout.addWidget(self.info)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(4)
        self.tree.setHeaderLabels([tr("Name"), tr("Ursprünglicher Ort"), tr("Gelöscht"), tr("Größe")])
        self.tree.setRootIsDecorated(False)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setSortingEnabled(True)
        self.tree.itemDoubleClicked.connect(lambda *_: self.restore_selected())
        layout.addWidget(self.tree, 1)

        btn_row = QHBoxLayout()
        self.restore_btn = QPushButton(tr("Wiederherstellen"))
        self.restore_btn.clicked.connect(self.restore_selected)
        self.delete_btn = QPushButton(tr("Endgültig löschen"))
        self.delete_btn.clicked.connect(self.delete_selected)
        self.empty_btn = QPushButton(tr("Papierkorb leeren"))
        self.empty_btn.clicked.connect(self.empty_all)
        close_btn = QPushButton(tr("Schließen"))
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.restore_btn)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.empty_btn)
        btn_row.addStretch(1)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        self._reload()

    # ---------------------------------------------------------------- Helpers
    def _reload(self):
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        entries = trash.list_trash_entries()
        for e in entries:
            origin = os.path.dirname(e["original"]) if e["original"] else tr("— (unbekannt)")
            deleted = (e["deleted"] or "").replace("T", " ")
            item = QTreeWidgetItem([e["name"], origin, deleted, _fmt_size(e["size"])])
            item.setData(0, Qt.ItemDataRole.UserRole, e["trash_path"])
            if e["original"]:
                item.setToolTip(1, e["original"])
            self.tree.addTopLevelItem(item)
        self.tree.setSortingEnabled(True)
        for c in range(4):
            self.tree.resizeColumnToContents(c)

        n = len(entries)
        self.info.setText(tr("Der Papierkorb ist leer.") if n == 0
                          else f"{n} " + tr("Datei(en) im Papierkorb."))
        empty = n == 0
        self.restore_btn.setEnabled(not empty)
        self.delete_btn.setEnabled(not empty)
        self.empty_btn.setEnabled(not empty)

    def _selected_paths(self):
        return [it.data(0, Qt.ItemDataRole.UserRole) for it in self.tree.selectedItems()]

    def _refresh_app_views(self):
        """Aktualisiert Viewer/Galerie/Liste der Hauptanwendung nach Änderungen."""
        app = self._app
        if not app or not hasattr(app, "image_loader"):
            return
        d = app.image_loader.image_directory
        if not d:
            return
        app.image_loader.update_directory(d)
        if hasattr(app, "gallery_widget"):
            app.gallery_widget.update_directory(d)
        if hasattr(app, "list_view_widget"):
            app.list_view_widget.update_directory(d)

    # ----------------------------------------------------------------- Actions
    def restore_selected(self):
        paths = self._selected_paths()
        if not paths:
            return
        fallback = getattr(self._app.image_loader, "image_directory", None) \
            if hasattr(self._app, "image_loader") else None
        restored = 0
        for tp in paths:
            if trash.restore_entry(tp, fallback_dir=fallback):
                restored += 1
        self._reload()
        self._refresh_app_views()
        if hasattr(self._app, "statusBar"):
            self._app.statusBar.showMessage(
                f"{restored} " + tr("Datei(en) wiederhergestellt"), 3000)

    def delete_selected(self):
        paths = self._selected_paths()
        if not paths:
            return
        reply = QMessageBox.question(
            self, tr("Endgültig löschen"),
            f"{len(paths)} " + tr("Datei(en) endgültig löschen? Dies kann nicht rückgängig gemacht werden."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for tp in paths:
            trash.delete_entry(tp)
        self._reload()

    def empty_all(self):
        reply = QMessageBox.question(
            self, tr("Papierkorb leeren"),
            tr("Alle Dateien endgültig löschen? Dies kann nicht rückgängig gemacht werden."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        n = trash.empty_trash()
        self._reload()
        if hasattr(self._app, "statusBar"):
            self._app.statusBar.showMessage(tr("Papierkorb geleert") + f" ({n})", 3000)
