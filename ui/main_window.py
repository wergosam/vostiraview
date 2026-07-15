from PyQt6.QtWidgets import QToolBar, QMenu
from PyQt6.QtGui import QAction, QIcon, QKeySequence, QActionGroup

# Relativer Import statt sys.path-Hack: funktioniert, weil "ui" jetzt ein
# echtes Package ist (siehe ui/__init__.py) und icons.py darin liegt.
from . import icons as IC
from i18n import tr


class MainWindowUI:
    def __init__(self, parent):
        self.parent = parent

    # ------------------------------------------------------------------
    # Hilfsfunktion: erspart die doppelte Erstellung von QAction-Objekten
    # für Menü und Toolbar. Eine Action wird einmal erzeugt und kann danach
    # an beliebig vielen Stellen (Menü, Toolbar, Untermenü) hinzugefügt
    # werden - Status (checked/enabled/icon) bleibt dadurch automatisch
    # überall synchron.
    # ------------------------------------------------------------------
    def _action(self, icon, text, slot=None, *, shortcut=None, shortcuts=None,
                checkable=False, checked=False, tooltip=None, enabled=True):
        action = QAction(icon, text, self.parent) if icon is not None else QAction(text, self.parent)
        if shortcut is not None:
            action.setShortcut(shortcut)
        if shortcuts is not None:
            action.setShortcuts(shortcuts)
        if checkable:
            action.setCheckable(True)
            action.setChecked(checked)
        if tooltip:
            action.setToolTip(tooltip)
        if not enabled:
            action.setEnabled(False)
        if slot is not None:
            action.triggered.connect(slot)
        return action

    def create_menu(self):
        self.parent.menubar = self.parent.menuBar()

        # ----------------------------------------------------------------
        # Menü: Datei  (Öffnen, Speichern, Sortieren, Einstellungen, Beenden)
        # ----------------------------------------------------------------
        self.parent.file_menu = self.parent.menubar.addMenu(tr("&Datei"))

        self.parent.open_action = self._action(
            QIcon.fromTheme("document-open"), tr("Datei öffnen (Taste o)"),
            self.parent.image_loader.open_file,
            shortcut=QKeySequence.StandardKey.Open)  # Strg+O
        self.parent.file_menu.addAction(self.parent.open_action)

        self.parent.select_dir_action = self._action(
            QIcon.fromTheme("folder-open"), tr("Bildverzeichnis wählen"),
            self.parent.image_loader.change_directory)
        self.parent.file_menu.addAction(self.parent.select_dir_action)

        self.parent.recent_menu = self.parent.file_menu.addMenu(
            QIcon.fromTheme("document-open-recent"), tr("Zuletzt verwendet"))
        self.parent.recent_menu.aboutToShow.connect(self.parent.populate_recent_menu)

        self.parent.file_menu.addSeparator()

        self.parent.save_as_action = self._action(
            IC.icon_save_as(), tr("Speichern unter (Taste s)"),
            self.parent.file_ops.save_image_as,
            shortcuts=[QKeySequence(QKeySequence.StandardKey.Save),       # Strg+S
                       QKeySequence(QKeySequence.StandardKey.SaveAs)])    # Strg+Shift+S
        self.parent.save_as_btn = self.parent.save_as_action  # Alias für Rückwärtskompatibilität
        self.parent.file_menu.addAction(self.parent.save_as_action)

        self.parent.rename_action = self._action(
            IC.icon_rename(), tr("Umbenennen (Taste u)"),
            self.parent.rename_selected_image, shortcut=QKeySequence("F2"))
        self.parent.rename_btn = self.parent.rename_action
        self.parent.file_menu.addAction(self.parent.rename_action)

        self.parent.file_menu.addSeparator()

        # Sortier-Untermenü: EINE gemeinsame QMenu, die sowohl im Datei-Menü
        # als auch später als Dropdown des Toolbar-Sortierbuttons verwendet
        # wird (statt die 6 Actions zweimal zu bauen).
        self.parent.sort_menu = self._build_sort_menu()
        self.parent.sort_menu.setIcon(IC.icon_sort())
        self.parent.file_menu.addMenu(self.parent.sort_menu)

        self.parent.move_to_folder_action = self._action(
            IC.icon_move_folder(), tr("In Ordner verschieben…"),
            self.parent.move_selection_to_folder)
        self.parent.file_menu.addAction(self.parent.move_to_folder_action)

        self.parent.copy_to_folder_action = self._action(
            IC.icon_copy_folder(), tr("In Ordner kopieren…"),
            self.parent.copy_selection_to_folder)
        self.parent.file_menu.addAction(self.parent.copy_to_folder_action)

        self.parent.batch_action = self._action(
            IC.icon_batch(), tr("Stapelverarbeitung… (Galerie/Liste)"),
            self.parent.open_batch_processor,
            tooltip=tr("Markierte Bilder konvertieren/verkleinern"))
        self.parent.file_menu.addAction(self.parent.batch_action)

        self.parent.file_menu.addSeparator()

        # Einstellungen (neu)
        self.parent.settings_action = self._action(
            None, tr("⚙️ Einstellungen"), self.parent.open_settings,
            shortcut=QKeySequence("Ctrl+,"))
        self.parent.file_menu.addAction(self.parent.settings_action)

        self.parent.manage_trash_action = self._action(
            QIcon.fromTheme("user-trash-full"), tr("🗑️ Papierkorb verwalten…"),
            self.parent.open_trash_manager)
        self.parent.file_menu.addAction(self.parent.manage_trash_action)

        self.parent.empty_trash_action = self._action(
            QIcon.fromTheme("user-trash"), tr("🗑️ Papierkorb leeren"),
            self.parent.empty_trash)
        self.parent.file_menu.addAction(self.parent.empty_trash_action)

        self.parent.file_menu.addSeparator()

        self.parent.exit_action = self._action(
            QIcon.fromTheme("application-exit"), tr("Beenden (Taste x)"),
            self.parent.close, shortcut=QKeySequence("Ctrl+Q"))
        self.parent.file_menu.addAction(self.parent.exit_action)

        # ----------------------------------------------------------------
        # Menü: Bearbeiten  (Zwischenablage + Bildbearbeitung + Löschen)
        # ----------------------------------------------------------------
        self.parent.edit_menu = self.parent.menubar.addMenu(tr("&Bearbeiten"))

        # Rückgängig (vorbereitet: nutzt UndoManager; initial deaktiviert,
        # bis eine Operation einen rückgängig machbaren Schritt hinterlegt)
        self.parent.undo_action = self._action(
            IC.icon_undo(), tr("Rückgängig (Strg+Z)"), self.parent.undo_last_action,
            shortcut=QKeySequence.StandardKey.Undo, enabled=False)
        self.parent.edit_menu.addAction(self.parent.undo_action)

        self.parent.redo_action = self._action(
            IC.icon_redo(), tr("Wiederholen (Strg+Y)"), self.parent.redo_last_action,
            shortcut=QKeySequence.StandardKey.Redo, enabled=False)
        self.parent.edit_menu.addAction(self.parent.redo_action)

        self.parent.edit_menu.addSeparator()

        self.parent.copy_action = self._action(
            IC.icon_copy(), tr("Kopieren (Strg+C)"),
            self.parent.clipboard_handler.copy_selected_images)
        self.parent.copy_btn = self.parent.copy_action
        self.parent.edit_menu.addAction(self.parent.copy_action)

        self.parent.cut_action = self._action(
            IC.icon_cut(), tr("Ausschneiden (Strg+X)"),
            self.parent.clipboard_handler.cut_selected_images)
        self.parent.cut_btn = self.parent.cut_action
        self.parent.edit_menu.addAction(self.parent.cut_action)

        self.parent.paste_action = self._action(
            QIcon.fromTheme("edit-paste"), tr("Einfügen (Strg+V)"),
            self.parent.clipboard_handler.paste_images_from_clipboard)
        self.parent.edit_menu.addAction(self.parent.paste_action)

        self.parent.edit_menu.addSeparator()

        self.parent.crop_action = self._action(
            IC.icon_crop(), tr("Bild zuschneiden (Taste c)"),
            self.parent.image_ops.start_crop_mode)
        self.parent.crop_btn = self.parent.crop_action
        self.parent.edit_menu.addAction(self.parent.crop_action)

        self.parent.resize_action = self._action(
            IC.icon_resize(), tr("Bildgröße ändern (Taste a)"),
            self.parent.image_ops.resize_current_image)
        self.parent.resize_btn = self.parent.resize_action
        self.parent.edit_menu.addAction(self.parent.resize_action)

        self.parent.rotate_action = self._action(
            IC.icon_rotate(), tr("Bild drehen (Taste d)"),
            self.parent.image_ops.rotate_current_image)
        self.parent.rotate_btn = self.parent.rotate_action
        self.parent.edit_menu.addAction(self.parent.rotate_action)

        # Schnelle Transformationen (sofort, ohne Dialog, mit Undo)
        self.parent.rotate_left_action = self._action(
            IC.icon_rotate_left(), tr("90° links drehen"),
            self.parent.image_ops.rotate_left_90, shortcut=QKeySequence("Ctrl+Left"))
        self.parent.rotate_left_btn = self.parent.rotate_left_action
        self.parent.edit_menu.addAction(self.parent.rotate_left_action)

        self.parent.rotate_right_action = self._action(
            IC.icon_rotate_right(), tr("90° rechts drehen"),
            self.parent.image_ops.rotate_right_90, shortcut=QKeySequence("Ctrl+Right"))
        self.parent.rotate_right_btn = self.parent.rotate_right_action
        self.parent.edit_menu.addAction(self.parent.rotate_right_action)

        self.parent.flip_h_action = self._action(
            IC.icon_flip_h(), tr("Horizontal spiegeln"),
            self.parent.image_ops.flip_horizontal, shortcut=QKeySequence("Ctrl+Shift+H"))
        self.parent.flip_h_btn = self.parent.flip_h_action
        self.parent.edit_menu.addAction(self.parent.flip_h_action)

        self.parent.flip_v_action = self._action(
            IC.icon_flip_v(), tr("Vertikal spiegeln"),
            self.parent.image_ops.flip_vertical, shortcut=QKeySequence("Ctrl+Shift+V"))
        self.parent.flip_v_btn = self.parent.flip_v_action
        self.parent.edit_menu.addAction(self.parent.flip_v_action)

        self.parent.adjust_action = self._action(
            IC.icon_adjust(), tr("Bild anpassen… (Taste b)"),
            self.parent.image_ops.adjust_current_image)
        self.parent.adjust_btn = self.parent.adjust_action
        self.parent.edit_menu.addAction(self.parent.adjust_action)

        self.parent.edit_menu.addSeparator()

        self.parent.delete_action = self._action(
            IC.icon_delete(), tr("Datei löschen (Taste del)"),
            self.parent.delete_selected_image, shortcut=QKeySequence.StandardKey.Delete)  # Entf
        self.parent.delete_btn = self.parent.delete_action
        self.parent.edit_menu.addAction(self.parent.delete_action)

        # ----------------------------------------------------------------
        # Menü: Ansicht  (Ansichten, Zoom, Vollbild, Slideshow, Suche, EXIF)
        # ----------------------------------------------------------------
        self.parent.view_menu = self.parent.menubar.addMenu(tr("&Ansicht"))

        # Viewer / Galerie / Liste: exklusive Gruppe, damit immer nur genau
        # eine Ansicht als aktiv markiert ist - sowohl im Menü als auch in
        # der Toolbar (gleiche Action-Objekte, s. create_toolbar).
        self.parent.view_switch_group = QActionGroup(self.parent)
        self.parent.view_switch_group.setExclusive(True)

        self.parent.viewer_action = self._action(
            IC.icon_viewer(), tr("Bildanzeige (Taste v)"),
            lambda: self.parent.switch_view(0),
            tooltip=tr("Zur Bildanzeige wechseln"), checkable=True, checked=True)
        self.parent.viewer_view_btn = self.parent.viewer_action
        self.parent.view_switch_group.addAction(self.parent.viewer_action)
        self.parent.view_menu.addAction(self.parent.viewer_action)

        # Hinweis: Im Original riefen Menü und Toolbar für Galerie/Liste
        # zwei unterschiedliche Methoden auf (switch_view(N) vs. die
        # dedizierten Handler show_gallery()/toggle_list_view()). Hier wird
        # einheitlich der dedizierte Handler verwendet, da er vermutlich
        # zusätzliche Vorbereitung (Laden/Aktualisieren) übernimmt. Falls
        # switch_view(N) bewusst der "leichtgewichtigere" Weg sein soll,
        # bitte Bescheid geben.
        self.parent.gallery_action = self._action(
            IC.icon_gallery(), tr("Galerie öffnen (Taste g)"),
            self.parent.gallery_handler.show_gallery,
            tooltip=tr("Galerie öffnen (Taste g)"), checkable=True)
        self.parent.gallery_btn = self.parent.gallery_action
        self.parent.view_switch_group.addAction(self.parent.gallery_action)
        self.parent.view_menu.addAction(self.parent.gallery_action)

        self.parent.list_view_action = self._action(
            IC.icon_list_view(), tr("Listenansicht (Taste l)"),
            self.parent.toggle_list_view,
            tooltip=tr("Listenansicht (Taste l)"), checkable=True)
        self.parent.list_view_btn = self.parent.list_view_action
        self.parent.view_switch_group.addAction(self.parent.list_view_action)
        self.parent.view_menu.addAction(self.parent.list_view_action)

        self.parent.view_menu.addSeparator()

        self.parent.zoom_action = self._action(
            IC.icon_zoom(), tr("Zoom-Modus (Taste z)"),
            self.parent.zoom_handler.toggle_zoom_mode, checkable=True)
        self.parent.zoom_btn = self.parent.zoom_action
        self.parent.view_menu.addAction(self.parent.zoom_action)

        self.parent.zoom_in_action = self._action(
            IC.icon_zoom_in(), tr("Vergrößern (+)"), self.parent.zoom_handler.zoom_in)
        self.parent.zoom_in_btn = self.parent.zoom_in_action
        self.parent.view_menu.addAction(self.parent.zoom_in_action)

        self.parent.zoom_out_action = self._action(
            IC.icon_zoom_out(), tr("Verkleinern (−)"), self.parent.zoom_handler.zoom_out)
        self.parent.zoom_out_btn = self.parent.zoom_out_action
        self.parent.view_menu.addAction(self.parent.zoom_out_action)

        self.parent.zoom_fit_action = self._action(
            IC.icon_zoom_fit(), tr("An Fenster anpassen (0)"), self.parent.zoom_handler.zoom_to_fit)
        self.parent.zoom_fit_btn = self.parent.zoom_fit_action
        self.parent.view_menu.addAction(self.parent.zoom_fit_action)

        self.parent.zoom_actual_action = self._action(
            IC.icon_zoom_actual(), tr("Originalgröße 100 % (1)"), self.parent.zoom_handler.zoom_actual)
        self.parent.zoom_actual_btn = self.parent.zoom_actual_action
        self.parent.view_menu.addAction(self.parent.zoom_actual_action)

        self.parent.fullscreen_action = self._action(
            IC.icon_fullscreen(), tr("Vollbild (Taste v)"),
            self.parent.toggle_fullscreen, shortcut=QKeySequence("F11"))
        self.parent.fullscreen_btn = self.parent.fullscreen_action
        self.parent.view_menu.addAction(self.parent.fullscreen_action)

        self.parent.slideshow_action = self._action(
            IC.icon_slideshow_play(), tr("Slideshow starten (Taste p)"),
            self.parent.slideshow_handler.toggle_slideshow)
        self.parent.slideshow_btn = self.parent.slideshow_action
        # Icons für den dynamischen Wechsel Play/Stop (siehe slideshow_handler)
        self.parent.slideshow_play_icon = IC.icon_slideshow_play()
        self.parent.slideshow_stop_icon = IC.icon_slideshow_stop()
        self.parent.view_menu.addAction(self.parent.slideshow_action)

        self.parent.view_menu.addSeparator()

        self.parent.search_action = self._action(
            IC.icon_search(), tr("Suchen (Taste f)"),
            self.parent.search_handler.open_search_dialog,
            shortcut=QKeySequence.StandardKey.Find)  # Strg+F
        self.parent.search_btn = self.parent.search_action
        self.parent.view_menu.addAction(self.parent.search_action)

        self.parent.exif_action = self._action(
            None, tr("EXIF-Daten anzeigen (Taste e)"), self.parent.exif_handler.show_exif_data)
        self.parent.view_menu.addAction(self.parent.exif_action)

        # ----------------------------------------------------------------
        # Menü: Hilfe
        # ----------------------------------------------------------------
        self.parent.help_menu = self.parent.menubar.addMenu(tr("&Hilfe"))
        self.parent.shortcuts_action = self._action(
            None, tr("⌨️ Tastaturkürzel (Taste h / ?)"), self.parent.help_handler.show_shortcuts,
            shortcuts=[QKeySequence("H"), QKeySequence(QKeySequence.StandardKey.HelpContents)])  # F1
        self.parent.help_menu.addAction(self.parent.shortcuts_action)
        self.parent.help_menu.addSeparator()
        self.parent.about_action = self._action(
            None, tr("ℹ️ Über VostiraView"), self.parent.help_handler.show_about)
        self.parent.help_menu.addAction(self.parent.about_action)

    def _build_sort_menu(self):
        """Baut das Sortier-Untermenü einmalig auf. Wird sowohl als
        Untermenü im Datei-Menü als auch als Dropdown des Toolbar-
        Sortierbuttons verwendet (siehe create_toolbar)."""
        menu = QMenu(tr("Bilder sortieren"), self.parent)
        sort_options = [
            ("↑ " + tr("Name"), "name", "asc"),
            ("↓ " + tr("Name"), "name", "desc"),
            ("↑ " + tr("Datum"), "date", "asc"),
            ("↓ " + tr("Datum"), "date", "desc"),
            ("↑ " + tr("Größe"), "size", "asc"),
            ("↓ " + tr("Größe"), "size", "desc"),
        ]
        for label, criterion, order in sort_options:
            action = QAction(label, self.parent)
            action.triggered.connect(
                lambda checked=False, c=criterion, o=order: self.parent.file_ops.sort_images(c, o))
            menu.addAction(action)
        return menu

    def create_toolbar(self):
        self.parent.toolbar = QToolBar(tr("Hauptwerkzeuge"))
        self.parent.addToolBar(self.parent.toolbar)

        # Rückgängig / Wiederholen (dieselben Actions wie im Menü Bearbeiten,
        # damit Status und Tooltip automatisch synchron bleiben)
        self.parent.toolbar.addAction(self.parent.undo_action)
        self.parent.toolbar.addAction(self.parent.redo_action)
        self.parent.toolbar.addSeparator()

        # Navigation
        self.parent.prev_btn = self._action(
            IC.icon_prev(), tr("Vorheriges Bild (←)"),
            lambda: self.parent.image_loader.navigate_image(-1))
        self.parent.toolbar.addAction(self.parent.prev_btn)

        self.parent.next_btn = self._action(
            IC.icon_next(), tr("Nächstes Bild (→)"),
            lambda: self.parent.image_loader.navigate_image(1))
        self.parent.toolbar.addAction(self.parent.next_btn)

        # Slideshow: dieselbe Action wie im Ansicht-Menü (s. create_menu)
        self.parent.toolbar.addAction(self.parent.slideshow_action)

        # fullscreen_action wurde bereits in create_menu() erzeugt
        self.parent.toolbar.addAction(self.parent.fullscreen_action)

        self.parent.toolbar.addSeparator()

        # Ansichten (gleiche, exklusiv gruppierte Actions wie im Ansicht-Menü)
        self.parent.toolbar.addAction(self.parent.viewer_action)
        self.parent.toolbar.addAction(self.parent.gallery_action)
        self.parent.toolbar.addAction(self.parent.list_view_action)
        self.parent.toolbar.addAction(self.parent.search_action)

        self.parent.toolbar.addSeparator()

        # Datei (immer sichtbar)
        self.parent.toolbar.addAction(self.parent.save_as_action)
        self.parent.toolbar.addAction(self.parent.rename_action)

        self.parent.toolbar.addSeparator()

        self.parent.toolbar.addAction(self.parent.copy_action)
        self.parent.toolbar.addAction(self.parent.cut_action)
        self.parent.toolbar.addAction(self.parent.delete_action)

        self.parent.toolbar.addSeparator()

        # Bearbeitung (nur Viewer)
        self.parent.toolbar.addAction(self.parent.crop_action)
        self.parent.toolbar.addAction(self.parent.resize_action)
        self.parent.toolbar.addAction(self.parent.rotate_action)

        # Schnelle Transformationen
        self.parent.toolbar.addAction(self.parent.rotate_left_action)
        self.parent.toolbar.addAction(self.parent.rotate_right_action)
        self.parent.toolbar.addAction(self.parent.flip_h_action)
        self.parent.toolbar.addAction(self.parent.flip_v_action)
        self.parent.toolbar.addAction(self.parent.adjust_action)

        self.parent.toolbar.addAction(self.parent.zoom_action)
        self.parent.toolbar.addAction(self.parent.zoom_in_action)
        self.parent.toolbar.addAction(self.parent.zoom_out_action)
        self.parent.toolbar.addAction(self.parent.zoom_fit_action)
        self.parent.toolbar.addAction(self.parent.zoom_actual_action)

        self.parent.toolbar.addSeparator()

        # Sortierung: Dropdown-Button, der dasselbe Sortier-Menü öffnet wie
        # im Datei-Menü (keine zweite Kopie der 6 Sortier-Actions mehr).
        self.parent.sort_btn = self._action(IC.icon_sort(), tr("Sortieren"), None)
        self.parent.sort_btn.setMenu(self.parent.sort_menu)
        self.parent.toolbar.addAction(self.parent.sort_btn)
