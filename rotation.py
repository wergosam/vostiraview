from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton,
                             QLabel, QSpinBox, QDialogButtonBox,
                             QComboBox, QFormLayout, QRadioButton,
                             QButtonGroup, QGroupBox, QHBoxLayout)
from PyQt6.QtGui import QPixmap, QTransform
from PyQt6.QtCore import Qt
from i18n import tr


class RotationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Bild drehen"))
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout()

        # Modus-Auswahl per RadioButtons
        mode_group = QGroupBox(tr("Modus"))
        mode_layout = QHBoxLayout()
        self.radio_fixed = QRadioButton(tr("Fester Winkel"))
        self.radio_custom = QRadioButton(tr("Benutzerdefiniert"))
        self.radio_fixed.setChecked(True)
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.radio_fixed)
        self.button_group.addButton(self.radio_custom)
        mode_layout.addWidget(self.radio_fixed)
        mode_layout.addWidget(self.radio_custom)
        mode_group.setLayout(mode_layout)
        layout.addRow(mode_group)

        # Feste Winkel-Auswahl
        self.fixed_angles = QComboBox()
        self.fixed_angles.addItems(["90°", "180°", "270°"])
        layout.addRow(tr("Fester Winkel:"), self.fixed_angles)

        # Benutzerdefinierter Winkel
        self.custom_angle = QSpinBox()
        self.custom_angle.setRange(-360, 360)
        self.custom_angle.setSingleStep(1)
        self.custom_angle.setValue(0)
        self.custom_angle.setEnabled(False)
        layout.addRow(tr("Benutzerdefinierter Winkel:"), self.custom_angle)

        # OK/Abbrechen Buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addRow(self.button_box)

        self.setLayout(layout)

        # Signale verbinden
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.radio_fixed.toggled.connect(self._toggle_input_fields)

    def _toggle_input_fields(self):
        """Aktiviert/deaktiviert Eingabefelder je nach gewähltem Modus."""
        is_custom = self.radio_custom.isChecked()
        self.fixed_angles.setEnabled(not is_custom)
        self.custom_angle.setEnabled(is_custom)

    def get_rotation_angle(self):
        """Gibt den gewählten Rotationswinkel zurück."""
        if self.radio_fixed.isChecked():
            return int(self.fixed_angles.currentText().replace("°", ""))
        return self.custom_angle.value()


def rotate_image(pixmap, angle):
    """Dreht ein QPixmap um den angegebenen Winkel."""
    if not pixmap or pixmap.isNull():
        return None
    transform = QTransform().rotate(angle)
    rotated = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
    return rotated


def show_rotation_dialog(parent, image_path):
    """Zeigt den Rotationsdialog an und führt die Drehung durch."""
    dialog = RotationDialog(parent)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        angle = dialog.get_rotation_angle()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            rotated_pixmap = rotate_image(pixmap, angle)
            return rotated_pixmap, angle

    return None, None
