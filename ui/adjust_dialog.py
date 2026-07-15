"""Dialog für Bildanpassungen (Helligkeit/Kontrast/Sättigung/Schärfe).

Zeigt eine Live-Vorschau auf einer verkleinerten Kopie. Liefert die gewählten
Verstärkungsfaktoren zurück; die eigentliche Anwendung auf das Originalbild
übernimmt der Aufrufer (siehe ImageOperations.adjust_current_image).
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QSlider, QLabel, QDialogButtonBox, QPushButton)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QImage
from PIL import Image, ImageEnhance
from i18n import tr


def pil_to_qpixmap(img):
    """Wandelt ein PIL-RGB-Bild in eine QPixmap um."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    data = img.tobytes("raw", "RGB")
    qimg = QImage(data, img.width, img.height, img.width * 3, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class AdjustDialog(QDialog):
    # (Schlüssel, Beschriftung)
    CHANNELS = [
        ("brightness", "Helligkeit"),
        ("contrast", "Kontrast"),
        ("color", "Sättigung"),
        ("sharpness", "Schärfe"),
    ]

    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Bild anpassen"))
        self.setMinimumSize(560, 480)

        self._base = Image.open(image_path)
        # Verkleinerte Kopie für die schnelle Live-Vorschau
        self._preview_src = self._base.copy()
        self._preview_src.thumbnail((520, 360))

        layout = QVBoxLayout(self)

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview.setMinimumHeight(300)
        self.preview.setStyleSheet("background:#222; border:1px solid #444;")
        layout.addWidget(self.preview, 1)

        form = QFormLayout()
        self.sliders = {}
        self.value_labels = {}
        for key, label in self.CHANNELS:
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(-100, 100)
            slider.setValue(0)
            slider.valueChanged.connect(self._schedule_preview)
            val = QLabel("0")
            val.setMinimumWidth(32)
            slider.valueChanged.connect(lambda v, lab=val: lab.setText(str(v)))
            row = QHBoxLayout()
            row.addWidget(slider, 1)
            row.addWidget(val)
            form.addRow(tr(label) + ":", row)
            self.sliders[key] = slider
            self.value_labels[key] = val
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        reset_btn = QPushButton(tr("Zurücksetzen"))
        reset_btn.clicked.connect(self.reset)
        buttons.addButton(reset_btn, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Vorschau leicht verzögert neu berechnen (Debounce gegen Slider-Spam)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(60)
        self._timer.timeout.connect(self._render_preview)

        self._render_preview()

    def reset(self):
        for slider in self.sliders.values():
            slider.setValue(0)

    def factors(self):
        """Verstärkungsfaktoren (1.0 = neutral) für ImageEnhance."""
        return {key: 1.0 + self.sliders[key].value() / 100.0 for key, _ in self.CHANNELS}

    @staticmethod
    def apply_factors(img, f):
        """Wendet die Faktoren auf ein PIL-Bild an (Alpha bleibt erhalten)."""
        alpha = None
        if img.mode in ("RGBA", "LA"):
            alpha = img.getchannel("A")
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(f["brightness"])
        img = ImageEnhance.Contrast(img).enhance(f["contrast"])
        img = ImageEnhance.Color(img).enhance(f["color"])
        img = ImageEnhance.Sharpness(img).enhance(f["sharpness"])
        if alpha is not None:
            img = img.convert("RGBA")
            img.putalpha(alpha)
        return img

    def _schedule_preview(self):
        self._timer.start()

    def _render_preview(self):
        img = self.apply_factors(self._preview_src.copy(), self.factors())
        self.preview.setPixmap(pil_to_qpixmap(img))

    @classmethod
    def get_adjustments(cls, parent, image_path):
        """Öffnet den Dialog. Gibt die Faktoren zurück oder None bei Abbruch
        bzw. wenn nichts verändert wurde."""
        dlg = cls(image_path, parent)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return None
        f = dlg.factors()
        if all(abs(v - 1.0) < 1e-6 for v in f.values()):
            return None  # keine Änderung
        return f
