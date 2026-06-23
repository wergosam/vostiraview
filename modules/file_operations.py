import os
import shutil
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog, QLineEdit
from PyQt6.QtGui import QPixmap

from modules.image_export import (build_filter_string, format_for_extension,
                                  primary_extension_for_filter, same_format,
                                  convert_and_save)
from i18n import tr


class FileOperations:
    def __init__(self, parent):
        self.parent = parent

    # ==================== IN ORDNER VERSCHIEBEN / KOPIEREN ====================
    @staticmethod
    def _unique_path(path):
        """Hängt bei Bedarf _1, _2 … an, um nichts zu überschreiben."""
        if not os.path.exists(path):
            return path
        base, ext = os.path.splitext(path)
        i = 1
        while os.path.exists(f"{base}_{i}{ext}"):
            i += 1
        return f"{base}_{i}{ext}"

    def _refresh_views(self):
        il = self.parent.image_loader
        d = il.image_directory
        if not d:
            return
        il.update_directory(d)
        self.parent.gallery_widget.update_directory(d)
        self.parent.list_view_widget.update_directory(d)

    def _choose_folder(self, title):
        start = self.parent.image_loader.image_directory or os.path.expanduser("~")
        return QFileDialog.getExistingDirectory(
            self.parent, title, start, QFileDialog.Option.ShowDirsOnly)

    def copy_to_folder(self, paths):
        """Kopiert die angegebenen Bilder in einen wählbaren Ordner."""
        if not paths:
            return
        dest = self._choose_folder(tr("In Ordner kopieren"))
        if not dest:
            return
        count = 0
        for src in paths:
            if not os.path.exists(src):
                continue
            if os.path.abspath(os.path.dirname(src)) == os.path.abspath(dest):
                continue  # schon im Zielordner
            try:
                shutil.copy2(src, self._unique_path(os.path.join(dest, os.path.basename(src))))
                count += 1
            except Exception as e:
                print(f"Fehler beim Kopieren von {src}: {e}")
        self._refresh_views()
        self.parent.statusBar.showMessage(f"{count} " + tr("Bild(er) kopiert nach") + f" {dest}", 4000)

    def move_to_folder(self, paths):
        """Verschiebt die angegebenen Bilder in einen wählbaren Ordner (mit Undo)."""
        if not paths:
            return
        dest = self._choose_folder(tr("In Ordner verschieben"))
        if not dest:
            return
        moved = []
        for src in paths:
            if not os.path.exists(src):
                continue
            if os.path.abspath(os.path.dirname(src)) == os.path.abspath(dest):
                continue
            target = self._unique_path(os.path.join(dest, os.path.basename(src)))
            try:
                shutil.move(src, target)
                moved.append((src, target))
            except Exception as e:
                print(f"Fehler beim Verschieben von {src}: {e}")
        self._refresh_views()
        if moved:
            self._push_move_command(moved)
        self.parent.statusBar.showMessage(f"{len(moved)} " + tr("Bild(er) verschoben nach") + f" {dest}", 4000)

    def _push_move_command(self, moved):
        """Registriert ein Verschieben für Rückgängig/Wiederholen.

        `moved`: Liste von (ursprung, ziel). Rückgängig schiebt die Dateien an
        den Ursprung zurück, Wiederholen wieder ins Ziel.
        """
        state = {"pairs": list(moved)}  # (home, away) – Datei liegt aktuell bei away

        def undo():
            new = []
            for home, away in state["pairs"]:
                if os.path.exists(away):
                    target = self._unique_path(home)
                    try:
                        shutil.move(away, target)
                        new.append((target, away))
                        continue
                    except Exception as e:
                        print(f"Fehler beim Zurückverschieben: {e}")
                new.append((home, away))
            state["pairs"] = new
            self._refresh_views()

        def redo():
            new = []
            for home, away in state["pairs"]:
                if os.path.exists(home):
                    target = self._unique_path(away)
                    try:
                        shutil.move(home, target)
                        new.append((home, target))
                        continue
                    except Exception as e:
                        print(f"Fehler beim erneuten Verschieben: {e}")
                new.append((home, away))
            state["pairs"] = new
            self._refresh_views()

        self.parent.undo_manager.push("Verschieben", undo, redo)

    def save_image_as(self):
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr('Fehler'), tr('Kein Bild zum Speichern'))
            return

        current_image_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        directory = os.path.dirname(current_image_path)
        filename = os.path.basename(current_image_path)

        file_path, selected_filter = QFileDialog.getSaveFileName(
            self.parent,
            tr("Bild speichern unter"),
            os.path.join(directory, filename),
            build_filter_string()
        )

        if file_path:
            # Fehlt eine Endung, die Standard-Endung des gewählten Filters anhängen
            ext = os.path.splitext(file_path)[1]
            if not ext:
                primary = primary_extension_for_filter(selected_filter)
                if primary:
                    file_path = f"{file_path}.{primary}"
                    ext = f".{primary}"

            try:
                src_ext = os.path.splitext(current_image_path)[1]
                pil_format = format_for_extension(ext)

                if pil_format is None:
                    # Unbekannte Endung -> unverändert kopieren (Fallback)
                    shutil.copy2(current_image_path, file_path)
                elif same_format(src_ext, ext):
                    # Gleiches Format -> verlustfrei kopieren (keine Neukodierung)
                    shutil.copy2(current_image_path, file_path)
                else:
                    # Format wechselt -> echte Konvertierung über Pillow
                    convert_and_save(current_image_path, file_path, pil_format)

                self.parent.statusBar.showMessage(tr("Bild gespeichert:") + f" {os.path.basename(file_path)}", 3000)

                if file_path != current_image_path:
                    self.parent.image_loader.image_paths.append(file_path)
                    self.parent.image_loader.current_index = self.parent.image_loader.image_paths.index(file_path)

                self.parent.image_loader.update_directory(self.parent.image_loader.image_directory)
                self.parent.gallery_widget.update_directory(self.parent.image_loader.image_directory)
                self.parent.list_view_widget.update_directory(self.parent.image_loader.image_directory)
                self.parent.update_image_info(file_path)

            except Exception as e:
                QMessageBox.warning(self.parent, tr('Fehler'), tr('Das Bild konnte nicht gespeichert werden:') + f' {e}')

    def rename_image(self):
        if not self.parent.image_loader.image_paths or self.parent.image_loader.current_index == -1:
            QMessageBox.warning(self.parent, tr("Fehler"), tr("Kein Bild zum Umbenennen ausgewählt."))
            return

        current_image_path = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
        directory, old_name = os.path.split(current_image_path)
        old_base, old_ext = os.path.splitext(old_name)

        new_base, ok = QInputDialog.getText(
            self.parent,
            tr("Bild umbenennen"),
            tr("Neuer Name (ohne Erweiterung):"),
            QLineEdit.EchoMode.Normal,
            old_base
        )

        if ok and new_base.strip():
            new_name = new_base.strip() + old_ext
            new_image_path = os.path.join(directory, new_name)

            if new_image_path == current_image_path:
                self.parent.statusBar.showMessage(tr("Name unverändert"), 2000)
                return

            if os.path.exists(new_image_path):
                reply = QMessageBox.question(
                    self.parent,
                    tr("Datei existiert"),
                    tr("Die Datei „{name}“ existiert bereits. Überschreiben?").format(name=new_name),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            try:
                os.rename(current_image_path, new_image_path)
                self.parent.image_loader.image_paths[self.parent.image_loader.current_index] = new_image_path
                self.parent.image_loader.update_directory(directory)
                self.parent.gallery_widget.update_directory(directory)
                self.parent.list_view_widget.update_directory(directory)
                self.parent.update_image_info(new_image_path)
                self.parent.statusBar.showMessage(tr("Umbenannt in:") + f" {new_name}", 3000)

            except Exception as e:
                QMessageBox.critical(self.parent, tr("Fehler"), tr("Das Bild konnte nicht umbenannt werden:") + f" {e}")

    def sort_images(self, criterion="name", order="asc"):
        if not self.parent.image_loader.image_paths:
            return

        self.parent.current_sort_criterion = criterion
        self.parent.current_sort_order = order

        reverse = order == "desc"

        if criterion == "name":
            self.parent.image_loader.image_paths.sort(
                key=lambda x: os.path.basename(x).lower(), reverse=reverse
            )
        elif criterion == "date":
            self.parent.image_loader.image_paths.sort(
                key=lambda x: os.path.getmtime(x), reverse=reverse
            )
        elif criterion == "size":
            self.parent.image_loader.image_paths.sort(
                key=lambda x: os.path.getsize(x), reverse=reverse
            )

        self.parent.gallery_widget.update_directory(
            self.parent.image_loader.image_directory, criterion, order
        )
        self.parent.list_view_widget.update_directory(
            self.parent.image_loader.image_directory, criterion, order
        )

        if self.parent.image_loader.current_index != -1:
            current_image = self.parent.image_loader.image_paths[self.parent.image_loader.current_index]
            if current_image in self.parent.image_loader.image_paths:
                self.parent.image_loader.current_index = self.parent.image_loader.image_paths.index(current_image)

        self.parent.statusBar.showMessage(tr("Sortiert nach") + f" {criterion} ({order})", 2000)