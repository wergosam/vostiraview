from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QPixmap
from exif_dialog import ExifDialog
from i18n import tr
import os
from PIL import Image, ExifTags


class ExifHandler:
    """Verwaltet EXIF-Daten-Funktionen."""

    def __init__(self, parent):
        self.parent = parent

    def show_exif_data(self):
        """Zeigt die EXIF-Daten des aktuellen Bildes an."""
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild ausgewählt.'))
            return

        current_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        if not os.path.exists(current_path):
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Bild nicht gefunden.'))
            return

        dialog = ExifDialog(current_path, self.parent)
        dialog.exec()

    def get_exif_summary(self, image_path):
        """
        Extrahiert eine kurze Zusammenfassung der wichtigsten EXIF-Daten.

        Args:
            image_path: Pfad zum Bild

        Returns:
            dict: Wichtige EXIF-Daten oder None
        """
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()

            if not exif_data:
                return None

            # Wichtige EXIF-Tags
            important_tags = {
                0x010f: 'Hersteller',      # Make
                0x0110: 'Modell',          # Model
                0x829a: 'Belichtungszeit', # ExposureTime
                0x829d: 'Blende',          # FNumber
                0x8827: 'ISO',             # ISOSpeedRatings
                0x9003: 'Aufnahmedatum',   # DateTimeOriginal
                0x920a: 'Brennweite',      # FocalLength
                0x9209: 'Blitz',           # Flash
                0xa402: 'Belichtungsmodus' # ExposureMode
            }

            result = {}
            for tag_id, tag_name in important_tags.items():
                if tag_id in exif_data:
                    value = exif_data[tag_id]
                    # Formatierung für bestimmte Werte
                    if tag_id == 0x829a:  # Belichtungszeit
                        # Versuche, den Wert als Bruch darzustellen
                        if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                            if value.numerator > 0 and value.denominator > 0:
                                if value.numerator < value.denominator:
                                    value = f"1/{int(value.denominator/value.numerator)}s"
                                else:
                                    value = f"{value.numerator/value.denominator:.1f}s"
                            else:
                                value = str(value)
                        elif isinstance(value, tuple) and len(value) == 2:
                            if value[0] > 0 and value[1] > 0:
                                if value[0] < value[1]:
                                    value = f"1/{int(value[1]/value[0])}s"
                                else:
                                    value = f"{value[0]/value[1]:.1f}s"
                            else:
                                value = str(value)
                        else:
                            value = str(value)
                    elif tag_id == 0x829d:  # Blende (FNumber)
                        if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                            value = f"f/{value.numerator/value.denominator:.1f}"
                        elif isinstance(value, tuple) and len(value) == 2:
                            value = f"f/{value[0]/value[1]:.1f}"
                        else:
                            value = str(value)
                    elif tag_id == 0x920a:  # Brennweite
                        if hasattr(value, 'numerator') and hasattr(value, 'denominator'):
                            value = f"{value.numerator/value.denominator:.1f}mm"
                        elif isinstance(value, tuple) and len(value) == 2:
                            value = f"{value[0]/value[1]:.1f}mm"
                        else:
                            value = str(value)
                    elif tag_id == 0x9209:  # Blitz
                        flash_dict = {0: 'Aus', 1: 'Ein', 5: 'Ein (Rote-Augen-Reduktion)', 7: 'Ein (Rote-Augen-Reduktion)'}
                        value = flash_dict.get(value, str(value))
                    elif tag_id == 0xa402:  # Belichtungsmodus
                        exp_dict = {0: 'Auto', 1: 'Manuell', 2: 'Blendenpriorität', 3: 'Zeitpriorität'}
                        value = exp_dict.get(value, str(value))
                    elif tag_id == 0x8827:  # ISO
                        value = str(value)
                    elif tag_id == 0x9003:  # DateTime
                        value = str(value)
                    else:
                        # Für alle anderen Werte sicherstellen, dass sie Strings sind
                        value = str(value)

                    result[tag_name] = value

            return result

        except Exception as e:
            return None

    def get_exif_string(self, image_path):
        """
        Gibt eine formatierte Zeichenkette mit den wichtigsten EXIF-Daten zurück.

        Args:
            image_path: Pfad zum Bild

        Returns:
            str: Formatierte EXIF-Zusammenfassung
        """
        exif_summary = self.get_exif_summary(image_path)
        if not exif_summary:
            return ""

        parts = []
        if 'Hersteller' in exif_summary and 'Modell' in exif_summary:
            parts.append(f"📷 {exif_summary['Hersteller']} {exif_summary['Modell']}")
        elif 'Hersteller' in exif_summary:
            parts.append(f"📷 {exif_summary['Hersteller']}")
        elif 'Modell' in exif_summary:
            parts.append(f"📷 {exif_summary['Modell']}")

        if 'Aufnahmedatum' in exif_summary:
            parts.append(f"📅 {exif_summary['Aufnahmedatum']}")

        exif_info = []
        if 'Belichtungszeit' in exif_summary:
            exif_info.append(str(exif_summary['Belichtungszeit']))  # in String umwandeln
        if 'Blende' in exif_summary:
            exif_info.append(str(exif_summary['Blende']))
        if 'ISO' in exif_summary:
            exif_info.append(f"ISO {exif_summary['ISO']}")
        if 'Brennweite' in exif_summary:
            exif_info.append(str(exif_summary['Brennweite']))

        if exif_info:
            parts.append(" ".join(exif_info))

        return " | ".join(parts)