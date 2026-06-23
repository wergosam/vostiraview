import sys
import os
import shutil
from PyQt6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QWidget,
                             QLabel, QSizePolicy, QStackedWidget, QMessageBox,
                             QFileDialog, QStatusBar, QMenu)
from PyQt6.QtGui import (QPixmap, QKeyEvent, QWheelEvent, QFont, QFontMetrics,
                         QDragEnterEvent, QDropEvent, QPainter)
from PyQt6.QtCore import Qt, QPoint, QTimer, QMimeData, QRect

from config import load_config, save_config, get_last_directory, set_last_directory
from crop import ImageCropperWidget
from gallery import ImageGallery
from list_view import ImageListView
from utils import resource_path

# Importe aus den Modulen
from modules.image_loader import ImageLoader
from modules.image_operations import ImageOperations
from modules.file_operations import FileOperations
from modules.zoom_handler import ZoomHandler
from modules.gallery_handler import GalleryHandler
from modules.search_handler import SearchHandler
from modules.slideshow_handler import SlideshowHandler
from modules.help_handler import HelpHandler
from modules.exif_handler import ExifHandler
from modules.clipboard_handler import ClipboardHandler
from modules.undo_manager import UndoManager
from modules.directory_watcher import DirectoryWatcher
from modules.image_export import (build_filter_string, format_for_extension,
                                  ensure_extension, save_pixmap_as)
from ui.main_window import MainWindowUI
from i18n import tr


class ImageViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VostiraView")

        # Config laden (wird u. a. für Start-Fenstergröße benötigt)
        self.config = load_config()

        # Oberflächensprache setzen, bevor die UI gebaut wird
        from i18n import init_language
        init_language()
        self.resize(int(self.config.get("window_width", 1280)),
                    int(self.config.get("window_height", 800)))

        # Status-Variablen
        self._normal_geometry = None
        self._resizing = False
        self.current_sort_criterion = self.config.get("sort_criterion", "name")
        self.current_sort_order = self.config.get("sort_order", "asc")

        # Zoom-Variablen
        self.zoom_factor = 1.0
        self._zoom_offset = QPoint(0, 0)   # Verschiebung des Zoom-Ausschnitts (in Pixeln)
        self._original_pixmap = None

        # Drag & Drop aktivieren
        self.setAcceptDrops(True)

        # Module initialisieren (Reihenfolge wichtig)
        self.image_loader = ImageLoader(self)
        self.image_ops = ImageOperations(self)
        self.file_ops = FileOperations(self)
        self.zoom_handler = ZoomHandler(self)
        self.gallery_handler = GalleryHandler(self)
        self.search_handler = SearchHandler(self)
        interval = self.config.get("slideshow_interval", 3000)
        self.slideshow_handler = SlideshowHandler(self, interval=interval)
        self.help_handler = HelpHandler(self)
        self.exif_handler = ExifHandler(self)
        self.clipboard_handler = ClipboardHandler(self)
        self.undo_manager = UndoManager(self)

        # UI erstellen
        self.ui = MainWindowUI(self)
        self.setup_ui()
        self.setup_crop_functionality()

        # StatusBar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        # Permanente Zoom-Anzeige rechts in der Statusleiste
        self.zoom_label = QLabel("")
        self.zoom_label.setStyleSheet("padding: 0 8px; color: #444;")
        self.statusBar.addPermanentWidget(self.zoom_label)

        # Initiales Verzeichnis laden
        self.image_loader.select_initial_directory()

        # Galerie-Widget aktualisieren
        if hasattr(self, "gallery_widget"):
            self.gallery_widget.update_directory(self.image_loader.image_directory)
            self.gallery_widget.images_dropped.connect(self.on_images_dropped)

        # Listenansicht
        if hasattr(self, "list_view_widget"):
            self.list_view_widget.directory = self.image_loader.image_directory

        # Verzeichnis-Watcher (automatische Aktualisierung der Galerie)
        self.directory_watcher = DirectoryWatcher(self)
        self.directory_watcher.set_directory(self.image_loader.image_directory)

        # UI-Status aktualisieren
        self.update_toolbar_buttons()
        self.update_menu_items()

    def refresh_current_directory_from_watcher(self):
        """Wird (entprellt) vom DirectoryWatcher aufgerufen, wenn sich der
        Inhalt des Bildverzeichnisses geändert hat. Aktualisiert Bildliste,
        Galerie und Listenansicht unter Beibehaltung des aktuellen Bildes."""
        added, removed = self.image_loader.refresh_directory_preserving_state()
        if added == 0 and removed == 0:
            return   # keine bildrelevante Änderung

        if hasattr(self, "gallery_widget"):
            # Galerie auf das überwachte Verzeichnis synchronisieren, dann
            # cache-schonend neu aufbauen.
            self.gallery_widget.directory = self.image_loader.image_directory
            self.gallery_widget.refresh_preserving_cache()
        if hasattr(self, "list_view_widget"):
            self.list_view_widget.update_directory(self.image_loader.image_directory)

        # Bildinfo (Zähler x/y) und Toolbar aktualisieren
        loader = self.image_loader
        if loader.image_paths and 0 <= loader.current_index < len(loader.image_paths):
            self.update_image_info(loader.image_paths[loader.current_index])
        self.update_toolbar_buttons()

        parts = []
        if added:
            parts.append(f"{added} neu")
        if removed:
            parts.append(f"{removed} entfernt")
        self.statusBar.showMessage(tr("Verzeichnis aktualisiert") + " (" + ", ".join(parts) + ")", 3000)

    # ==================== DRAG & DROP ====================
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
        if image_paths:
            self.handle_dropped_images(image_paths)
            event.acceptProposedAction()
        else:
            event.ignore()

    def is_image_file(self, file_path):
        supported = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']
        return os.path.splitext(file_path)[1].lower() in supported

    def handle_dropped_images(self, image_paths):
        if not image_paths:
            return
        if len(image_paths) == 1:
            self.show_single_image_dialog(image_paths[0])
        else:
            self.show_multiple_images_dialog(image_paths)

    def show_single_image_dialog(self, image_path):
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("Bild geöffnet"))
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(tr("Sie haben das Bild „{name}“ geöffnet.").format(name=os.path.basename(image_path)))
        msg.setInformativeText(
            tr("Was möchten Sie tun?\n\n👁️ Direkt anzeigen\n📁 In Galerie kopieren\n👁️‍🗨️ Nur in Galerie anzeigen")
        )
        view_btn = msg.addButton(tr("👁️ Direkt anzeigen"), QMessageBox.ButtonRole.YesRole)
        copy_btn = msg.addButton(tr("📁 In Galerie kopieren"), QMessageBox.ButtonRole.ActionRole)
        show_btn = msg.addButton(tr("👁️‍🗨️ Nur anzeigen"), QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg.addButton(tr("Abbrechen"), QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(view_btn)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == view_btn:
            self.image_loader.load_image(image_path)
            self.statusBar.showMessage(tr("Bild geladen:") + f" {os.path.basename(image_path)}", 3000)
        elif clicked == copy_btn:
            copied = self.gallery_widget.copy_images_to_directory([image_path])
            if copied:
                self.gallery_widget.update_gallery_after_copy(copied)
                self.image_loader.update_directory(self.image_loader.image_directory)
                self.statusBar.showMessage(tr("Bild in Galerie kopiert:") + f" {os.path.basename(image_path)}", 3000)
        elif clicked == show_btn:
            self.gallery_widget.add_images_to_gallery([image_path])
            self.statusBar.showMessage(tr("Bild in Galerie angezeigt:") + f" {os.path.basename(image_path)}", 3000)

    def show_multiple_images_dialog(self, image_paths):
        count = len(image_paths)
        msg = QMessageBox(self)
        msg.setWindowTitle(tr("Bilder geöffnet"))
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(tr("Sie haben {count} Bilder geöffnet.").format(count=count))
        msg.setInformativeText(
            tr("Was möchten Sie tun?\n\n📁 In Galerie kopieren\n👁️‍🗨️ Nur in Galerie anzeigen")
        )
        copy_btn = msg.addButton(tr("📁 Alle kopieren"), QMessageBox.ButtonRole.YesRole)
        show_btn = msg.addButton(tr("👁️‍🗨️ Nur anzeigen"), QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg.addButton(tr("Abbrechen"), QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(copy_btn)
        msg.exec()
        clicked = msg.clickedButton()
        if clicked == copy_btn:
            copied = self.gallery_widget.copy_images_to_directory(image_paths)
            if copied:
                self.gallery_widget.update_gallery_after_copy(copied)
                self.image_loader.update_directory(self.image_loader.image_directory)
                self.statusBar.showMessage(f"{len(copied)} " + tr("Bilder in Galerie kopiert"), 3000)
        elif clicked == show_btn:
            self.gallery_widget.add_images_to_gallery(image_paths)
            self.statusBar.showMessage(f"{len(image_paths)} " + tr("Bilder in Galerie angezeigt"), 3000)

    def on_images_dropped(self, image_paths):
        self.image_loader.update_directory(self.image_loader.image_directory)
        if hasattr(self, "list_view_widget"):
            self.list_view_widget.update_directory(self.image_loader.image_directory)
        self.statusBar.showMessage(f"{len(image_paths)} " + tr("Bild(er) in Galerie hinzugefügt"), 3000)

    # ==================== NEUE HILFSMETHODEN ====================
    def _get_active_image_path(self) -> str | None:
        """Gibt den Pfad des aktiv selektierten Bildes zurück (Galerie, Liste oder Viewer).
        Zeigt eine Warnung und gibt None zurück, wenn kein Bild ausgewählt ist."""
        current = self.stacked_widget.currentIndex()
        path = None
        if current == 1:
            sel = self.gallery_widget.get_selected_images()
            if sel:
                path = sel[0]
        elif current == 3:
            sel = self.list_view_widget.get_selected_images()
            if sel:
                path = sel[0]
        if path is None:
            if self.image_loader.image_paths and self.image_loader.current_index >= 0:
                path = self.image_loader.image_paths[self.image_loader.current_index]
            else:
                QMessageBox.warning(self, tr("Kein Bild"), tr("Bitte wählen Sie ein Bild aus."))
                return None
        if path not in self.image_loader.image_paths:
            QMessageBox.warning(self, tr("Fehler"), tr("Das ausgewählte Bild ist nicht in der Liste."))
            return None
        self.image_loader.current_index = self.image_loader.image_paths.index(path)
        return path

    def rename_selected_image(self):
        if self._get_active_image_path() is not None:
            self.file_ops.rename_image()

    def delete_selected_image(self):
        if self._get_active_image_path() is not None:
            self.image_ops.delete_image()

    def open_settings(self):
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    # ==================== UI SETUP ====================
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout()
        central.setLayout(self.layout)

        self.ui.create_menu()
        self.ui.create_toolbar()

        self.image_info_label = QLabel("Keine Bildinformationen")
        self.image_info_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.image_info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                padding: 5px;
                border-bottom: 1px solid #ddd;
                font-size: 11px;
            }
        """)
        self.image_info_label.setWordWrap(True)
        self.layout.addWidget(self.image_info_label)

        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)

        # VostiraView
        self.image_container = QWidget()
        self.image_container.setAcceptDrops(True)
        self.image_container_layout = QVBoxLayout()
        self.image_container_layout.setContentsMargins(0, 0, 0, 0)
        self.image_container.setLayout(self.image_container_layout)

        self.image_viewer = QLabel(self)
        self.image_viewer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_viewer.setText(tr("Kein Bild geladen"))
        self.image_viewer.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_viewer.setAcceptDrops(True)
        self.image_viewer.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.image_viewer.customContextMenuRequested.connect(self._show_viewer_context_menu)
        self.image_viewer.wheelEvent = self.wheel_event
        self.image_container_layout.addWidget(self.image_viewer)
        self.stacked_widget.addWidget(self.image_container)

        # Galerie
        self.gallery_widget = ImageGallery("")
        self.gallery_widget.image_clicked.connect(self._gallery_image_clicked)
        self.stacked_widget.addWidget(self.gallery_widget)

        self.stacked_widget.setCurrentIndex(0)
        self.image_viewer.setText(tr("Kein Bild geladen"))

    def _gallery_image_clicked(self, path):
        self.image_loader.load_image(path)
        self.switch_view(0)

    def setup_crop_functionality(self):
        self.crop_widget = ImageCropperWidget(self)
        self.stacked_widget.addWidget(self.crop_widget)
        self.crop_widget.cropped_image_signal.connect(self.handle_cropped_image)

        self.list_view_widget = ImageListView("")
        self.list_view_widget.image_clicked.connect(self.image_loader.load_image)
        self.list_view_widget.image_activated.connect(self._list_view_open_image)
        self.list_view_widget.delete_requested.connect(self._list_view_delete)
        self.list_view_widget.rename_requested.connect(self._list_view_rename)
        self.stacked_widget.addWidget(self.list_view_widget)

    def handle_cropped_image(self, cropped_pixmap):
        if cropped_pixmap and self.image_loader.current_index >= 0:
            cur = self.image_loader.image_paths[self.image_loader.current_index]

            # Überschreiben-Modus: nach Bestätigung direkt ins Original schreiben
            if self.image_ops._overwrite_mode():
                if self.image_ops._save_edit(
                        "Zuschneiden", cur,
                        lambda p: save_pixmap_as(cropped_pixmap, p, format_for_extension(os.path.splitext(p)[1]))):
                    self.stacked_widget.setCurrentIndex(0)
                    QMessageBox.information(self, tr("Erfolg"), tr("Bild zugeschnitten und gespeichert."))
                return

            directory = os.path.dirname(cur)
            base, ext = os.path.splitext(os.path.basename(cur))
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                tr("Zugeschnittenes Bild speichern"),
                os.path.join(directory, f"{base}_cropped{ext}"),
                build_filter_string()
            )
            if file_path:
                file_path, save_ext = ensure_extension(file_path, selected_filter)
                if save_pixmap_as(cropped_pixmap, file_path, format_for_extension(save_ext)):
                    # Zustand vor der Änderung für Rückgängig sichern
                    prev_path = self.image_loader.image_paths[self.image_loader.current_index]

                    self.image_loader.image_paths.append(file_path)
                    self.image_loader.current_index = len(self.image_loader.image_paths) - 1
                    self.image_loader.load_image(file_path)
                    self.gallery_widget.update_directory(self.image_loader.image_directory)
                    self.stacked_widget.setCurrentIndex(0)

                    # Rückgängig/Wiederholen für das Zuschneiden registrieren
                    self.image_ops._push_added_file_command("Zuschneiden", file_path, prev_path)

                    QMessageBox.information(self, tr("Erfolg"), tr("Bild zugeschnitten und gespeichert."))
                else:
                    QMessageBox.warning(self, tr("Fehler"), tr("Konnte nicht speichern."))

    def exit_crop_mode(self):
        if hasattr(self, 'crop_widget'):
            self.crop_widget.reset_crop_state()
        self.stacked_widget.setCurrentIndex(0)

    # ==================== ZOOM & ANZEIGE ====================
    def calculate_fit_to_window_zoom(self):
        if not self.image_loader._original_pixmap or self.image_loader._original_pixmap.isNull():
            return 1.0
        if self.isFullScreen():
            avail = self.screen().availableGeometry()
            tw, th = avail.width(), avail.height()
        else:
            tw, th = self.width(), self.height() - 80
        tw, th = max(300, tw), max(200, th)
        ow, oh = self.image_loader._original_pixmap.width(), self.image_loader._original_pixmap.height()
        return min(tw / ow, th / oh)

    def update_image_info(self, image_path):
        if not image_path or not os.path.exists(image_path):
            self.image_info_label.setText(tr("Keine Bildinformationen"))
            return
        file_name = os.path.basename(image_path)
        file_size = os.path.getsize(image_path) / 1024
        # Bereits geladenes Original-Pixmap wiederverwenden statt Bild neu laden
        pm = self.image_loader._original_pixmap
        if pm and not pm.isNull():
            width, height = pm.width(), pm.height()
        else:
            tmp = QPixmap(image_path)
            width, height = tmp.width(), tmp.height()
        fm = QFontMetrics(self.image_info_label.font())
        short_name = fm.elidedText(file_name, Qt.TextElideMode.ElideMiddle, 800)
        info = f"{short_name}  ▒  {width}x{height}px  ▒  {file_size:.2f} KB  ▒  {self.image_loader.current_index+1}/{len(self.image_loader.image_paths)}"
        if self.zoom_factor == 1.0:
            info += "  ▒  🔍 An Fenster anpassen"
        else:
            fit = self.calculate_fit_to_window_zoom()
            if fit > 0:
                zoom_percent = int((self.zoom_factor / fit) * 100)
                info += f"  ▒  Zoom: {zoom_percent}%"
        exif = self.exif_handler.get_exif_string(image_path)
        if exif:
            info += f"\n{exif}"
        self.image_info_label.setText(info)

    def _display_pixmap(self):
        if not self.image_loader._original_pixmap or self.image_loader._original_pixmap.isNull():
            return

        if self.zoom_handler._zoom_mode:
            self._display_zoomed_pixmap()
            return

        # Fit to window
        self.zoom_factor = 1.0
        self._zoom_offset = QPoint(0, 0)

        if self.isFullScreen():
            avail = self.screen().availableGeometry()
            tw, th = avail.width(), avail.height()
        else:
            tw, th = self.width(), self.height() - 80
        tw, th = max(300, tw), max(200, th)

        scaled = self.image_loader._original_pixmap.scaled(
            tw, th,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_loader._pixmap = scaled
        self.image_viewer.setPixmap(scaled)
        self._update_zoom_label()

    def _update_zoom_label(self):
        """Aktualisiert die permanente Zoom-Prozentanzeige (100 % = Originalgröße)."""
        if not hasattr(self, "zoom_label"):
            return
        pm = self.image_loader._original_pixmap
        if not pm or pm.isNull():
            self.zoom_label.setText("")
            return
        if self.zoom_handler._zoom_mode:
            pct = self.zoom_factor * 100
        else:
            pct = self.calculate_fit_to_window_zoom() * 100
        self.zoom_label.setText(f"{int(round(pct))} %")

    def _display_zoomed_pixmap(self):
        if not self.image_loader._original_pixmap or self.image_loader._original_pixmap.isNull():
            return

        # Bildgröße (Original)
        orig_w = self.image_loader._original_pixmap.width()
        orig_h = self.image_loader._original_pixmap.height()

        # Zoom-Faktor (relativ zur Originalgröße)
        zoom = self.zoom_factor
        # Gezoomte Größe in Pixeln (auf Original bezogen)
        zoom_w = int(orig_w * zoom)
        zoom_h = int(orig_h * zoom)

        # Begrenzung des Offsets (damit nicht leerer Rand entsteht)
        max_offset_x = max(0, zoom_w - self.image_viewer.width())
        max_offset_y = max(0, zoom_h - self.image_viewer.height())

        # Offset anwenden (von der Mitte ausgehend)
        ox = self._zoom_offset.x()
        oy = self._zoom_offset.y()
        ox = max(-max_offset_x, min(0, ox))
        oy = max(-max_offset_y, min(0, oy))

        # Ausschnitt aus dem Original berechnen
        # Wir skalieren das Original so, dass es in den Viewer passt, dann den Ausschnitt
        # Besser: Wir schneiden aus dem Original den sichtbaren Bereich aus und skalieren auf Viewer-Größe
        # aber einfacher: Skaliertes Bild erzeugen und dann mit QPainter ausschneiden
        scaled = self.image_loader._original_pixmap.scaled(
            zoom_w, zoom_h,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Viewer-Größe
        vw = self.image_viewer.width()
        vh = self.image_viewer.height()

        # Startkoordinaten im skalierten Bild
        sx = -ox  # da ox negativ ist, wird sx positiv
        sy = -oy
        # Sicherstellen, dass sx/sy innerhalb des Bildes liegen
        sx = max(0, min(sx, scaled.width() - vw))
        sy = max(0, min(sy, scaled.height() - vh))

        # Ausschnitt kopieren
        cropped = scaled.copy(QRect(sx, sy, min(vw, scaled.width()-sx), min(vh, scaled.height()-sy)))
        self.image_loader._pixmap = cropped
        self.image_viewer.setPixmap(cropped)
        self._update_zoom_label()

    def clear_image_display(self):
        self.image_viewer.clear()
        self.image_viewer.setText(tr("Kein Bild geladen"))
        self.image_info_label.setText(tr("Keine Bildinformationen"))
        self.image_loader._pixmap = QPixmap()

    # ==================== VOLLBILD ====================
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            if self._normal_geometry is not None:
                self.setGeometry(self._normal_geometry)
        else:
            self._normal_geometry = self.geometry()
            self.showFullScreen()
        self._display_pixmap()

    # ==================== RESIZE ====================
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._resizing:
            return
        self._resizing = True
        self._display_pixmap()
        self._resizing = False

    # ==================== MAUS & TASTATUR ====================
    def wheel_event(self, event: QWheelEvent):
        self.zoom_handler.wheel_event(event)

    def mousePressEvent(self, event):
        if not self.zoom_handler.mouse_press_event(event):
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.zoom_handler.mouse_move_event(event):
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.zoom_handler.mouse_release_event(event):
            super().mouseReleaseEvent(event)

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self._zoom_offset = QPoint(0, 0)
        self._display_pixmap()
        self.update_image_info(self.image_loader.image_paths[self.image_loader.current_index] if self.image_loader.image_paths else None)
        self.statusBar.showMessage(tr("Zoom: An Fenster anpassen"), 2000)

    def keyPressEvent(self, event: QKeyEvent):
        if self.clipboard_handler.handle_key_press(event):
            return
        key = event.key()
        if key == Qt.Key.Key_Right:
            self.image_loader.navigate_image(1)
        elif key == Qt.Key.Key_Left:
            self.image_loader.navigate_image(-1)
        elif key == Qt.Key.Key_Delete:
            self.delete_selected_image()
        elif key == Qt.Key.Key_G:
            self.switch_view(1)
        elif key == Qt.Key.Key_L:
            self.switch_view(3)
        elif key == Qt.Key.Key_S:
            self.file_ops.save_image_as()
        elif key == Qt.Key.Key_U:
            self.rename_selected_image()
        elif key == Qt.Key.Key_Z:
            self.zoom_handler.toggle_zoom_mode()
        elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_handler.zoom_in()
        elif key == Qt.Key.Key_Minus:
            self.zoom_handler.zoom_out()
        elif key == Qt.Key.Key_0:
            self.zoom_handler.zoom_to_fit()
        elif key == Qt.Key.Key_1:
            self.zoom_handler.zoom_actual()
        elif key == Qt.Key.Key_P:
            self.slideshow_handler.toggle_slideshow()
        elif key == Qt.Key.Key_C:
            self.image_ops.start_crop_mode()
        elif key == Qt.Key.Key_A:
            self.image_ops.resize_current_image()
        elif key == Qt.Key.Key_D:
            self.image_ops.rotate_current_image()
        elif key == Qt.Key.Key_B:
            self.image_ops.adjust_current_image()
        elif key == Qt.Key.Key_V:
            self.toggle_fullscreen()
        elif key == Qt.Key.Key_O:
            self.image_loader.open_file()
        elif key == Qt.Key.Key_X:
            self.close()
        elif key == Qt.Key.Key_F:
            self.search_handler.open_search_dialog()
        elif key == Qt.Key.Key_E:
            self.exif_handler.show_exif_data()
        elif key == Qt.Key.Key_R:
            self.reset_zoom()
        elif key in (Qt.Key.Key_H, Qt.Key.Key_Question):
            self.help_handler.show_shortcuts()
        else:
            super().keyPressEvent(event)

    # ==================== KONTEXTMENÜ VIEWER ====================
    def _show_viewer_context_menu(self, pos):
        if not self.image_loader.image_paths or self.image_loader.current_index < 0:
            return
        cur = self.image_loader.image_paths[self.image_loader.current_index]
        if not cur or not os.path.exists(cur):
            return
        menu = QMenu(self)
        act_rename = menu.addAction(tr("Umbenennen"))
        act_delete = menu.addAction(tr("Löschen"))
        act_save_as = menu.addAction(tr("Speichern unter"))
        menu.addSeparator()
        act_copy_name = menu.addAction(tr("Dateiname kopieren"))
        act_copy_path = menu.addAction(tr("Pfad kopieren"))
        menu.addSeparator()
        act_fullscreen = menu.addAction(tr("Vollbild umschalten"))
        act_reset_zoom = menu.addAction(tr("Zoom zurücksetzen"))

        action = menu.exec(self.image_viewer.mapToGlobal(pos))
        if action == act_rename:
            self.rename_selected_image()
        elif action == act_delete:
            self.delete_selected_image()
        elif action == act_save_as:
            self.file_ops.save_image_as()
        elif action == act_copy_name:
            QApplication.clipboard().setText(os.path.basename(cur))
        elif action == act_copy_path:
            QApplication.clipboard().setText(cur)
        elif action == act_fullscreen:
            self.toggle_fullscreen()
        elif action == act_reset_zoom:
            self.reset_zoom()

    # ==================== LISTENANSICHT ====================
    def _list_view_open_image(self, path):
        self.image_loader.load_image(path)
        self.switch_view(0)

    def _list_view_delete(self, path):
        self.delete_selected_image()

    def _list_view_rename(self, path):
        self.rename_selected_image()

    # ==================== ANSICHT UMSCHALTEN ====================
    def switch_view(self, index):
        if index == 1:
            self.gallery_widget.update_directory(self.image_loader.image_directory)
        elif index == 3:
            self.list_view_widget.update_directory(self.image_loader.image_directory)
        self.stacked_widget.setCurrentIndex(index)
        self.update_toolbar_buttons()
        self.update_menu_items()

    def toggle_list_view(self):
        self.switch_view(3)

    def update_toolbar_buttons(self):
        current = self.stacked_widget.currentIndex()
        in_gallery = current == 1
        in_list = current == 3
        in_gallery_or_list = in_gallery or in_list
        viewer_only = not in_gallery_or_list

        self.viewer_view_btn.setChecked(current == 0)
        self.gallery_btn.setChecked(in_gallery)
        self.list_view_btn.setChecked(in_list)

        always_visible = [
            self.viewer_view_btn, self.gallery_btn, self.list_view_btn,
            self.sort_btn, self.fullscreen_btn, self.search_btn,
            self.copy_btn, self.cut_btn,
            self.save_as_btn, self.rename_btn, self.delete_btn,
        ]
        for btn in always_visible:
            btn.setVisible(True)

        viewer_only_btns = [
            self.slideshow_btn,
            self.zoom_btn, self.zoom_in_btn, self.zoom_out_btn,
            self.zoom_fit_btn, self.zoom_actual_btn,
            self.crop_btn, self.resize_btn,
            self.rotate_btn, self.rotate_left_btn, self.rotate_right_btn,
            self.flip_h_btn, self.flip_v_btn, self.adjust_btn,
            self.prev_btn, self.next_btn,
        ]
        for btn in viewer_only_btns:
            btn.setVisible(viewer_only)

    def undo_last_action(self):
        """Macht die zuletzt hinterlegte Operation rückgängig."""
        self.undo_manager.undo()

    def redo_last_action(self):
        """Wiederholt die zuletzt rückgängig gemachte Operation."""
        self.undo_manager.redo()

    def update_undo_redo_actions(self):
        """Aktiviert/deaktiviert Rückgängig & Wiederholen und passt die Texte an."""
        if hasattr(self, "undo_action"):
            desc = self.undo_manager.peek_undo()
            self.undo_action.setEnabled(self.undo_manager.can_undo())
            self.undo_action.setText(
                f"{tr('Rückgängig')}: {tr(desc)} (Strg+Z)" if desc else tr("Rückgängig (Strg+Z)"))
        if hasattr(self, "redo_action"):
            desc = self.undo_manager.peek_redo()
            self.redo_action.setEnabled(self.undo_manager.can_redo())
            self.redo_action.setText(
                f"{tr('Wiederholen')}: {tr(desc)} (Strg+Y)" if desc else tr("Wiederholen (Strg+Y)"))

    def populate_recent_menu(self):
        """Baut das Untermenü 'Zuletzt verwendet' bei jedem Öffnen neu auf."""
        from config import get_recent_directories
        menu = self.recent_menu
        menu.clear()
        recents = get_recent_directories()
        if not recents:
            act = menu.addAction(tr("(keine)"))
            act.setEnabled(False)
            return
        home = os.path.expanduser("~")
        for d in recents:
            label = ("~" + d[len(home):]) if d.startswith(home) else d
            act = menu.addAction(label)
            act.setToolTip(d)
            if not os.path.isdir(d):
                act.setEnabled(False)  # Ordner existiert nicht mehr
            act.triggered.connect(lambda checked=False, path=d: self.image_loader.change_directory(path))
        menu.addSeparator()
        clear_act = menu.addAction(tr("Liste leeren"))
        clear_act.triggered.connect(self._clear_recent_directories)

    def _clear_recent_directories(self):
        from config import clear_recent_directories
        clear_recent_directories()
        self.statusBar.showMessage(tr("Liste der zuletzt verwendeten Ordner geleert"), 3000)

    def open_trash_manager(self):
        """Öffnet die Papierkorb-Verwaltung (ansehen/wiederherstellen/löschen)."""
        from ui.trash_dialog import TrashDialog
        TrashDialog(self).exec()

    def open_batch_processor(self):
        """Öffnet die Stapelverarbeitung für die in Galerie/Liste markierten Bilder."""
        idx = self.stacked_widget.currentIndex()
        if idx == 1:
            paths = self.gallery_widget.get_selected_images()
        elif idx == 3:
            paths = self.list_view_widget.get_selected_images()
        else:
            paths = []
        if not paths:
            QMessageBox.information(
                self, tr("Stapelverarbeitung"),
                tr("Bitte zuerst Bilder in der Galerie- oder Listenansicht markieren."))
            return
        from ui.batch_dialog import BatchDialog
        BatchDialog.run(self, paths)
        # Ansichten aktualisieren (neue Dateien könnten im aktuellen Ordner liegen)
        d = self.image_loader.image_directory
        if d:
            self.image_loader.update_directory(d)
            self.gallery_widget.update_directory(d)
            self.list_view_widget.update_directory(d)

    def _current_selection_paths(self):
        """Markierte Bilder der aktiven Ansicht, sonst das aktuelle Bild."""
        idx = self.stacked_widget.currentIndex()
        if idx == 1:
            return self.gallery_widget.get_selected_images()
        if idx == 3:
            return self.list_view_widget.get_selected_images()
        if self.image_loader.image_paths and self.image_loader.current_index >= 0:
            return [self.image_loader.image_paths[self.image_loader.current_index]]
        return []

    def move_selection_to_folder(self):
        """Verschiebt die Auswahl (oder das aktuelle Bild) in einen Ordner."""
        paths = self._current_selection_paths()
        if not paths:
            QMessageBox.information(self, tr("In Ordner verschieben"),
                                    tr("Bitte zuerst ein oder mehrere Bilder auswählen."))
            return
        self.file_ops.move_to_folder(paths)

    def copy_selection_to_folder(self):
        """Kopiert die Auswahl (oder das aktuelle Bild) in einen Ordner."""
        paths = self._current_selection_paths()
        if not paths:
            QMessageBox.information(self, tr("In Ordner kopieren"),
                                    tr("Bitte zuerst ein oder mehrere Bilder auswählen."))
            return
        self.file_ops.copy_to_folder(paths)

    def empty_trash(self):
        """Leert den Papierkorb endgültig (nach Rückfrage)."""
        from modules.trash import list_trash, empty_trash
        count = len(list_trash())
        if count == 0:
            QMessageBox.information(self, tr("Papierkorb"), tr("Der Papierkorb ist bereits leer."))
            return
        reply = QMessageBox.question(
            self,
            tr("Papierkorb leeren"),
            f"{count} " + tr("Datei(en) endgültig löschen? Dies kann nicht rückgängig gemacht werden."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            removed = empty_trash()
            self.statusBar.showMessage(tr("Papierkorb geleert") + f" ({removed})", 3000)

    def update_menu_items(self):
        current = self.stacked_widget.currentIndex()
        in_gallery_or_list = current in (1, 3)
        viewer_only = not in_gallery_or_list

        always_visible = [
            self.gallery_action, self.list_view_action, self.select_dir_action,
            self.sort_menu.menuAction(), self.delete_action,
            self.exit_action, self.shortcuts_action,
        ]
        for act in always_visible:
            act.setVisible(True)

        viewer_only_actions = [
            self.slideshow_action,
            self.open_action, self.save_as_action, self.rename_action,
            self.zoom_action, self.zoom_in_action, self.zoom_out_action,
            self.zoom_fit_action, self.zoom_actual_action,
            self.crop_action, self.resize_action,
            self.rotate_action, self.rotate_left_action, self.rotate_right_action,
            self.flip_h_action, self.flip_v_action,
            self.adjust_action, self.exif_action,
        ]
        for act in viewer_only_actions:
            act.setVisible(viewer_only)


def main():
    app = QApplication(sys.argv)
    viewer = ImageViewerApp()
    viewer.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()