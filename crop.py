import sys
import os
import shutil  # Für das Kopieren von Dateien
from PyQt6.QtWidgets import (QMainWindow, QApplication, QVBoxLayout, QWidget,
                             QFileDialog, QMessageBox, QToolBar, QLabel, QCheckBox,
                             QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QPushButton, QHBoxLayout, QRubberBand)
from PyQt6.QtGui import QAction, QIcon, QPixmap, QPainter, QPen, QColor, QCursor, QPixmapCache
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from i18n import tr


class ResizeHandle(QLabel):
    def __init__(self, parent=None, cursor=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.start_point = None
        self.end_point = None
        self.crop_rect = None
        self.is_cropping = False
        self.is_resizing = False
        self.resize_mode = None
        self.setFixedSize(10, 10)
        self.setStyleSheet("background-color: blue; border: 1px solid white;")
        self.setCursor(cursor)
        self.is_dragging = False
        self.offset = QPoint()

class CroppableImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.start_point = None
        self.end_point = None
        self.crop_rect = None
        self.is_cropping = False
        self.is_resizing = False
        self.resize_mode = None

        self.handles = {
            'top_left': ResizeHandle(self, QCursor(Qt.CursorShape.SizeFDiagCursor)),
            'top_right': ResizeHandle(self, QCursor(Qt.CursorShape.SizeBDiagCursor)),
            'bottom_left': ResizeHandle(self, QCursor(Qt.CursorShape.SizeBDiagCursor)),
            'bottom_right': ResizeHandle(self, QCursor(Qt.CursorShape.SizeFDiagCursor)),
            'top': ResizeHandle(self, QCursor(Qt.CursorShape.SizeVerCursor)),
            'bottom': ResizeHandle(self, QCursor(Qt.CursorShape.SizeVerCursor)),
            'left': ResizeHandle(self, QCursor(Qt.CursorShape.SizeHorCursor)),
            'right': ResizeHandle(self, QCursor(Qt.CursorShape.SizeHorCursor))
        }

        for handle in self.handles.values():
            handle.hide()

    def update_handles(self):
        if not self.crop_rect:
            for handle in self.handles.values():
                handle.hide()
            return

        # Top handles
        self.handles['top_left'].move(self.crop_rect.x() - 5, self.crop_rect.y() - 5)
        self.handles['top_right'].move(self.crop_rect.x() + self.crop_rect.width() - 5, self.crop_rect.y() - 5)
        self.handles['top'].move(self.crop_rect.x() + self.crop_rect.width() // 2 - 5, self.crop_rect.y() - 5)

        # Bottom handles
        self.handles['bottom_left'].move(self.crop_rect.x() - 5, self.crop_rect.y() + self.crop_rect.height() - 5)
        self.handles['bottom_right'].move(self.crop_rect.x() + self.crop_rect.width() - 5, self.crop_rect.y() + self.crop_rect.height() - 5)
        self.handles['bottom'].move(self.crop_rect.x() + self.crop_rect.width() // 2 - 5, self.crop_rect.y() + self.crop_rect.height() - 5)

        # Side handles
        self.handles['left'].move(self.crop_rect.x() - 5, self.crop_rect.y() + self.crop_rect.height() // 2 - 5)
        self.handles['right'].move(self.crop_rect.x() + self.crop_rect.width() - 5, self.crop_rect.y() + self.crop_rect.height() // 2 - 5)

        for handle in self.handles.values():
            handle.show()

    def mousePressEvent(self, event):
        # Check if any handle is clicked
        for name, handle in self.handles.items():
            if handle.geometry().contains(event.pos()):
                self.is_resizing = True
                self.resize_mode = name
                handle.is_dragging = True
                handle.offset = event.pos() - handle.pos()
                return

        if not self.is_cropping:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        # Wenn Handles zum Ändern der Größe verwendet werden
        if self.is_resizing and self.crop_rect:
            pos = event.pos()

            # Definiere Anpassungslogik für jeden Handle
            if self.resize_mode == 'top_left':
                self.crop_rect.setTopLeft(pos)
            elif self.resize_mode == 'top_right':
                self.crop_rect.setTopRight(pos)
            elif self.resize_mode == 'bottom_left':
                self.crop_rect.setBottomLeft(pos)
            elif self.resize_mode == 'bottom_right':
                self.crop_rect.setBottomRight(pos)
            elif self.resize_mode == 'top':
                self.crop_rect.setTop(pos.y())
            elif self.resize_mode == 'bottom':
                self.crop_rect.setBottom(pos.y())
            elif self.resize_mode == 'left':
                self.crop_rect.setLeft(pos.x())
            elif self.resize_mode == 'right':
                self.crop_rect.setRight(pos.x())

            self.update_handles()
            self.update()
            return

        # Wenn kein Cropping-Modus aktiv oder kein Startpunkt gesetzt ist, abbrechen
        if not self.is_cropping or not self.start_point:
            return

        # Aktualisiere den Endpunkt während des Ziehens
        self.end_point = event.pos()

        # Trigger ein Neuzeichnen der Oberfläche
        self.update()

    def mouseReleaseEvent(self, event):
        # Reset resize mode
        if self.is_resizing:
            for handle in self.handles.values():
                handle.is_dragging = False
            self.is_resizing = False
            self.resize_mode = None
            return

        if not self.is_cropping:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            self.end_point = event.pos()
            self.crop_rect = self.create_crop_rect()
            self.update_handles()
            self.is_cropping = False
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def paintEvent(self, event):
        super().paintEvent(event)

        # Zeichne das bestehende Crop-Rechteck
        if self.crop_rect:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.SolidLine))
            painter.drawRect(self.crop_rect)

        # Zeichne das temporäre Auswahlrechteck während des Ziehens
        if self.is_cropping and self.start_point and self.end_point:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(0, 120, 215), 2, Qt.PenStyle.DashLine))  # Gestrichelte Linie
            selection_rect = self.create_crop_rect()
            painter.drawRect(selection_rect)

    def create_crop_rect(self):
        if not self.start_point or not self.end_point:
            return None
        x1, y1 = self.start_point.x(), self.start_point.y()
        x2, y2 = self.end_point.x(), self.end_point.y()
        return QRect(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))

class ImageCropperApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.original_pixmap = None
        self.cropped_pixmap = None

    def initUI(self):
        self.setGeometry(100, 100, 800, 600)
        central_widget = QWidget()
        layout = QVBoxLayout()

        # Horizontales Layout für die Buttons
        button_layout = QHBoxLayout()

        # Buttons erstellen
        load_btn = QPushButton(tr('Bild laden'))
        crop_btn = QPushButton(tr('Zuschneiden aktivieren'))
        crop_save_btn = QPushButton(tr('Zuschneiden'))
        cancel_btn = QPushButton(tr('Abbrechen'))
        save_btn = QPushButton(tr('Bild speichern'))

        # Button-Breiten setzen
        button_width = 120  # Breite in Pixeln
        for btn in [load_btn, crop_btn, crop_save_btn, cancel_btn, save_btn]:
            btn.setFixedWidth(button_width)  # Feste Breite setzen

        # Buttons mit Funktionen verbinden
        load_btn.clicked.connect(self.load_image)
        crop_btn.clicked.connect(self.toggle_crop_mode)
        crop_save_btn.clicked.connect(self.crop_image)
        cancel_btn.clicked.connect(self.cancel_crop)
        save_btn.clicked.connect(self.save_cropped_image)

        # Buttons dem Layout hinzufügen
        button_layout.addWidget(load_btn)
        button_layout.addWidget(crop_btn)
        button_layout.addWidget(crop_save_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)

        # Layouts hinzufügen
        layout.addLayout(button_layout)

        # Bild-Label
        self.image_label = CroppableImageLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Bild auswählen',
            '',
            'Bilder (*.png *.jpg *.jpeg *.bmp)'
        )
        if file_path:
            # Den vollständigen Pfad als Klassenattribut speichern
            self.last_file_path = file_path
            self.original_pixmap = QPixmap(file_path)
            self.display_image(self.original_pixmap)

    def save_cropped_image(self):
        if not self.image_label.pixmap():
            QMessageBox.warning(self, tr('Fehler'), tr('Kein Bild zum Speichern'))
            return

        # Überprüfe, ob ein Dateipfad existiert
        directory = os.path.dirname(self.last_file_path) if hasattr(self, 'last_file_path') else os.getcwd()
        filename = os.path.basename(self.last_file_path) if hasattr(self, 'last_file_path') else "cropped_image.jpg"
        name, ext = os.path.splitext(filename)
        default_path = os.path.join(directory, f"{name}_cropped{ext}")

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Bild speichern',
            default_path,
            'JPEG-Dateien (*.jpg *.jpeg);;PNG-Dateien (*.png)'
        )

        if file_path:
            try:
                self.image_label.pixmap().save(file_path)
                QMessageBox.information(self, tr('Erfolg'), tr('Bild wurde erfolgreich gespeichert.'))
            except Exception as e:
                QMessageBox.critical(self, tr('Fehler'), tr('Fehler beim Speichern:') + f' {e}')

    def save_image(self):
        if not self.image_label.pixmap():
            QMessageBox.warning(self, tr('Fehler'), tr('Kein Bild zum Speichern'))
            return

        file_path, _ = QFileDialog.getSaveFileName(self, tr('Bild speichern'), '', 'JPEG-Dateien (*.jpg *.jpeg);;PNG-Dateien (*.png)')
        if file_path:
            self.image_label.pixmap().save(file_path)

    def load_image_from_path(self, file_path):
        if file_path:
            self.original_pixmap = QPixmap(file_path)  # Speichere das Original
            self.display_image(self.original_pixmap)
            self.activate_crop_mode()

    def display_image(self, pixmap):
        scaled_pixmap = pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)

    def cancel_crop(self):
        self.image_label.is_cropping = False
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.reset_crop_state()  # Setzt Crop-Status und Handles zurück
        if self.parent_window:
            self.parent_window.exit_crop_mode()

