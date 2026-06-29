import os
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont

from i18n import tr


class SearchDialog(QDialog):
    """Suchdialog für die Bildsuche."""

    def __init__(self, image_paths, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Suchergebnisse"))
        self.setFixedSize(800, 400)

        layout = QVBoxLayout()

        search_container = QHBoxLayout()
        search_label = QLabel(tr("Suchen:"), self)
        search_container.addWidget(search_label)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(tr("Suchbegriff eingeben..."))
        self.search_input.textChanged.connect(self.update_results)
        self.search_input.setSizePolicy(
            self.search_input.sizePolicy().Policy.Expanding,
            self.search_input.sizePolicy().Policy.Fixed
        )
        search_container.addWidget(self.search_input)
        layout.addLayout(search_container)

        self.search_results = QListWidget(self)
        self.search_results.setFixedHeight(300)
        self.search_results.setMinimumWidth(580)
        self.search_results.itemDoubleClicked.connect(self.select_image)  # Doppelklick zum Öffnen
        self.search_results.itemClicked.connect(self.select_image)  # Einfacher Klick zum Öffnen

        font = self.search_results.font()
        font.setPointSize(10)
        self.search_results.setFont(font)

        self.close_button = QPushButton(tr("Schließen"), self)
        self.close_button.clicked.connect(self.close)

        layout.addWidget(self.search_results)
        layout.addWidget(self.close_button)
        self.setLayout(layout)

        self.image_paths = image_paths
        self.selected_image = None
        self.update_results("")

    def update_results(self, query):
        """Aktualisiert die Suchergebnisse basierend auf der Eingabe."""
        self.search_results.clear()
        query = query.strip().lower()

        if not query:
            # Zeige alle Bilder
            items = [os.path.basename(img) for img in self.image_paths]
            self.search_results.addItems(items)
            return

        # Filtere Bilder basierend auf Suchbegriff
        filtered_images = []
        for img_path in self.image_paths:
            if query in os.path.basename(img_path).lower():
                filtered_images.append(img_path)

        if filtered_images:
            # Zeige die gefilterten Dateinamen
            items = [os.path.basename(img) for img in filtered_images]
            self.search_results.addItems(items)
            # Speichere die Pfade für die Auswahl
            self.search_results.setProperty("filtered_paths", filtered_images)
        else:
            self.search_results.addItem("Kein Bild gefunden")
            self.search_results.setProperty("filtered_paths", [])

    def select_image(self, item):
        """Wählt ein Bild aus der Liste aus (wird bei Klick oder Doppelklick aufgerufen)."""
        selected_filename = item.text()

        # Hole die gefilterten Pfade
        filtered_paths = self.search_results.property("filtered_paths")
        if not filtered_paths:
            # Wenn keine gefilterten Pfade, suche in allen Pfaden
            for path in self.image_paths:
                if os.path.basename(path) == selected_filename:
                    self.selected_image = path
                    self.accept()
                    return
        else:
            # Suche in den gefilterten Pfaden
            for path in filtered_paths:
                if os.path.basename(path) == selected_filename:
                    self.selected_image = path
                    self.accept()
                    return

        # Fallback: Suche in allen Pfaden
        for path in self.image_paths:
            if os.path.basename(path) == selected_filename:
                self.selected_image = path
                self.accept()
                return


class SearchHandler:
    """Verwaltet die Suchfunktionalität."""

    def __init__(self, parent):
        self.parent = parent

    def open_search_dialog(self):
        """Öffnet den Suchdialog für die Bildsuche."""
        # Stelle sicher, dass die ImageLoader-Liste aktuell ist
        # Wenn wir in der Galerie sind, verwende die Galerie-Bilder
        if self.parent.stacked_widget.currentIndex() == 1:
            # Galerie-Ansicht: Verwende die Galerie-Bilder
            gallery_images = []
            for img in self.parent.gallery_widget.images:
                img_path = os.path.join(self.parent.gallery_widget.directory, img)
                if os.path.exists(img_path):
                    gallery_images.append(img_path)
            if gallery_images:
                image_paths = gallery_images
            else:
                image_paths = self.parent.image_loader.image_paths
        else:
            # Viewer-Ansicht: Verwende die ImageLoader-Liste
            image_paths = self.parent.image_loader.image_paths

        if not image_paths:
            QMessageBox.warning(self.parent, tr("Keine Bilder"), tr("Es sind keine Bilder zum Durchsuchen vorhanden."))
            return

        search_dialog = SearchDialog(image_paths, self.parent)

        if search_dialog.exec():
            selected_image = search_dialog.selected_image
            if selected_image and os.path.exists(selected_image):
                # Wenn wir in der Galerie sind, zur Viewer-Ansicht wechseln
                if self.parent.stacked_widget.currentIndex() == 1:
                    self.parent.gallery_handler.show_gallery()

                # Bild laden
                if selected_image in self.parent.image_loader.image_paths:
                    self.parent.image_loader.current_index = self.parent.image_loader.image_paths.index(selected_image)
                else:
                    # Bild zur ImageLoader-Liste hinzufügen
                    self.parent.image_loader.image_paths.append(selected_image)
                    self.parent.image_loader.current_index = len(self.parent.image_loader.image_paths) - 1

                self.parent.image_loader.load_image(selected_image)
            elif selected_image:
                QMessageBox.warning(self.parent, tr("Fehler"), tr("Das ausgewählte Bild wurde nicht gefunden:") + f"\n{selected_image}")
