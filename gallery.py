import os
import shutil
from PyQt6.QtWidgets import (QWidget, QGridLayout, QLabel, QScrollArea,
                              QVBoxLayout, QHBoxLayout, QSizePolicy,
                              QFileDialog, QMessageBox, QFrame, QMenu,
                              QApplication)
from PyQt6.QtGui import QPixmap, QFont, QFontMetrics, QDragEnterEvent, QDropEvent, QPainter, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QMimeData, QRect

from config import load_config


class ImageGallery(QScrollArea):
    image_clicked      = pyqtSignal(str)
    selection_changed  = pyqtSignal(list)
    images_dropped     = pyqtSignal(list)
    context_requested  = pyqtSignal(str, object)

    def __init__(self, directory):
        super().__init__()
        self.directory = directory

        self.THUMBNAIL_SIZE = int(load_config().get("thumbnail_size", 200))
        self.MAX_COLUMNS = 5
        self.GRID_SPACING = 5
        self.VERTICAL_SPACING = 2
        self.MAX_IMAGES = 500

        self.gallery_widget = QWidget()
        self.main_layout = QHBoxLayout()
        self.gallery_layout = QGridLayout()
        self.main_layout.addLayout(self.gallery_layout)
        self.selection_layout = QHBoxLayout()
        self.main_layout.addLayout(self.selection_layout)
        self.gallery_widget.setLayout(self.main_layout)

        self.gallery_layout.setHorizontalSpacing(self.GRID_SPACING)
        self.gallery_layout.setVerticalSpacing(self.VERTICAL_SPACING)
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)

        self.setWidgetResizable(True)
        self.setWidget(self.gallery_widget)

        self.setAcceptDrops(True)
        self.gallery_widget.setAcceptDrops(True)

        self.supported_formats = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

        self.image_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_next_image)

        self.images = []
        self.selected_images = []
        self.containers = {}
        self.image_labels = {}
        self.sort_criterion = "name"
        self.sort_order = "asc"
        self.thumbnail_cache = {}

        self.prepare_image_list()
        self.default_columns = 5
        self.fullscreen_columns = self.calculate_columns()
        self.MAX_COLUMNS = self.default_columns

    # === Drag & Drop ===
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if self.is_image_file(url.toLocalFile()):
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if not event.mimeData().hasUrls():
            return
        image_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self.is_image_file(file_path):
                image_paths.append(file_path)
        if not image_paths:
            event.ignore()
            return

        msg_box = QMessageBox(self.window())
        msg_box.setWindowTitle("Bilder einfügen")
        msg_box.setIcon(QMessageBox.Icon.Question)
        count = len(image_paths)
        bild_text = "Bild" if count == 1 else "Bilder"
        msg_box.setText(f"Sie haben {count} {bild_text} in die Galerie gezogen.")
        msg_box.setInformativeText(
            "Möchten Sie die Bilder in den Viewer-Ordner kopieren?\n\n"
            "📁 Ja = In den Viewer-Ordner kopieren\n"
            "👁️ Nein = Nur in der Galerie anzeigen (Originale bleiben wo sie sind)"
        )
        copy_btn = msg_box.addButton("📁 Kopieren", QMessageBox.ButtonRole.YesRole)
        view_btn = msg_box.addButton("👁️ Nur anzeigen", QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg_box.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
        msg_box.setDefaultButton(copy_btn)
        msg_box.exec()

        clicked_button = msg_box.clickedButton()
        if clicked_button == copy_btn:
            copied_paths = self.copy_images_to_directory(image_paths)
            if copied_paths:
                self.update_gallery_after_copy(copied_paths)
                self.images_dropped.emit(copied_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        elif clicked_button == view_btn:
            self.add_images_to_gallery(image_paths)
            self.images_dropped.emit(image_paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def is_image_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats

    def copy_images_to_directory(self, image_paths):
        if not self.directory or not os.path.exists(self.directory):
            directory = QFileDialog.getExistingDirectory(
                self.window(),
                "Wählen Sie einen Ordner zum Speichern der Bilder",
                os.path.expanduser("~"),
                options=QFileDialog.Option.ShowDirsOnly
            )
            if directory:
                self.directory = directory
                if hasattr(self.window(), 'image_loader'):
                    self.window().image_loader.image_directory = directory
                from config import save_config
                save_config(directory)
            else:
                return []

        copied_paths = []
        failed_paths = []
        for src_path in image_paths:
            try:
                filename = os.path.basename(src_path)
                dest_path = os.path.join(self.directory, filename)
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(dest_path):
                    new_name = f"{base_name}_{counter}{ext}"
                    dest_path = os.path.join(self.directory, new_name)
                    counter += 1
                shutil.copy2(src_path, dest_path)
                copied_paths.append(dest_path)
            except Exception as e:
                print(f"Fehler beim Kopieren von {src_path}: {e}")
                failed_paths.append(os.path.basename(src_path))

        if copied_paths and hasattr(self.window(), 'statusBar'):
            self.window().statusBar.showMessage(
                f"{len(copied_paths)} Bild(er) wurden in den Viewer-Ordner kopiert",
                5000
            )
        if failed_paths:
            QMessageBox.warning(
                self.window(),
                "Fehler beim Kopieren",
                f"Die folgenden Bilder konnten nicht kopiert werden:\n\n" +
                "\n".join(failed_paths) +
                "\n\nMöglicherweise haben Sie keine Schreibrechte für den Zielordner."
            )
        return copied_paths

    def update_gallery_after_copy(self, copied_paths):
        if hasattr(self.window(), 'image_loader'):
            self.window().image_loader.update_directory(self.directory)
        if hasattr(self.window(), 'gallery_widget'):
            self.window().gallery_widget.update_directory(self.directory)
        self.update_directory(self.directory)
        if hasattr(self.window(), 'switch_view'):
            self.window().switch_view(1)

    def add_images_to_gallery(self, image_paths):
        if not image_paths:
            return
        added = 0
        for path in image_paths:
            if os.path.exists(path) and path not in self.images:
                self.images.append(os.path.basename(path))
                added += 1
        if added > 0:
            self.sort_images()
            self.image_index = 0
            self.clear_gallery()
            self.prepare_image_list()
            self.timer.start(10)
            if hasattr(self.window(), 'statusBar'):
                self.window().statusBar.showMessage(f"{added} Bild(er) hinzugefügt", 3000)
            if hasattr(self.window(), 'switch_view'):
                self.window().switch_view(1)

    # === Auswahl ===
    def toggle_selection(self, image_path):
        full_path = os.path.abspath(image_path)
        if full_path in self.selected_images:
            self.selected_images.remove(full_path)
        else:
            self.selected_images.append(full_path)
        self.update_selection_frame(full_path)
        self.selection_changed.emit(self.selected_images)

    def update_selection_frame(self, full_path):
        if full_path in self.image_labels:
            label = self.image_labels[full_path]
            if full_path in self.selected_images:
                label.setStyleSheet("border: 1px solid red;")
            else:
                label.setStyleSheet("border: none;")

    def get_selected_images(self):
        return self.selected_images

    def clear_selection(self):
        for full_path in list(self.selected_images):
            if full_path in self.image_labels:
                self.image_labels[full_path].setStyleSheet("border: none;")
        self.selected_images.clear()
        self.selection_changed.emit(self.selected_images)

    def select_all(self):
        for full_path in self.image_labels.keys():
            if full_path not in self.selected_images:
                self.selected_images.append(full_path)
                self.update_selection_frame(full_path)
        self.selection_changed.emit(self.selected_images)

    # === Bild mit Dateinamen ===
    def _add_filename_to_pixmap(self, pixmap, filename):
        if pixmap.isNull():
            return pixmap
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = pixmap.rect()
        text_rect = QRect(0, rect.height() - 25, rect.width(), 25)
        painter.fillRect(text_rect, QColor(0, 0, 0, 150))
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        metrics = QFontMetrics(font)
        elided = metrics.elidedText(filename, Qt.TextElideMode.ElideRight, rect.width() - 10)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, elided)
        painter.end()
        return pixmap

    # === Laden und Sortieren ===
    def prepare_image_list(self):
        self.setUpdatesEnabled(False)
        if not self.directory or not os.path.exists(self.directory):
            self.images = []
            self.image_index = 0
            self.setUpdatesEnabled(True)
            return
        self.images = [
            f for f in os.listdir(self.directory)
            if os.path.splitext(f)[1].lower() in self.supported_formats
        ][:self.MAX_IMAGES]
        self.images.sort(key=lambda x: x.lower())
        self.sort_images()
        self.image_index = 0
        if self.images:
            self.timer.start(10)
        self.setUpdatesEnabled(True)

    def sort_images(self):
        if not self.directory or not os.path.exists(self.directory):
            return
        reverse = self.sort_order == "desc"
        if self.sort_criterion == "name":
            self.images.sort(key=lambda x: x.lower(), reverse=reverse)
        elif self.sort_criterion == "date":
            self.images.sort(key=lambda x: os.path.getmtime(os.path.join(self.directory, x)), reverse=reverse)
        elif self.sort_criterion == "size":
            self.images.sort(key=lambda x: os.path.getsize(os.path.join(self.directory, x)), reverse=reverse)

    def load_next_image(self):
        if self.image_index >= len(self.images):
            self.timer.stop()
            return
        image = self.images[self.image_index]
        full_path = os.path.join(self.directory, image)
        row = self.image_index // self.MAX_COLUMNS
        col = self.image_index % self.MAX_COLUMNS

        if full_path not in self.thumbnail_cache:
            pixmap = QPixmap(full_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    self.THUMBNAIL_SIZE, self.THUMBNAIL_SIZE,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                scaled = self._add_filename_to_pixmap(scaled, image)
                self.thumbnail_cache[full_path] = scaled
            else:
                self.thumbnail_cache[full_path] = QPixmap()

        scaled = self.thumbnail_cache[full_path]
        img_width = scaled.width() if not scaled.isNull() else self.THUMBNAIL_SIZE
        img_height = scaled.height() if not scaled.isNull() else self.THUMBNAIL_SIZE

        container = QFrame()
        container.setFixedSize(img_width, img_height)
        container.setFrameShape(QFrame.Shape.NoFrame)
        container.setStyleSheet("border: none; background: transparent;")
        container.setProperty("image_path", full_path)
        self.containers[full_path] = container

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        # Auswahl-Markierung beim (Neu-)Aufbau wiederherstellen
        if full_path in self.selected_images:
            image_label.setStyleSheet("border: 1px solid red;")
        else:
            image_label.setStyleSheet("border: none; background: transparent;")
        self.image_labels[full_path] = image_label

        if not scaled.isNull():
            image_label.setPixmap(scaled)

        image_label.mouseDoubleClickEvent = lambda event, path=full_path: self.image_clicked.emit(path)
        image_label.mousePressEvent = lambda event, path=full_path: self._on_press(event, path)
        container.mousePressEvent  = lambda event, path=full_path: self._on_press(event, path)

        layout.addWidget(image_label)
        self.gallery_layout.addWidget(container, row, col, Qt.AlignmentFlag.AlignHCenter)

        self.image_index += 1

    def on_image_click(self, image_path):
        self.image_clicked.emit(image_path)

    # ===== KONTEXTMENÜ FÜR GALERIE =====
    def _on_press(self, event, path):
        if event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(path, event.globalPosition().toPoint())
        else:
            self.toggle_selection(path)

    def _show_context_menu(self, path, global_pos):
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

        action = menu.exec(global_pos)

        if action == act_open:
            self.image_clicked.emit(path)
        elif action == act_copy:
            self.window().copy_image(path)
        elif action == act_cut:
            self.window().cut_image(path)
        elif action == act_rename:
            self.window().rename_image(path)
        elif action == act_delete:
            self.window().delete_image(path)
        elif action == act_save_as:
            self.window().save_image_as(path)
        elif action == act_copy_name:
            QApplication.clipboard().setText(os.path.basename(path))
        elif action == act_copy_path:
            QApplication.clipboard().setText(path)

    # ===== Ende Kontextmenü =====

    def update_directory(self, directory, sort_criterion=None, sort_order=None):
        self.directory = directory
        if sort_criterion:
            self.sort_criterion = sort_criterion
        if sort_order:
            self.sort_order = sort_order
        if self.timer.isActive():
            self.timer.stop()
        self.clear_gallery()
        self.prepare_image_list()
        if self.images:
            self.image_index = 0
            self.timer.start(50)

    def clear_gallery(self):
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.images = []
        self.selected_images = []
        self.image_index = 0
        self.thumbnail_cache.clear()
        self.containers.clear()
        self.image_labels.clear()

    def refresh_preserving_cache(self):
        """Aktualisiert die Galerie nach einer Verzeichnisänderung durch den
        DirectoryWatcher. Im Gegensatz zu clear_gallery() bleibt der
        Thumbnail-Cache erhalten – nur Thumbnails gelöschter Dateien werden
        verworfen, sodass bestehende Bilder nicht neu gerendert werden."""
        if self.timer.isActive():
            self.timer.stop()
        # Auswahl auf weiterhin vorhandene Bilder beschränken
        self.selected_images = [p for p in self.selected_images if os.path.exists(p)]
        # Cache gelöschter Dateien verwerfen (Speicher freigeben)
        for cached_path in list(self.thumbnail_cache.keys()):
            if not os.path.exists(cached_path):
                self.thumbnail_cache.pop(cached_path, None)
        # Nur die Grid-Widgets entfernen (Cache + Auswahl bleiben erhalten)
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.containers.clear()
        self.image_labels.clear()
        # Bildliste neu aufbauen; prepare_image_list startet den Render-Timer,
        # der für bestehende Bilder den Cache wiederverwendet.
        self.image_index = 0
        self.prepare_image_list()

    def resizeEvent(self, event):
        new_columns = self.calculate_columns()
        if new_columns != self.MAX_COLUMNS:
            self.setUpdatesEnabled(False)
            self.MAX_COLUMNS = new_columns
            self.rearrange_gallery()
            self.setUpdatesEnabled(True)
        super().resizeEvent(event)

    def calculate_columns(self):
        available_width = self.width()
        column_width = self.THUMBNAIL_SIZE + self.GRID_SPACING
        return max(5, available_width // column_width)

    def rearrange_gallery(self):
        containers = []
        while self.gallery_layout.count():
            item = self.gallery_layout.takeAt(0)
            if item and item.widget():
                containers.append(item.widget())
        for index, container in enumerate(containers):
            row = index // self.MAX_COLUMNS
            col = index % self.MAX_COLUMNS
            self.gallery_layout.addWidget(container, row, col, Qt.AlignmentFlag.AlignHCenter)