class ImageCropperWidget(QWidget):
    cropped_image_signal = pyqtSignal(QPixmap)

    def __init__(self, parent=None):  # Parent hinzufügen
        super().__init__(parent)
        self.parent_window = parent  # Speichert den Parent
        self.initUI()
        self.original_pixmap = None
        self.cropped_pixmap = None

    def initUI(self):
        layout = QVBoxLayout()

        # Button-Layout
        button_layout = QHBoxLayout()

        # Zuschneiden-Button
        save_btn = QPushButton(tr('Zuschneiden'))
        save_btn.clicked.connect(self.crop_image)
        button_layout.addWidget(save_btn)

        # **Abbrechen-Button hinzufügen**
        cancel_btn = QPushButton(tr('Abbrechen'))
        cancel_btn.clicked.connect(self.cancel_crop)  # Mit der Abbrechen-Funktion verbinden
        button_layout.addWidget(cancel_btn)

        # Button-Layout zum Hauptlayout hinzufügen
        layout.addLayout(button_layout)

        # Bild-Label
        self.image_label = CroppableImageLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

    def cancel_crop(self):
        self.image_label.is_cropping = False
        self.image_label.crop_rect = None
        self.image_label.start_point = None
        self.image_label.end_point = None
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)
        self.image_label.update()
        if self.parent_window:
            self.parent_window.exit_crop_mode()

    def load_image_from_path(self, file_path):
        if file_path and os.path.exists(file_path):
            self.original_pixmap = QPixmap(file_path)
            self.display_image(self.original_pixmap)
            # Aktiviere automatisch den Zuschneidemodus
            self.activate_crop_mode()

    def display_image(self, pixmap):
        # Definiere die feste Zielgröße
        target_width = 1280
        target_height = 800

        # Skaliere das Pixmap unter Beibehaltung des Seitenverhältnisses
        scaled_pixmap = pixmap.scaled(
            target_width,
            target_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Erstelle ein neues Pixmap in der Zielgröße mit weißem Hintergrund
        final_pixmap = QPixmap(target_width, target_height)
        final_pixmap.fill(Qt.GlobalColor.white)  # Weißer Hintergrund

        # Berechne die Position zum Zentrieren des skalierten Bildes
        x = (target_width - scaled_pixmap.width()) // 2
        y = (target_height - scaled_pixmap.height()) // 2

        # Erstelle einen Painter, um das skalierte Bild auf dem neuen Pixmap zu zeichnen
        painter = QPainter(final_pixmap)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        # Setze das finale Pixmap im Label
        self.image_label.setPixmap(final_pixmap)

    def activate_crop_mode(self):
        """Neue Funktion zum direkten Aktivieren des Crop-Modus"""
        self.image_label.is_cropping = True
        self.image_label.setCursor(Qt.CursorShape.CrossCursor)
        self.image_label.crop_rect = None

    def reset_crop_state(self):
        """Setzt den Crop-Modus vollständig zurück und blendet alle Handles aus."""
        self.image_label.crop_rect = None
        self.image_label.start_point = None
        self.image_label.end_point = None
        self.image_label.is_cropping = False
        self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

        # Alle Handle-Widgets explizit ausblenden
        for handle in self.image_label.handles.values():
            handle.hide()

        self.image_label.update()

    def crop_image(self):
        if not self.image_label.crop_rect:
            QMessageBox.warning(self, tr('Fehler'), tr('Kein Auswahlbereich'))
            return

        displayed_pixmap = self.image_label.pixmap()
        if not self.original_pixmap:
            QMessageBox.warning(self, tr('Fehler'), tr('Kein Originalbild gefunden'))
            return

        # Get the dimensions
        target_width = 1280
        target_height = 800

        # Calculate the scaling of the displayed image
        display_scale = min(target_width / self.original_pixmap.width(),
                        target_height / self.original_pixmap.height())

        # Calculate the actual dimensions of the displayed image
        displayed_width = int(self.original_pixmap.width() * display_scale)
        displayed_height = int(self.original_pixmap.height() * display_scale)

        # Calculate the offset of the centered image
        x_offset = (target_width - displayed_width) // 2
        y_offset = (target_height - displayed_height) // 2

        # Adjust the crop coordinates by subtracting the offset and scaling back to original size
        original_x = int((self.image_label.crop_rect.x() - x_offset) / display_scale)
        original_y = int((self.image_label.crop_rect.y() - y_offset) / display_scale)
        original_width = int(self.image_label.crop_rect.width() / display_scale)
        original_height = int(self.image_label.crop_rect.height() / display_scale)

        # Ensure coordinates are within bounds
        original_x = max(0, min(original_x, self.original_pixmap.width()))
        original_y = max(0, min(original_y, self.original_pixmap.height()))
        original_width = min(original_width, self.original_pixmap.width() - original_x)
        original_height = min(original_height, self.original_pixmap.height() - original_y)

        # Create the scaled crop rectangle
        scaled_crop_rect = QRect(
            original_x,
            original_y,
            original_width,
            original_height
        )

        # Create the cropped pixmap
        cropped_pixmap = self.original_pixmap.copy(scaled_crop_rect)

        # Emit the signal with the cropped image
        self.cropped_image_signal.emit(cropped_pixmap)

        # Reset the crop state
        self.image_label.crop_rect = None
        self.image_label.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ImageCropperApp()
    window.show()
    sys.exit(app.exec())