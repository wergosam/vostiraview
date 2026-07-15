import os
from datetime import datetime

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
                              QHeaderView, QAbstractItemView, QMenu, QApplication)
from PyQt6.QtGui import QImageReader, QPixmap, QIcon, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QTimer


# ── Sortierbares Item ──────────────────────────────────────────────────────────
class SortableItem(QTreeWidgetItem):
    COL_NAME       = 0
    COL_SIZE       = 1
    COL_FORMAT     = 2
    COL_RESOLUTION = 3
    COL_DATE       = 4
    COL_PATH       = 5

    def __init__(self, values, size_bytes, pixel_count, mtime):
        super().__init__(values)
        self._size_bytes  = size_bytes
        self._pixel_count = pixel_count
        self._mtime       = mtime

    def __lt__(self, other):
        col = self.treeWidget().sortColumn() if self.treeWidget() else 0
        if col == self.COL_SIZE:
            return self._size_bytes < other._size_bytes
        if col == self.COL_RESOLUTION:
            return self._pixel_count < other._pixel_count
        if col == self.COL_DATE:
            return self._mtime < other._mtime
        return self.text(col).lower() < other.text(col).lower()


# ── Format-Farben ─────────────────────────────────────────────────────────────
FORMAT_COLORS = {
    "JPG":  QColor(255, 248, 220),
    "JPEG": QColor(255, 248, 220),
    "PNG":  QColor(220, 235, 255),
    "GIF":  QColor(220, 255, 220),
    "BMP":  QColor(255, 220, 220),
    "WEBP": QColor(240, 220, 255),
}


# ── Thumbnail-Cache ───────────────────────────────────────────────────────────
class ThumbnailCache:
    SIZE = QSize(24, 24)

    def __init__(self, max_entries=800):
        self._cache = {}
        self._max   = max_entries

    def get(self, path):
        return self._cache.get(path)

    def load(self, path):
        if path in self._cache:
            return self._cache[path]
        reader = QImageReader(path)
        reader.setScaledSize(self.SIZE)
        img = reader.read()
        icon = QIcon(QPixmap.fromImage(img)) if not img.isNull() else QIcon()
        if len(self._cache) >= self._max:
            self._cache.pop(next(iter(self._cache)))
        self._cache[path] = icon
        return icon

    def clear(self):
        self._cache.clear()


