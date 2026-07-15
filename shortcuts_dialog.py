from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QPushButton,
                             QLabel, QHBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence

class ShortcutsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tastaturkürzel - VostiraView")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px 10px;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                padding: 8px;
                border: none;
                font-weight: bold;
                color: #333333;
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

        # Titel
        title_label = QLabel("⌨️ Tastaturkürzel")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333333;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Untertitel
        subtitle_label = QLabel("Alle verfügbaren Tastaturkürzel für VostiraView")
        subtitle_label.setStyleSheet("font-size: 12px; color: #666666;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Tabelle erstellen
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Taste", "Funktion"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(True)
        self.table.verticalHeader().setVisible(False)

        # Shortcuts hinzufügen
        shortcuts = [
            # Navigation
            ("← / →", "Vorheriges / Nächstes Bild"),
            ("Pfeil links / rechts", "Bildnavigation"),

            # Datei
            ("O", "Datei öffnen"),
            ("S", "Bild speichern unter"),
            ("U", "Bild umbenennen"),
            ("Del", "Bild löschen"),

            # Zwischenablage
            ("Ctrl+C", "Ausgewählte Bilder kopieren"),
            ("Ctrl+V", "Bilder aus Zwischenablage einfügen"),

            # Bildbearbeitung
            ("Z", "Zoom-Modus umschalten"),
            ("C", "Bild zuschneiden"),
            ("A", "Bildgröße ändern"),
            ("D", "Bild drehen"),
            ("Mausrad", "Zoomen (rein/raus)"),
            ("R", "Zoom zurücksetzen"),

            # Slideshow
            ("P", "Slideshow starten/stoppen"),

            # Ansicht
            ("V", "Vollbild umschalten"),
            ("F", "Suche öffnen"),
            ("G", "Galerie öffnen/schließen"),

            # EXIF & Hilfe
            ("E", "EXIF-Daten anzeigen"),
            ("H / ?", "Diese Übersicht öffnen"),

            # Programm
            ("X", "Programm beenden"),
        ]

        for key, desc in shortcuts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            key_item = QTableWidgetItem(key)
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            key_item.setFont(QFont("Monospace", 10))
            key_item.setBackground(Qt.GlobalColor.white)
            self.table.setItem(row, 0, key_item)

            func_item = QTableWidgetItem(desc)
            func_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 1, func_item)

        for row in range(self.table.rowCount()):
            self.table.setRowHeight(row, 35)

        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        close_btn.setMinimumWidth(120)
        close_btn.setStyleSheet("""
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
        """)
        button_layout.addWidget(close_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.resize_table()

    def resize_table(self):
        """Optimiert die Tabellengröße."""
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
