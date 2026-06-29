from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QApplication
import math


class ZoomHandler:
    def __init__(self, parent):
        self.parent = parent
        self._zoom_mode = False
        self._drag_start = QPoint()
        self._drag_start_offset = QPoint()

    def _sync_zoom_button(self):
        """Hält Toolbar-Button und Menü-Eintrag mit dem Zoom-Modus synchron."""
        if hasattr(self.parent, 'zoom_btn'):
            self.parent.zoom_btn.setChecked(self._zoom_mode)
        if hasattr(self.parent, 'zoom_action'):
            self.parent.zoom_action.setChecked(self._zoom_mode)

    def _enter_zoom_mode_at_fit(self):
        """Aktiviert den Zoom-Modus und startet beim aktuellen Fit-Faktor."""
        if not self._zoom_mode:
            fit = self.parent.calculate_fit_to_window_zoom()
            self.parent.zoom_factor = fit if fit > 0 else 1.0
            self._zoom_mode = True
            self.parent.setCursor(Qt.CursorShape.OpenHandCursor)
            self._sync_zoom_button()

    def _set_zoom_centered(self, old, new):
        """Setzt einen neuen Zoom-Faktor, zentriert auf die Viewer-Mitte."""
        il = self.parent.image_loader
        vw = self.parent.image_viewer.width()
        vh = self.parent.image_viewer.height()
        cx, cy = vw / 2, vh / 2
        ox, oy = self.parent._zoom_offset.x(), self.parent._zoom_offset.y()
        zd = new / old if old else 1.0
        new_ox = cx - (-ox + cx) * zd
        new_oy = cy - (-oy + cy) * zd
        new_w = int(il._original_pixmap.width() * new)
        new_h = int(il._original_pixmap.height() * new)
        new_ox = max(-max(0, new_w - vw), min(0, new_ox))
        new_oy = max(-max(0, new_h - vh), min(0, new_oy))
        self.parent.zoom_factor = new
        self.parent._zoom_offset = QPoint(int(new_ox), int(new_oy))
        self.parent._display_pixmap()
        self.parent.statusBar.showMessage(f"Zoom: {int(new * 100)}%", 2000)

    def _relative_zoom(self, factor):
        il = self.parent.image_loader
        if not il._original_pixmap or il._original_pixmap.isNull():
            return
        self._enter_zoom_mode_at_fit()
        old = self.parent.zoom_factor
        new = max(0.1, min(old * factor, 10.0))
        self._set_zoom_centered(old, new)

    def zoom_in(self):
        self._relative_zoom(1.25)

    def zoom_out(self):
        self._relative_zoom(1 / 1.25)

    def zoom_actual(self):
        """Zeigt das Bild in Originalgröße (100 %)."""
        il = self.parent.image_loader
        if not il._original_pixmap or il._original_pixmap.isNull():
            return
        self._zoom_mode = True
        self.parent.setCursor(Qt.CursorShape.OpenHandCursor)
        self._sync_zoom_button()
        self.parent.zoom_factor = 1.0
        self.parent._zoom_offset = QPoint(0, 0)
        self.parent._display_pixmap()
        self.parent.statusBar.showMessage("Zoom: 100 % (Originalgröße)", 2000)

    def zoom_to_fit(self):
        """Passt das Bild wieder an das Fenster an (Zoom-Modus aus)."""
        if self._zoom_mode:
            self._zoom_mode = False
            self.parent.setCursor(Qt.CursorShape.ArrowCursor)
            self._sync_zoom_button()
        self.parent.zoom_factor = 1.0
        self.parent._zoom_offset = QPoint(0, 0)
        self.parent._display_pixmap()
        self.parent.statusBar.showMessage("An Fenster angepasst", 2000)

    def toggle_zoom_mode(self):
        self._zoom_mode = not self._zoom_mode
        self._sync_zoom_button()
        if self._zoom_mode:
            self.parent.statusBar.showMessage("Zoom-Modus aktiviert - Mausrad zum Zoomen, ziehen zum Verschieben", 3000)
            self.parent.setCursor(Qt.CursorShape.OpenHandCursor)
            # Setze Zoom-Faktor auf aktuellen Fit-Wert, falls noch nicht gezoomt
            if self.parent.zoom_factor == 1.0:
                fit = self.parent.calculate_fit_to_window_zoom()
                if fit > 0:
                    self.parent.zoom_factor = fit
            self.parent._display_pixmap()
        else:
            self.parent.statusBar.showMessage("Zoom-Modus deaktiviert", 2000)
            self.parent.setCursor(Qt.CursorShape.ArrowCursor)
            self.parent.zoom_factor = 1.0
            self.parent._zoom_offset = QPoint(0, 0)
            self.parent._display_pixmap()
            self.parent.update_image_info(
                self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
                if self.parent.image_loader.image_paths else None
            )

    def wheel_event(self, event):
        if not self._zoom_mode:
            return
        if not self.parent.image_loader._original_pixmap or self.parent.image_loader._original_pixmap.isNull():
            return

        # Mausposition im Viewer (relativ zur Bildmitte)
        # Wir verwenden die globale Mausposition, um den Zoom-Punkt zu bestimmen
        mouse_pos = event.globalPosition().toPoint()
        viewer_rect = self.parent.image_viewer.geometry()
        # Umrechnung in Viewer-Koordinaten
        local_pos = self.parent.image_viewer.mapFromGlobal(mouse_pos)
        # Zentrum des Viewers
        center_x = self.parent.image_viewer.width() / 2
        center_y = self.parent.image_viewer.height() / 2

        # Mausposition relativ zum Zentrum (in Pixel, -1..1)
        rel_x = (local_pos.x() - center_x) / (self.parent.image_viewer.width() / 2) if self.parent.image_viewer.width() > 0 else 0
        rel_y = (local_pos.y() - center_y) / (self.parent.image_viewer.height() / 2) if self.parent.image_viewer.height() > 0 else 0

        delta = event.angleDelta().y()
        old_zoom = self.parent.zoom_factor
        if delta > 0:
            new_zoom = old_zoom * 1.1
        else:
            new_zoom = old_zoom / 1.1
        new_zoom = max(0.1, min(new_zoom, 10.0))

        # Änderung des Zoom-Faktors
        zoom_delta = new_zoom / old_zoom

        # Offset anpassen, damit der Punkt unter der Maus fix bleibt
        # Der Offset ist in Pixeln im skalierten Raum (Bildkoordinaten)
        # Wir müssen den Offset so verschieben, dass der Punkt unter der Maus gleich bleibt
        # Dazu berechnen wir den aktuellen sichtbaren Ausschnitt (in Bildkoordinaten)
        orig_w = self.parent.image_loader._original_pixmap.width()
        orig_h = self.parent.image_loader._original_pixmap.height()

        # Aktuelle Zoom-Größe
        zoom_w = int(orig_w * old_zoom)
        zoom_h = int(orig_h * old_zoom)

        # Viewer-Größe
        vw = self.parent.image_viewer.width()
        vh = self.parent.image_viewer.height()

        # Aktueller Offset (negativ, weil wir von der Mitte aus verschieben)
        ox = self.parent._zoom_offset.x()
        oy = self.parent._zoom_offset.y()

        # Die Position unter der Maus in Bildkoordinaten (im aktuell sichtbaren Bereich)
        # Dazu: Mausposition im Viewer (0..vw, 0..vh) in Bildkoordinaten umrechnen
        # Der sichtbare Bereich beginnt bei ( -ox, -oy ) im skalierten Bild
        # Die Mausposition im Bild: ( -ox + mouse_x, -oy + mouse_y )
        # wobei mouse_x und mouse_y die lokale Position im Viewer sind
        mouse_x = local_pos.x()
        mouse_y = local_pos.y()

        # Bildkoordinaten des Mauszeigers (im aktuell sichtbaren Bereich)
        img_x = -ox + mouse_x
        img_y = -oy + mouse_y

        # Nach dem Zoomen ändert sich die Zoom-Größe
        new_zoom_w = int(orig_w * new_zoom)
        new_zoom_h = int(orig_h * new_zoom)

        # Wir wollen, dass der Bildpunkt (img_x, img_y) nach dem Zoomen wieder unter der Maus liegt
        # Neuer Offset so wählen, dass (img_x, img_y) an der gleichen Viewer-Position erscheint
        # Dazu muss gelten: -new_ox + mouse_x = img_x   =>   new_ox = mouse_x - img_x
        # Aber img_x ist im alten Koordinatensystem, wir müssen es in das neue skalieren
        # Da der Zoom-Faktor sich ändert, verschiebt sich der Punkt (img_x, img_y) im skalierten Bild.
        # Im neuen Zoom-Bild hat der Punkt die Koordinaten (img_x * zoom_delta, img_y * zoom_delta)
        new_img_x = img_x * zoom_delta
        new_img_y = img_y * zoom_delta

        # Neuer Offset, damit der Punkt unter der Maus bleibt:
        new_ox = mouse_x - new_img_x
        new_oy = mouse_y - new_img_y

        # Begrenzung (damit kein leerer Rand entsteht)
        max_offset_x = max(0, new_zoom_w - vw)
        max_offset_y = max(0, new_zoom_h - vh)
        new_ox = max(-max_offset_x, min(0, new_ox))
        new_oy = max(-max_offset_y, min(0, new_oy))

        # Anwenden
        self.parent.zoom_factor = new_zoom
        self.parent._zoom_offset = QPoint(int(new_ox), int(new_oy))
        self.parent._display_pixmap()
        self.parent.update_image_info(
            self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
            if self.parent.image_loader.image_paths else None
        )
        self.parent.statusBar.showMessage(f"Zoom: {int(self.parent.zoom_factor * 100)}%", 2000)

    def mouse_press_event(self, event):
        if self._zoom_mode and event.button() == Qt.MouseButton.LeftButton:
            self._drag_start = event.globalPosition().toPoint()
            self._drag_start_offset = self.parent._zoom_offset
            self.parent.setCursor(Qt.CursorShape.ClosedHandCursor)
            return True
        return False

    def mouse_move_event(self, event):
        if self._zoom_mode and event.buttons() & Qt.MouseButton.LeftButton:
            if not self._drag_start.isNull():
                delta = event.globalPosition().toPoint() - self._drag_start
                new_ox = self._drag_start_offset.x() + delta.x()
                new_oy = self._drag_start_offset.y() + delta.y()

                # Begrenzung
                orig_w = self.parent.image_loader._original_pixmap.width() if self.parent.image_loader._original_pixmap else 0
                orig_h = self.parent.image_loader._original_pixmap.height() if self.parent.image_loader._original_pixmap else 0
                zoom_w = int(orig_w * self.parent.zoom_factor)
                zoom_h = int(orig_h * self.parent.zoom_factor)
                vw = self.parent.image_viewer.width()
                vh = self.parent.image_viewer.height()
                max_offset_x = max(0, zoom_w - vw)
                max_offset_y = max(0, zoom_h - vh)
                new_ox = max(-max_offset_x, min(0, new_ox))
                new_oy = max(-max_offset_y, min(0, new_oy))

                self.parent._zoom_offset = QPoint(int(new_ox), int(new_oy))
                self.parent._display_pixmap()
                self.parent.setCursor(Qt.CursorShape.ClosedHandCursor)
                return True
        return False

    def mouse_release_event(self, event):
        if self._zoom_mode and event.button() == Qt.MouseButton.LeftButton:
            self.parent.setCursor(Qt.CursorShape.OpenHandCursor)
            self._drag_start = QPoint()
            return True
        return False

    def _display_zoomed_pixmap(self):
        # Diese Methode wird nicht benötigt, da viewer._display_zoomed_pixmap den Zoom-Handler nicht aufruft.
        # Sie bleibt als Platzhalter.
        pass