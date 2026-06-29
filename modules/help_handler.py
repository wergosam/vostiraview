from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from i18n import tr


class HelpHandler:
    def __init__(self, parent):
        self.parent = parent

    def show_shortcuts(self):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(tr("Tastaturkürzel"))
        dialog.resize(600, 500)

        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([tr("Taste"), tr("Funktion")])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        shortcuts = [
            ("— Navigation —", ""),
            ("← / →", "Vorheriges / Nächstes Bild"),
            ("P", "Slideshow starten / stoppen"),
            ("— Ansicht —", ""),
            ("G", "Galerie öffnen"),
            ("L", "Listenansicht öffnen"),
            ("V  /  F11", "Vollbild umschalten"),
            ("Z", "Zoom-Modus umschalten"),
            ("+  /  −", "Vergrößern / Verkleinern"),
            ("0", "An Fenster anpassen"),
            ("1", "Originalgröße 100 %"),
            ("R", "Zoom zurücksetzen"),
            ("F  /  Strg+F", "Suche öffnen"),
            ("E", "EXIF-Daten anzeigen"),
            ("— Datei —", ""),
            ("O  /  Strg+O", "Datei öffnen"),
            ("S  /  Strg+S", "Speichern unter"),
            ("U  /  F2", "Umbenennen"),
            ("Entf", "Löschen"),
            ("Strg+,", "Einstellungen"),
            ("X  /  Strg+Q", "Beenden"),
            ("— Bearbeiten —", ""),
            ("Strg+Z  /  Strg+Y", "Rückgängig / Wiederholen"),
            ("Strg+C / X / V", "Kopieren / Ausschneiden / Einfügen"),
            ("C", "Zuschneiden"),
            ("A", "Größe ändern"),
            ("D", "Drehen (Dialog)"),
            ("Strg+←  /  Strg+→", "90° links / rechts drehen"),
            ("Strg+Umsch+H / V", "Horizontal / Vertikal spiegeln"),
            ("B", "Bild anpassen"),
            ("— Hilfe —", ""),
            ("H  /  ?  /  F1", "Diese Hilfe anzeigen"),
        ]

        from PyQt6.QtGui import QFont, QColor
        table.setRowCount(len(shortcuts))
        for row, (key, desc) in enumerate(shortcuts):
            key_item = QTableWidgetItem(tr(key))
            desc_item = QTableWidgetItem(tr(desc))
            if desc == "":  # Abschnitts-Überschrift
                font = QFont()
                font.setBold(True)
                key_item.setForeground(QColor("#4CAF50"))
                key_item.setFont(font)
            table.setItem(row, 0, key_item)
            table.setItem(row, 1, desc_item)

        layout.addWidget(table)
        dialog.exec()

    APP_NAME = "VostiraView"
    APP_VERSION = "1.72"
    APP_TAGLINE = "Bildbetrachter mit Bearbeitungsfunktionen"
    APP_FEATURES = [
        ("📷", "Anzeigen & Navigieren"),
        ("✂️", "Zuschneiden, Drehen, Skalieren"),
        ("🔄", "Vergleichsmodus (Vorher/Nachher)"),
        ("🎬", "Slideshow"),
        ("📊", "EXIF-Daten"),
        ("🔍", "Zoom mit Mausrad"),
        ("🖼️", "Galerie-Ansicht"),
        ("🖼️", "Listen-Ansicht"),
    ]

    def show_about(self):
        dialog = QDialog(self.parent)
        dialog.setWindowTitle(f"Über {self.APP_NAME}")
        dialog.setMinimumWidth(440)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(6)

        # --- Kopfbereich ---
        logo = QLabel("🖼️")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 44px;")
        layout.addWidget(logo)

        title = QLabel(self.APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        tagline = QLabel(tr(self.APP_TAGLINE))
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline.setStyleSheet("color: #888888;")
        layout.addWidget(tagline)

        version = QLabel(f"Version {self.APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color: #888888; margin-bottom: 6px;")
        layout.addWidget(version)

        layout.addWidget(self._separator())

        # --- Funktionen ---
        features_header = QLabel(tr("Funktionen"))
        features_header.setStyleSheet("font-weight: bold; margin-top: 4px;")
        layout.addWidget(features_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.setContentsMargins(4, 4, 4, 4)
        for index, (icon, text) in enumerate(self.APP_FEATURES):
            entry = QLabel(f"{icon}  " + tr(text))
            grid.addWidget(entry, index // 2, index % 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)

        layout.addWidget(self._separator())

        # --- Fußzeile ---
        footer = QLabel(
            tr("💡 Drücke <b>H</b> oder <b>?</b> für alle Tastaturkürzel.") + "<br>"
            + tr("👤 Entwickelt von Jürg Rechsteiner (Schweiz)") + "<br>"
            + tr("🐍 Erstellt mit Python und PyQt6")
        )
        footer.setTextFormat(Qt.TextFormat.RichText)
        footer.setStyleSheet("color: #888888; margin-top: 4px;")
        layout.addWidget(footer)

        # --- Button ---
        button_row = QHBoxLayout()
        button_row.addStretch()
        ok_button = QPushButton(tr("Schließen"))
        ok_button.setDefault(True)
        ok_button.clicked.connect(dialog.accept)
        button_row.addWidget(ok_button)
        layout.addSpacing(8)
        layout.addLayout(button_row)

        dialog.exec()

    @staticmethod
    def _separator():
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line
