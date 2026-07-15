from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton,
                             QTabWidget, QTextEdit, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices
from PIL import Image, ExifTags
import os
from i18n import tr


def gps_coordinates(image_path):
    """Liest GPS-Koordinaten aus den EXIF-Daten. Gibt (lat, lon) oder None."""
    try:
        exif = Image.open(image_path)._getexif()
        if not exif:
            return None
        gps = exif.get(0x8825)  # GPSInfo
        if not gps:
            return None

        def _num(x):
            try:
                return x[0] / x[1] if isinstance(x, tuple) else float(x)
            except (TypeError, ZeroDivisionError):
                return None

        def _to_deg(val):
            d, m, s = (_num(v) for v in val)
            if None in (d, m, s):
                return None
            return d + m / 60.0 + s / 3600.0

        lat = _to_deg(gps.get(2))
        lon = _to_deg(gps.get(4))
        if lat is None or lon is None:
            return None
        if str(gps.get(1, "")).upper() == "S":
            lat = -lat
        if str(gps.get(3, "")).upper() == "W":
            lon = -lon
        return (lat, lon)
    except Exception:
        return None


class ExifDialog(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("EXIF-Daten"))
        self.setFixedSize(700, 500)

        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #e8e8e8;
                padding: 8px 15px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #4CAF50;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: none;
            }
            QTableWidget::item {
                padding: 5px 10px;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #333333;
            }
            QTextEdit {
                background-color: white;
                border: none;
                font-family: monospace;
                font-size: 11px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 30px;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #2E7D32;
            }
            QLabel {
                color: #333333;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Info-Label mit Dateiname
        info_label = QLabel(f"📷 {os.path.basename(image_path)}")
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #333333; padding: 5px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        # Tabs für verschiedene Ansichten
        tabs = QTabWidget()

        # EXIF-Tabelle
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([tr("Tag"), tr("Wert")])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        tabs.addTab(self.table, tr("📊 EXIF-Daten"))

        # Rohdaten-Ansicht
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        tabs.addTab(self.raw_text, tr("📝 Rohdaten"))

        layout.addWidget(tabs)

        self.image_path = image_path

        # Aktions-Buttons
        btn_row = QHBoxLayout()

        self.remove_btn = QPushButton(tr("🧹 Metadaten entfernen…"))
        self.remove_btn.setToolTip(tr("Speichert das Bild ohne EXIF-/Metadaten (Datenschutz)."))
        self.remove_btn.clicked.connect(self._remove_metadata)
        btn_row.addWidget(self.remove_btn)

        coords = gps_coordinates(image_path)
        if coords:
            self._coords = coords
            map_btn = QPushButton(tr("🗺 Auf Karte anzeigen"))
            map_btn.setToolTip(f"{coords[0]:.6f}, {coords[1]:.6f} " + tr("– in OpenStreetMap öffnen"))
            map_btn.clicked.connect(self._open_map)
            btn_row.addWidget(map_btn)

        btn_row.addStretch(1)

        close_btn = QPushButton(tr("Schließen"))
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(120)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        self.setLayout(layout)
        self.load_exif_data(image_path)

    def _open_map(self):
        lat, lon = self._coords
        url = f"https://www.openstreetmap.org/?mlat={lat}&mlon={lon}#map=15/{lat}/{lon}"
        QDesktopServices.openUrl(QUrl(url))

    def _remove_metadata(self):
        """Stößt das Entfernen der Metadaten über die Hauptanwendung an."""
        app = self.parent()
        if app is None or not hasattr(app, "image_ops"):
            QMessageBox.warning(self, tr("Nicht möglich"), tr("Funktion nicht verfügbar."))
            return
        self.accept()  # Dialog schließen; das Bild ändert sich
        app.image_ops.remove_metadata()

    def load_exif_data(self, image_path):
        """Lädt und zeigt EXIF-Daten an."""
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()

            if not exif_data:
                self.table.setRowCount(1)
                self.table.setItem(0, 0, QTableWidgetItem(tr("Keine EXIF-Daten")))
                self.table.setItem(0, 1, QTableWidgetItem(""))
                self.raw_text.setText(tr("Keine EXIF-Daten gefunden."))
                return

            # Lese EXIF-Tags
            row = 0
            raw_output = []
            for tag_id, value in exif_data.items():
                tag_name = ExifTags.TAGS.get(tag_id, tag_id)

                # Formatierte Darstellung
                if isinstance(value, bytes):
                    try:
                        value_str = value.decode('utf-8', errors='ignore')
                    except:
                        value_str = str(value)
                else:
                    value_str = str(value)

                # Tabelle füllen
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(tag_name))
                self.table.setItem(row, 1, QTableWidgetItem(value_str))

                # Rohdaten
                raw_output.append(f"{tag_name}: {value_str}")
                row += 1

            # Zeilenhöhe anpassen
            for row in range(self.table.rowCount()):
                self.table.setRowHeight(row, 30)

            self.raw_text.setText("\n".join(raw_output))

        except Exception as e:
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem(tr("Fehler")))
            self.table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.raw_text.setText(f"Fehler beim Laden: {e}")
