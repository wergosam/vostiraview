import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtGui import QPixmap

from config import load_config
from utils import resource_path
from resize import resize_current_image
from rotation import show_rotation_dialog
from modules.trash import (move_to_trash, restore_from_trash,
                           copy_to_trash, copy_from_trash)
from modules.image_export import (build_filter_string, format_for_extension,
                                  ensure_extension, save_pixmap_as, save_pil_image)
from PIL import Image
from i18n import tr


class ImageOperations:
    """Verwaltet Bildbearbeitungsoperationen."""
    
    def __init__(self, parent):
        self.parent = parent
        
    def start_crop_mode(self):
        """Startet den Crop-Modus für das aktuelle Bild."""
        # Deaktiviere Zoom-Modus wenn aktiv
        if hasattr(self.parent, 'zoom_handler') and self.parent.zoom_handler._zoom_mode:
            self.parent.zoom_handler.toggle_zoom_mode()
        
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr("Fehler"), tr("Kein Bild zum Zuschneiden ausgewählt."))
            return

        current_image = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        self.parent.crop_widget.load_image_from_path(resource_path(current_image))
        self.parent.stacked_widget.setCurrentIndex(2)
        
    def resize_current_image(self):
        """Ruft den Bildgrößenänderungs-Dialog auf."""
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild zum Ändern der Größe.'))
            return

        current_image_path = resource_path(
            self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        )

        # Überschreiben-Modus: nach Bestätigung direkt ins Original speichern
        if self._overwrite_mode():
            if self._save_edit(
                    "Größe ändern", current_image_path,
                    lambda p: resize_current_image(self.parent, current_image_path, output_path=p) is not None):
                QMessageBox.information(self.parent, tr('Erfolg'), tr('Bild erfolgreich geändert.'))
            return

        resized_path = resize_current_image(self.parent, current_image_path)

        if resized_path:
            # Zustand vor der Änderung für Rückgängig sichern
            prev_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]

            self.parent.image_loader.image_paths.append(resized_path)
            self.parent.image_loader.current_index = len(self.parent.image_loader.image_paths) - 1
            self.parent.image_loader.load_image(resized_path)
            self.parent.image_loader.update_directory(self.parent.image_loader.image_directory)

            # Rückgängig/Wiederholen für die Größenänderung registrieren
            self._push_added_file_command("Größe ändern", resized_path, prev_path)

            QMessageBox.information(self.parent, tr('Erfolg'), tr('Bild erfolgreich geändert.'))
            
    def rotate_current_image(self):
        """Dreht das aktuelle Bild."""
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild zum Drehen ausgewählt.'))
            return

        current_image_path = resource_path(
            self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        )

        try:
            rotated_pixmap, angle = show_rotation_dialog(self.parent, current_image_path)

            if rotated_pixmap and angle is not None:
                # Überschreiben-Modus: ohne Speichern-Dialog ins Original schreiben
                if self._overwrite_mode():
                    if self._save_edit(
                            "Drehen", current_image_path,
                            lambda p: save_pixmap_as(rotated_pixmap, p, format_for_extension(os.path.splitext(p)[1]))):
                        QMessageBox.information(self.parent, tr('Erfolg'), tr('Bild wurde um {a}° gedreht.').format(a=angle))
                    return

                directory = os.path.dirname(current_image_path)
                filename = os.path.basename(current_image_path)
                base_name, ext = os.path.splitext(filename)
                suggested_name = f"{base_name}_rotated{ext}"

                file_path, selected_filter = QFileDialog.getSaveFileName(
                    self.parent,
                    tr("Gedrehtes Bild speichern"),
                    os.path.join(directory, suggested_name),
                    build_filter_string()
                )

                if file_path:
                    file_path, save_ext = ensure_extension(file_path, selected_filter)
                    if save_pixmap_as(rotated_pixmap, file_path, format_for_extension(save_ext)):
                        # Zustand vor der Änderung für Rückgängig sichern
                        prev_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]

                        self.parent.image_loader.image_paths.append(file_path)
                        self.parent.image_loader.current_index = len(self.parent.image_loader.image_paths) - 1

                        self.parent.image_loader.update_directory(self.parent.image_loader.image_directory)
                        self.parent.gallery_widget.update_directory(self.parent.image_loader.image_directory)

                        self.parent.image_loader.load_image(file_path)
                        self.parent.image_viewer.update()

                        # Rückgängig/Wiederholen für die Drehung registrieren
                        self._push_added_file_command("Drehen", file_path, prev_path)

                        QMessageBox.information(self.parent, tr('Erfolg'), tr('Bild wurde um {a}° gedreht.').format(a=angle))
                    else:
                        QMessageBox.warning(self.parent, tr('Fehler'), tr('Das gedrehte Bild konnte nicht gespeichert werden.'))
        except Exception as e:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Ein Fehler ist aufgetreten:') + f' {e}')
            
    def rotate_left_90(self):
        """Dreht das aktuelle Bild um 90° gegen den Uhrzeigersinn (sofort)."""
        self._quick_transform("90° links gedreht", Image.Transpose.ROTATE_90)

    def rotate_right_90(self):
        """Dreht das aktuelle Bild um 90° im Uhrzeigersinn (sofort)."""
        self._quick_transform("90° rechts gedreht", Image.Transpose.ROTATE_270)

    def flip_horizontal(self):
        """Spiegelt das aktuelle Bild horizontal (sofort)."""
        self._quick_transform("Horizontal gespiegelt", Image.Transpose.FLIP_LEFT_RIGHT)

    def flip_vertical(self):
        """Spiegelt das aktuelle Bild vertikal (sofort)."""
        self._quick_transform("Vertikal gespiegelt", Image.Transpose.FLIP_TOP_BOTTOM)

    def adjust_current_image(self):
        """Öffnet den Anpassungs-Dialog (Helligkeit/Kontrast/Sättigung/Schärfe)."""
        il = self.parent.image_loader
        if not il.image_paths or il.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild zum Anpassen ausgewählt.'))
            return
        from ui.adjust_dialog import AdjustDialog
        path = il.image_paths[il.current_index]
        factors = AdjustDialog.get_adjustments(self.parent, path)
        if factors is None:
            return
        self._apply_pil_edit("Anpassen", "angepasst", path,
                             lambda im: AdjustDialog.apply_factors(im, factors))

    def remove_metadata(self):
        """Speichert das aktuelle Bild ohne EXIF-/Metadaten (Datenschutz).

        Nutzt dieselbe Speicherlogik wie die Anpassungen: im Überschreiben-Modus
        wird das Original ersetzt (mit Sicherung/Undo), sonst als neue Datei
        gespeichert. Beim Neuschreiben über Pillow gehen Metadaten verloren.
        """
        il = self.parent.image_loader
        if not il.image_paths or il.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild ausgewählt.'))
            return
        path = il.image_paths[il.current_index]
        self._apply_pil_edit("Metadaten entfernen", "ohne_metadaten", path,
                             lambda im: im.copy())

    def _apply_pil_edit(self, description, suffix, src_path, transform):
        """Wendet eine PIL-Transformation an und speichert das Ergebnis.

        Im Überschreiben-Modus wird das Original ersetzt (mit Sicherung/Undo),
        sonst per Dialog als neue Datei gespeichert. `transform(PIL.Image)` muss
        das bearbeitete PIL-Bild zurückgeben.
        """
        il = self.parent.image_loader

        if self._overwrite_mode():
            def save_fn(p):
                with Image.open(src_path) as im:
                    out = transform(im)
                save_pil_image(out, p, format_for_extension(os.path.splitext(p)[1]))
                return True
            if self._save_edit(description, src_path, save_fn):
                QMessageBox.information(self.parent, tr('Erfolg'), f'{tr(description)}: ' + tr('gespeichert.'))
            return

        # Nicht-Überschreiben: als neue Datei speichern
        directory = os.path.dirname(src_path)
        base, ext = os.path.splitext(os.path.basename(src_path))
        suggested = os.path.join(directory, f"{base}_{suffix}{ext}")
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.parent, f"{description}: speichern unter", suggested, build_filter_string())
        if not file_path:
            return
        file_path, save_ext = ensure_extension(file_path, selected_filter)
        prev_path = il.image_paths[il.current_index]
        try:
            with Image.open(src_path) as im:
                out = transform(im)
            save_pil_image(out, file_path, format_for_extension(save_ext))
        except Exception as e:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Konnte nicht speichern:') + f' {e}')
            return
        if file_path not in il.image_paths:
            il.image_paths.append(file_path)
        self._refresh()
        self._reselect(file_path)
        self._push_added_file_command(description, file_path, prev_path)
        QMessageBox.information(self.parent, tr('Erfolg'), f'{tr(description)}: ' + tr('gespeichert.'))

    def _quick_transform(self, description, transpose_op):
        """Wendet eine verlustarme Sofort-Transformation auf das Original an.

        Speichert direkt im Original (mit Papierkorb-Sicherung + Undo), ohne
        Speichern-Dialog und ohne Rückfrage – wie bei Bildbetrachtern üblich.
        """
        il = self.parent.image_loader
        if not il.image_paths or il.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild ausgewählt.'))
            return

        path = il.image_paths[il.current_index]

        def save_fn(p):
            with Image.open(p) as im:
                out = im.transpose(transpose_op)
            save_pil_image(out, p, format_for_extension(os.path.splitext(p)[1]))
            return True

        if self._save_edit(description, path, save_fn, confirm=False):
            self.parent.statusBar.showMessage(f"{tr(description)} (" + tr("Rückgängig mit Strg+Z") + ")", 3000)

    def _refresh(self):
        """Liest das aktuelle Verzeichnis neu ein und aktualisiert die Ansicht."""
        il = self.parent.image_loader
        il.update_directory(il.image_directory)
        self.parent.gallery_widget.update_directory(il.image_directory)
        self.parent.image_viewer.update()

    def _reselect(self, path):
        """Wählt das Bild mit dem angegebenen Pfad aus, falls noch vorhanden."""
        il = self.parent.image_loader
        if path and path in il.image_paths:
            il.current_index = il.image_paths.index(path)
            il.load_image(path)

    def _push_added_file_command(self, description, new_file, prev_path):
        """Registriert eine Operation, die eine neue Datei erzeugt hat
        (Drehen/Zuschneiden/Größe ändern), für Rückgängig/Wiederholen.

        Rückgängig verschiebt die erzeugte Datei in den Papierkorb (statt sie
        endgültig zu löschen), damit Wiederholen sie wiederherstellen kann.
        """
        state = {'trash': None}

        def undo():
            state['trash'] = move_to_trash(new_file)
            self._refresh()
            self._reselect(prev_path)

        def redo():
            if state['trash']:
                restore_from_trash(state['trash'], new_file)
                state['trash'] = None
            self._refresh()
            self._reselect(new_file)

        self.parent.undo_manager.push(description, undo, redo)

    def _overwrite_mode(self):
        """True, wenn Bearbeitungen das Original überschreiben sollen."""
        return bool(load_config().get("overwrite_on_edit", False))

    def _confirm_overwrite(self, path):
        """Sicherheitsabfrage vor dem Überschreiben des Originals."""
        reply = QMessageBox.question(
            self.parent,
            tr("Original überschreiben?"),
            tr("Die Originaldatei „{name}“ wird durch die bearbeitete Version ersetzt. "
               "Eine Sicherung wird im Papierkorb abgelegt und kann mit Rückgängig "
               "(Strg+Z) wiederhergestellt werden. Fortfahren?").format(name=os.path.basename(path)),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _push_overwrite_command(self, description, target_path, pre_backup):
        """Registriert eine Operation, die das Original überschrieben hat, für
        Rückgängig/Wiederholen.

        `pre_backup` ist eine Papierkorb-Kopie des Originals (vor der Änderung).
        Rückgängig stellt das Original wieder her, Wiederholen die bearbeitete
        Version – beide Versionen liegen als Kopie im Papierkorb.
        """
        state = {'pre': pre_backup, 'post': None}

        def undo():
            # Bearbeitete Version einmalig für Wiederholen sichern
            if state['post'] is None:
                state['post'] = copy_to_trash(target_path)
            if state['pre']:
                copy_from_trash(state['pre'], target_path)
            self._refresh()
            self._reselect(target_path)

        def redo():
            if state['post']:
                copy_from_trash(state['post'], target_path)
            self._refresh()
            self._reselect(target_path)

        self.parent.undo_manager.push(description, undo, redo)

    def _save_edit(self, description, target_path, save_fn, confirm=True):
        """Gemeinsame Logik zum Überschreiben des Originals.

        `save_fn(path)` muss das bearbeitete Bild speichern und True/False
        zurückgeben. Legt vorher eine Sicherung des Originals an und
        registriert Rückgängig/Wiederholen. `confirm=False` überspringt die
        Sicherheitsabfrage (für Schnellaktionen wie 90°-Drehen/Spiegeln).
        """
        if confirm and not self._confirm_overwrite(target_path):
            return False
        pre = copy_to_trash(target_path)
        if save_fn(target_path):
            self._refresh()
            self._reselect(target_path)
            self._push_overwrite_command(description, target_path, pre)
            return True
        # Speichern fehlgeschlagen -> Sicherung verwerfen
        if pre and os.path.exists(pre):
            try:
                os.remove(pre)
            except Exception:
                pass
        return False

    def _push_delete_command(self, restore_list):
        """Registriert ein bereits ausgeführtes Löschen für Rückgängig/Wiederholen.

        `restore_list` ist eine Liste von (papierkorb_pfad, original_pfad).
        Rückgängig stellt aus dem Papierkorb wieder her, Wiederholen verschiebt
        erneut in den Papierkorb.
        """
        state = {'pairs': list(restore_list)}

        def undo():
            restored = []
            for trash_path, original_path in state['pairs']:
                if restore_from_trash(trash_path, original_path):
                    restored.append(original_path)
            self._refresh()
            if restored:
                self._reselect(restored[0])

        def redo():
            new_pairs = []
            for _trash_path, original_path in state['pairs']:
                if os.path.exists(original_path):
                    trash_path = move_to_trash(original_path)
                    if trash_path:
                        new_pairs.append((trash_path, original_path))
                    if original_path in self.parent.image_loader.image_paths:
                        self.parent.image_loader.image_paths.remove(original_path)
            state['pairs'] = new_pairs
            self._refresh()

        self.parent.undo_manager.push("Löschen", undo, redo)

    def delete_image(self):
        """Löscht das aktuelle Bild oder die in der Galerie markierten Bilder."""
        # Galerie-Modus: Markierte Bilder löschen
        if self.parent.gallery_widget.selected_images:
            reply = QMessageBox.question(
                self.parent,
                tr('Bilder löschen'),
                tr('Möchten Sie die ausgewählten Bilder wirklich löschen?'),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                restore_list = []
                for image_path in self.parent.gallery_widget.selected_images:
                    if os.path.exists(image_path):
                        try:
                            trash_path = move_to_trash(image_path)
                            if trash_path:
                                restore_list.append((trash_path, image_path))
                            if image_path in self.parent.image_loader.image_paths:
                                self.parent.image_loader.image_paths.remove(image_path)
                        except Exception as e:
                            print(f"Fehler beim Löschen von {image_path}: {e}")

                self.parent.gallery_widget.selected_images.clear()
                self.parent.gallery_widget.update_directory(self.parent.image_loader.image_directory)

                if self.parent.image_loader.image_paths:
                    self.parent.image_loader.current_index = 0
                    self.parent.image_loader.load_image(self.parent.image_loader.image_paths[0])
                else:
                    self.parent.image_loader.current_index = -1
                    self.parent.clear_image_display()

                # Rückgängig/Wiederholen für das Löschen registrieren
                if restore_list:
                    self._push_delete_command(restore_list)
                return

        # Einzelbild-Modus: Aktuelles Bild löschen
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild zum Löschen vorhanden.'))
            return

        current_image_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]

        reply = QMessageBox.question(
            self.parent,
            tr('Bild löschen'),
            tr('Möchten Sie das aktuelle Bild wirklich löschen?'),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                trash_path = move_to_trash(current_image_path)
                del self.parent.image_loader.image_paths[self.parent.image_loader.current_index]

                self.parent.gallery_widget.update_directory(self.parent.image_loader.image_directory)

                if self.parent.image_loader.image_paths:
                    self.parent.image_loader.current_index = min(
                        self.parent.image_loader.current_index,
                        len(self.parent.image_loader.image_paths) - 1
                    )
                    self.parent.image_loader.load_image(
                        self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
                    )
                else:
                    self.parent.image_loader.current_index = -1
                    self.parent.clear_image_display()

                # Rückgängig/Wiederholen für das Löschen registrieren
                if trash_path:
                    self._push_delete_command([(trash_path, current_image_path)])

                QMessageBox.information(self.parent, tr('Erfolg'), tr('Bild wurde in den Papierkorb verschoben.'))

            except Exception as e:
                QMessageBox.warning(self.parent, tr('Fehler'), tr('Fehler beim Löschen des Bildes:') + f' {e}')