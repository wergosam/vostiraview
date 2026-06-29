import os
import shutil
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QApplication
from PyQt6.QtCore import QUrl
from i18n import tr


class ClipboardHandler:
    """Verwaltet Kopieren/Einfügen von Bildern über die Zwischenablage."""
    
    def __init__(self, parent):
        self.parent = parent
        self.copied_paths = []          # Zwischenspeicher für kopierte Bilder
        self.cut_paths = []             # Zwischenspeicher für ausgeschnittene Bilder
        self.is_cut = False             # Flag, ob die kopierten Bilder ausgeschnitten wurden

    def handle_key_press(self, event: QKeyEvent):
        """Behandelt Tastaturereignisse für Copy/Paste."""
        # Strg+C oder Ctrl+C
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.key() == Qt.Key.Key_C:
                self.copy_selected_images()
                return True
            elif event.key() == Qt.Key.Key_V:
                self.paste_images_from_clipboard()
                return True
            elif event.key() == Qt.Key.Key_X:
                self.cut_selected_images()
                return True
        return False
    
    def copy_selected_images(self):
        """Kopiert die ausgewählten Bilder in die Zwischenablage (ohne Löschen)."""
        self.is_cut = False  # Zurücksetzen der Cut-Flag
        self._copy_or_cut_images(cut=False)

    def cut_selected_images(self):
        """Schneidet die ausgewählten Bilder aus (kopieren + als ausgeschnitten markieren)."""
        self.is_cut = True
        self._copy_or_cut_images(cut=True)

    def _copy_or_cut_images(self, cut=False):
        """Interne Methode zum Kopieren oder Ausschneiden von Bildern."""
        # Prüfen ob wir in der Galerie sind
        if self.parent.stacked_widget.currentIndex() == 1:
            # Galerie-Ansicht: Kopiere ausgewählte Bilder
            selected = self.parent.gallery_widget.get_selected_images()
            if selected:
                self.copied_paths = selected.copy()
                if cut:
                    self.cut_paths = selected.copy()
                # Auch in die System-Zwischenablage kopieren
                self.copy_to_system_clipboard(selected)
                action = tr("Ausgeschnitten") if cut else tr("Kopiert")
                self.parent.statusBar.showMessage(f"{len(selected)} " + tr("Bild(er)") + f" {action}", 3000)
            else:
                QMessageBox.information(self.parent, tr("Keine Auswahl"),
                    tr("Bitte wählen Sie zuerst Bilder in der Galerie aus (mit Checkbox)."))
        else:
            # Viewer-Ansicht: Kopiere aktuelles Bild
            current_path = self.parent.image_loader.get_current_image_path()
            if current_path and os.path.exists(current_path):
                self.copied_paths = [current_path]
                if cut:
                    self.cut_paths = [current_path]
                self.copy_to_system_clipboard([current_path])
                action = tr("Ausgeschnitten") if cut else tr("Kopiert")
                self.parent.statusBar.showMessage(tr("Bild") + f" {action}: {os.path.basename(current_path)}", 3000)
            else:
                QMessageBox.warning(self.parent, tr("Kein Bild"), tr("Kein Bild zum Kopieren vorhanden."))

    def copy_to_system_clipboard(self, file_paths):
        """Kopiert Dateipfade in die System-Zwischenablage."""
        if not file_paths:
            return
        
        # Erstelle MIME-Daten für Datei-URLs
        mime_data = QMimeData()
        urls = [QUrl.fromLocalFile(path) for path in file_paths]
        mime_data.setUrls(urls)
        
        # In die Zwischenablage kopieren
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
    
    def paste_images_from_clipboard(self):
        """Fügt Bilder aus der Zwischenablage ein."""
        # Prüfen ob Bilder in der Zwischenablage sind
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if mime_data.hasUrls():
            urls = mime_data.urls()
            image_paths = []
            for url in urls:
                file_path = url.toLocalFile()
                if self.parent.is_image_file(file_path) and os.path.exists(file_path):
                    image_paths.append(file_path)
            
            if image_paths:
                # Frage ob kopiert oder nur angezeigt werden soll
                msg_box = QMessageBox(self.parent)
                msg_box.setWindowTitle(tr("Bilder einfügen"))
                msg_box.setIcon(QMessageBox.Icon.Question)
                
                count = len(image_paths)
                bild_text = "Bild" if count == 1 else "Bilder"
                
                msg_box.setText(tr("Möchten Sie die ausgewählten Bilder einfügen?"))
                msg_box.setInformativeText(
                    tr("📁 In Galerie kopieren - Zum Viewer-Ordner hinzufügen\n👁️‍🗨️ Nur anzeigen - Originale bleiben wo sie sind")
                )
                
                copy_btn = msg_box.addButton(tr("📁 Kopieren"), QMessageBox.ButtonRole.YesRole)
                view_btn = msg_box.addButton(tr("👁️ Nur anzeigen"), QMessageBox.ButtonRole.NoRole)
                cancel_btn = msg_box.addButton(tr("Abbrechen"), QMessageBox.ButtonRole.RejectRole)
                
                msg_box.setDefaultButton(copy_btn)
                msg_box.exec()
                
                clicked_button = msg_box.clickedButton()
                
                if clicked_button == copy_btn:
                    # In den Viewer-Ordner kopieren
                    copied_paths = self.parent.gallery_widget.copy_images_to_directory(image_paths)
                    if copied_paths:
                        self.parent.gallery_widget.update_gallery_after_copy(copied_paths)
                        self.parent.image_loader.update_directory(self.parent.image_loader.image_directory)
                        self.parent.statusBar.showMessage(f"{len(copied_paths)} " + tr("Bilder eingefügt"), 3000)
                        
                        # Wenn es sich um ausgeschnittene Bilder handelt, die Originale löschen
                        if self.is_cut and self.cut_paths:
                            self._delete_cut_originals()
                            self.is_cut = False
                            self.cut_paths = []
                elif clicked_button == view_btn:
                    # Nur anzeigen
                    self.parent.gallery_widget.add_images_to_gallery(image_paths)
                    self.parent.statusBar.showMessage(f"{len(image_paths)} " + tr("Bilder angezeigt"), 3000)
                else:
                    # Abbrechen
                    return
            else:
                QMessageBox.information(self.parent, tr("Keine Bilder"),
                    tr("Die Zwischenablage enthält keine Bilddateien."))
        else:
            # Prüfen ob Text in der Zwischenablage ist (Dateipfade)
            if mime_data.hasText():
                text = mime_data.text()
                # Prüfen ob es sich um Dateipfade handelt
                image_paths = []
                for line in text.split('\n'):
                    line = line.strip()
                    if os.path.exists(line) and self.parent.is_image_file(line):
                        image_paths.append(line)
                
                if image_paths:
                    self.parent.handle_dropped_images(image_paths)
                else:
                    QMessageBox.information(self.parent, tr("Keine Bilder"),
                        tr("Die Zwischenablage enthält keine Bilddateien."))
            else:
                QMessageBox.information(self.parent, tr("Keine Bilder"),
                    tr("Die Zwischenablage enthält keine Bilder."))
    
    def _delete_cut_originals(self):
        """Löscht die als ausgeschnitten markierten Originale."""
        for path in self.cut_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    # Aus der ImageLoader-Liste entfernen, falls vorhanden
                    if path in self.parent.image_loader.image_paths:
                        self.parent.image_loader.image_paths.remove(path)
                except Exception as e:
                    print(f"Fehler beim Löschen von {path}: {e}")
        # Galerie aktualisieren
        self.parent.gallery_widget.update_directory(self.parent.image_loader.image_directory)
        # Aktuelle Bildanzeige aktualisieren, falls das gelöschte Bild aktuell war
        if self.parent.image_loader.current_index >= len(self.parent.image_loader.image_paths):
            self.parent.image_loader.current_index = len(self.parent.image_loader.image_paths) - 1
        if self.parent.image_loader.image_paths:
            self.parent.image_loader.load_image(self.parent.image_loader.image_paths[self.parent.image_loader.current_index])
        else:
            self.parent.clear_image_display()

    def get_copied_paths(self):
        """Gibt die zuletzt kopierten Pfade zurück."""
        return self.copied_paths