import os
from PIL import Image
from PyQt6.QtWidgets import (QFileDialog, QMessageBox, QDialog, QFormLayout,
                             QLineEdit, QCheckBox, QDialogButtonBox, QLabel)
from PyQt6.QtCore import Qt
from i18n import tr

from modules.image_export import (build_filter_string, format_for_extension,
                                  ensure_extension, save_pil_image)


def resize_current_image(parent, image_path, output_path=None):
    """Öffnet einen Dialog zur Bildgrößenänderung und ruft resize_image() auf.

    Ist output_path gesetzt, wird ohne Speichern-Dialog direkt dorthin
    geschrieben (Überschreiben-Modus)."""

    img = Image.open(image_path)
    original_width, original_height = img.size

    dialog = QDialog(parent)
    dialog.setWindowTitle(tr("Bildgröße ändern"))
    layout = QFormLayout()

    width_input = QLineEdit()
    height_input = QLineEdit()
    percent_input = QLineEdit()
    keep_ratio_checkbox = QCheckBox(tr("Proportionen beibehalten"))
    keep_ratio_checkbox.setChecked(True)

    layout.addRow(tr("Breite (Pixel):"), width_input)
    layout.addRow(tr("Höhe (Pixel):"), height_input)
    hint_label = QLabel(tr("Wenn Skalierung (%) angegeben, werden Pixel-Werte ignoriert."))
    hint_label.setStyleSheet("color: gray; font-size: 10px;")
    layout.addRow(tr("Skalierung (%):"), percent_input)
    layout.addRow(hint_label)
    layout.addRow(keep_ratio_checkbox)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addRow(buttons)
    dialog.setLayout(layout)

    # Endlosschleifen verhindern
    width_updating = False
    height_updating = False

    def adjust_height():
        nonlocal width_updating
        if (keep_ratio_checkbox.isChecked()
                and not width_updating
                and width_input.text().isdigit()):
            width_updating = True
            new_width = int(width_input.text())
            new_height = round((new_width / original_width) * original_height)
            height_input.setText(str(new_height))
            width_updating = False

    def adjust_width():
        nonlocal height_updating
        if (keep_ratio_checkbox.isChecked()
                and not height_updating
                and height_input.text().isdigit()):
            height_updating = True
            new_height = int(height_input.text())
            new_width = round((new_height / original_height) * original_width)
            width_input.setText(str(new_width))
            height_updating = False

    width_input.textChanged.connect(adjust_height)
    height_input.textChanged.connect(adjust_width)

    # Standardwerte setzen
    width_input.setText(str(original_width))
    height_input.setText(str(original_height))

    if dialog.exec() == QDialog.DialogCode.Accepted:
        try:
            percent_text = percent_input.text().strip()
            width_text = width_input.text().strip()
            height_text = height_input.text().strip()

            # Prozent hat Vorrang vor Pixel-Werten
            if percent_text and percent_text.isdigit():
                percent = int(percent_text)
                width = None
                height = None
            else:
                percent = None
                width = int(width_text) if width_text.isdigit() else None
                height = int(height_text) if height_text.isdigit() else None

            resized_path = resize_image(
                image_path,
                img=img,
                width=width,
                height=height,
                scale_percent=percent,
                parent=parent,
                output_path=output_path
            )
            return resized_path

        except ValueError:
            QMessageBox.warning(parent, tr('Fehler'), tr('Ungültige Eingabe. Bitte nur Zahlen eingeben.'))

    return None


def resize_image(image_path, width=None, height=None, scale_percent=None, parent=None, output_path=None, img=None):
    """
    Ändert die Größe eines Bildes nach Pixeldimensionen oder in Prozent.

    Args:
        image_path (str): Pfad zur Bilddatei
        width (int, optional): Neue Breite in Pixeln
        height (int, optional): Neue Höhe in Pixeln
        scale_percent (int, optional): Prozentsatz zum Skalieren des Bildes
        parent (QWidget, optional): Übergeordnetes Widget für Dialoge
        img (Image, optional): Bereits geöffnetes PIL-Image (vermeidet doppeltes Laden)

    Rückgabe:
        str: Pfad zum skalierten Bild oder None, wenn abgebrochen
    """
    if img is None:
        img = Image.open(image_path)

    if scale_percent is not None:
        width = int(img.width * scale_percent / 100)
        height = int(img.height * scale_percent / 100)

    width = width or img.width
    height = height or img.height

    resized_img = img.resize((width, height), Image.LANCZOS)

    # Überschreiben-Modus: direkt zum vorgegebenen Pfad speichern
    if output_path:
        save_pil_image(resized_img, output_path,
                       format_for_extension(os.path.splitext(output_path)[1]))
        return output_path

    original_directory = os.path.dirname(image_path)
    original_filename = os.path.splitext(os.path.basename(image_path))[0]

    file_path, selected_filter = QFileDialog.getSaveFileName(
        parent,
        tr('Bild speichern'),
        os.path.join(original_directory, f'{original_filename}_resized'),
        build_filter_string()
    )

    if not file_path:
        return None

    file_path, save_ext = ensure_extension(file_path, selected_filter)
    save_pil_image(resized_img, file_path, format_for_extension(save_ext))
    return file_path