# ── Hauptklasse ───────────────────────────────────────────────────────────────
class ImageListView(QWidget):
    image_clicked     = pyqtSignal(str)
    image_activated   = pyqtSignal(str)
    context_requested = pyqtSignal(str, object)
    delete_requested  = pyqtSignal(str)
    rename_requested  = pyqtSignal(str)

    SUPPORTED_FORMATS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

    def __init__(self, directory=""):
        super().__init__()
        self.directory = directory
        self._loaded   = False
        self._thumb_cache = ThumbnailCache()
        self._items = []
        self._load_index = 0
        self._load_timer = QTimer()
        self._load_timer.timeout.connect(self._load_next_batch)
        self._load_timer.setInterval(5)
        self._setup_ui()

    # ── UI ────────────────────────────────────────────────────────────────────
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(6)
        self.tree.setHeaderLabels(
            ["Dateiname", "Größe", "Format", "Auflösung", "Änderungsdatum", "Pfad"]
        )
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(False)
        self.tree.setSortingEnabled(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tree.setUniformRowHeights(True)
        self.tree.setIconSize(QSize(24, 24))

        header = self.tree.header()
        header.setSectionsMovable(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tree.setColumnHidden(5, True)

        self.tree.itemClicked.connect(self._on_single_click)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)

        self.tree.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        layout.addWidget(self.tree)

    # ── Daten laden (asynchron) ─────────────────────────────────────────────
    def update_directory(self, directory, sort_criterion=None, sort_order=None):
        # sort_criterion/sort_order werden für Signatur-Kompatibilität mit
        # gallery.update_directory akzeptiert; die Listenansicht sortiert
        # selbst über die Spaltenköpfe und lädt beim nächsten Anzeigen neu.
        self.directory = directory
        self._loaded   = False

    def showEvent(self, event):
        super().showEvent(event)
        if not self._loaded:
            self._load()

    def _load(self):
        self._loaded = True
        self.tree.setSortingEnabled(False)
        self.tree.clear()
        self._thumb_cache.clear()
        self._items.clear()
        self._load_index = 0

        if not self.directory or not os.path.exists(self.directory):
            self.tree.setSortingEnabled(True)
            return

        items = []
        for filename in sorted(os.listdir(self.directory), key=str.lower):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in self.SUPPORTED_FORMATS:
                continue

            full_path = os.path.join(self.directory, filename)

            try:
                size_bytes = os.path.getsize(full_path)
                size_str = self._format_size(size_bytes)
            except OSError:
                size_bytes = 0
                size_str = "—"

            fmt = ext.lstrip(".").upper()

            w, h = self._read_resolution(full_path)
            pixel_count = w * h
            resolution = f"{w} × {h}" if w else "—"

            try:
                mtime = os.path.getmtime(full_path)
                date_str = datetime.fromtimestamp(mtime).strftime("%d.%m.%Y  %H:%M")
            except OSError:
                mtime = 0
                date_str = "—"

            item = SortableItem(
                [filename, size_str, fmt, resolution, date_str, full_path],
                size_bytes, pixel_count, mtime
            )

            item.setTextAlignment(1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(3, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item.setTextAlignment(4, Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)

            color = FORMAT_COLORS.get(fmt)
            if color:
                for col in range(5):
                    item.setBackground(col, color)

            items.append(item)

        self._items = items
        self.tree.addTopLevelItems(items)

        self._load_index = 0
        self._load_timer.start()

    def _load_next_batch(self):
        batch_size = 20
        end = min(self._load_index + batch_size, len(self._items))
        for i in range(self._load_index, end):
            item = self._items[i]
            path = item.text(SortableItem.COL_PATH)
            icon = self._thumb_cache.load(path)
            item.setIcon(0, icon)

        self._load_index = end
        if self._load_index >= len(self._items):
            self._load_timer.stop()
            self.tree.setSortingEnabled(True)

    # ── Hilfsmethoden ────────────────────────────────────────────────────────
    @staticmethod
    def _format_size(b):
        if b >= 1_048_576:
            return f"{b / 1_048_576:.2f} MB"
        if b >= 1024:
            return f"{b / 1024:.1f} KB"
        return f"{b} B"

    @staticmethod
    def _read_resolution(path):
        reader = QImageReader(path)
        size = reader.size()
        if size.isValid():
            return size.width(), size.height()
        return 0, 0

    def refresh(self):
        self._loaded = False
        if self.isVisible():
            self._load()

    # ── Ereignisse ───────────────────────────────────────────────────────────
    def _on_single_click(self, item, _col):
        full_path = item.text(5)
        if full_path and os.path.exists(full_path):
            self.image_clicked.emit(full_path)

    def _on_double_click(self, item, _col):
        full_path = item.text(5)
        if full_path and os.path.exists(full_path):
            self.image_activated.emit(full_path)

    def _on_context_menu(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return
        full_path = item.text(5)

        menu = QMenu(self)

        act_open   = menu.addAction("Öffnen")
        menu.addSeparator()
        act_copy   = menu.addAction("Kopieren")
        act_cut    = menu.addAction("Ausschneiden")
        act_rename = menu.addAction("Umbenennen")
        act_delete = menu.addAction("Löschen")
        act_save_as= menu.addAction("Speichern unter")
        menu.addSeparator()
        act_copy_name = menu.addAction("Dateiname kopieren")
        act_copy_path = menu.addAction("Pfad kopieren")

        action = menu.exec(self.tree.viewport().mapToGlobal(pos))

        if action == act_open:
            self.image_activated.emit(full_path)
        elif action == act_copy:
            self.window().copy_image(full_path)
        elif action == act_cut:
            self.window().cut_image(full_path)
        elif action == act_rename:
            self.rename_requested.emit(full_path)
        elif action == act_delete:
            self.delete_requested.emit(full_path)
        elif action == act_save_as:
            self.window().save_image_as(full_path)
        elif action == act_copy_name:
            QApplication.clipboard().setText(os.path.basename(full_path))
        elif action == act_copy_path:
            QApplication.clipboard().setText(full_path)

    # ── Auswahl ──────────────────────────────────────────────────────────────
    def get_selected_images(self):
        return [item.text(5) for item in self.tree.selectedItems()]

    def clear_selection(self):
        self.tree.clearSelection()

    def select_all(self):
        self.tree.selectAll()