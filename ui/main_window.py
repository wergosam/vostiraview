from PyQt6.QtWidgets import QToolBar, QLabel, QMenu, QSizePolicy
from PyQt6.QtGui import QAction, QIcon, QPixmap, QKeySequence
from PyQt6.QtCore import Qt
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icons as IC
from i18n import tr


class MainWindowUI:
    def __init__(self, parent):
        self.parent = parent

    def create_menu(self):
        self.parent.menubar = self.parent.menuBar()

        # ----------------------------------------------------------------
        # Menü: Datei  (Öffnen, Speichern, Sortieren, Einstellungen, Beenden)
        # ----------------------------------------------------------------
        self.parent.file_menu = self.parent.menubar.addMenu(tr("&Datei"))

        self.parent.open_action = QAction(QIcon.fromTheme("document-open"), tr("Datei öffnen (Taste o)"), self.parent)
        self.parent.open_action.setShortcut(QKeySequence.StandardKey.Open)  # Strg+O
        self.parent.open_action.triggered.connect(self.parent.image_loader.open_file)
        self.parent.file_menu.addAction(self.parent.open_action)

        self.parent.select_dir_action = QAction(QIcon.fromTheme("folder-open"), tr("Bildverzeichnis wählen"), self.parent)
        self.parent.select_dir_action.triggered.connect(self.parent.image_loader.change_directory)
        self.parent.file_menu.addAction(self.parent.select_dir_action)

        self.parent.recent_menu = self.parent.file_menu.addMenu(QIcon.fromTheme("document-open-recent"), tr("Zuletzt verwendet"))
        self.parent.recent_menu.aboutToShow.connect(self.parent.populate_recent_menu)

        self.parent.file_menu.addSeparator()

        self.parent.save_as_action = QAction(IC.icon_save_as(), tr("Speichern unter (Taste s)"), self.parent)
        self.parent.save_as_action.setShortcuts([
            QKeySequence(QKeySequence.StandardKey.Save),      # Strg+S
            QKeySequence(QKeySequence.StandardKey.SaveAs),    # Strg+Shift+S
        ])
        self.parent.save_as_action.triggered.connect(self.parent.file_ops.save_image_as)
        self.parent.file_menu.addAction(self.parent.save_as_action)

        self.parent.rename_action = QAction(IC.icon_rename(), tr("Umbenennen (Taste u)"), self.parent)
        self.parent.rename_action.setShortcut(QKeySequence("F2"))
        self.parent.rename_action.triggered.connect(self.parent.rename_selected_image)
        self.parent.file_menu.addAction(self.parent.rename_action)

        self.parent.file_menu.addSeparator()

        self.parent.sort_menu = self.parent.file_menu.addMenu(IC.icon_sort(), tr("Bilder sortieren"))
        sort_name_asc = QAction(tr("Name (aufsteigend)"), self.parent)
        sort_name_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("name", "asc"))
        self.parent.sort_menu.addAction(sort_name_asc)
        sort_name_desc = QAction(tr("Name (absteigend)"), self.parent)
        sort_name_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("name", "desc"))
        self.parent.sort_menu.addAction(sort_name_desc)
        sort_date_asc = QAction(tr("Datum (aufsteigend)"), self.parent)
        sort_date_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("date", "asc"))
        self.parent.sort_menu.addAction(sort_date_asc)
        sort_date_desc = QAction(tr("Datum (absteigend)"), self.parent)
        sort_date_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("date", "desc"))
        self.parent.sort_menu.addAction(sort_date_desc)
        sort_size_asc = QAction(tr("Größe (aufsteigend)"), self.parent)
        sort_size_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("size", "asc"))
        self.parent.sort_menu.addAction(sort_size_asc)
        sort_size_desc = QAction(tr("Größe (absteigend)"), self.parent)
        sort_size_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("size", "desc"))
        self.parent.sort_menu.addAction(sort_size_desc)

        self.parent.move_to_folder_action = QAction(IC.icon_move_folder(), tr("In Ordner verschieben…"), self.parent)
        self.parent.move_to_folder_action.triggered.connect(self.parent.move_selection_to_folder)
        self.parent.file_menu.addAction(self.parent.move_to_folder_action)

        self.parent.copy_to_folder_action = QAction(IC.icon_copy_folder(), tr("In Ordner kopieren…"), self.parent)
        self.parent.copy_to_folder_action.triggered.connect(self.parent.copy_selection_to_folder)
        self.parent.file_menu.addAction(self.parent.copy_to_folder_action)

        self.parent.batch_action = QAction(IC.icon_batch(), tr("Stapelverarbeitung… (Galerie/Liste)"), self.parent)
        self.parent.batch_action.setToolTip(tr("Markierte Bilder konvertieren/verkleinern"))
        self.parent.batch_action.triggered.connect(self.parent.open_batch_processor)
        self.parent.file_menu.addAction(self.parent.batch_action)

        self.parent.file_menu.addSeparator()

        # Einstellungen (neu)
        self.parent.settings_action = QAction(tr("⚙️ Einstellungen"), self.parent)
        self.parent.settings_action.setShortcut(QKeySequence("Ctrl+,"))
        self.parent.settings_action.triggered.connect(self.parent.open_settings)
        self.parent.file_menu.addAction(self.parent.settings_action)

        self.parent.manage_trash_action = QAction(QIcon.fromTheme("user-trash-full"), tr("🗑️ Papierkorb verwalten…"), self.parent)
        self.parent.manage_trash_action.triggered.connect(self.parent.open_trash_manager)
        self.parent.file_menu.addAction(self.parent.manage_trash_action)

        self.parent.empty_trash_action = QAction(QIcon.fromTheme("user-trash"), tr("🗑️ Papierkorb leeren"), self.parent)
        self.parent.empty_trash_action.triggered.connect(self.parent.empty_trash)
        self.parent.file_menu.addAction(self.parent.empty_trash_action)

        self.parent.file_menu.addSeparator()

        self.parent.exit_action = QAction(QIcon.fromTheme("application-exit"), tr("Beenden (Taste x)"), self.parent)
        self.parent.exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        self.parent.exit_action.triggered.connect(self.parent.close)
        self.parent.file_menu.addAction(self.parent.exit_action)

        # ----------------------------------------------------------------
        # Menü: Bearbeiten  (Zwischenablage + Bildbearbeitung + Löschen)
        # ----------------------------------------------------------------
        self.parent.edit_menu = self.parent.menubar.addMenu(tr("&Bearbeiten"))

        # Rückgängig (vorbereitet: nutzt UndoManager; initial deaktiviert,
        # bis eine Operation einen rückgängig machbaren Schritt hinterlegt)
        self.parent.undo_action = QAction(IC.icon_undo(), tr("Rückgängig (Strg+Z)"), self.parent)
        self.parent.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.parent.undo_action.setEnabled(False)
        self.parent.undo_action.triggered.connect(self.parent.undo_last_action)
        self.parent.edit_menu.addAction(self.parent.undo_action)

        self.parent.redo_action = QAction(IC.icon_redo(), tr("Wiederholen (Strg+Y)"), self.parent)
        self.parent.redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        self.parent.redo_action.setEnabled(False)
        self.parent.redo_action.triggered.connect(self.parent.redo_last_action)
        self.parent.edit_menu.addAction(self.parent.redo_action)

        self.parent.edit_menu.addSeparator()

        self.parent.copy_action = QAction(IC.icon_copy(), tr("Kopieren (Strg+C)"), self.parent)
        self.parent.copy_action.triggered.connect(self.parent.clipboard_handler.copy_selected_images)
        self.parent.edit_menu.addAction(self.parent.copy_action)

        self.parent.cut_action = QAction(IC.icon_cut(), tr("Ausschneiden (Strg+X)"), self.parent)
        self.parent.cut_action.triggered.connect(self.parent.clipboard_handler.cut_selected_images)
        self.parent.edit_menu.addAction(self.parent.cut_action)

        self.parent.paste_action = QAction(QIcon.fromTheme("edit-paste"), tr("Einfügen (Strg+V)"), self.parent)
        self.parent.paste_action.triggered.connect(self.parent.clipboard_handler.paste_images_from_clipboard)
        self.parent.edit_menu.addAction(self.parent.paste_action)

        self.parent.edit_menu.addSeparator()

        self.parent.crop_action = QAction(IC.icon_crop(), tr("Bild zuschneiden (Taste c)"), self.parent)
        self.parent.crop_action.triggered.connect(self.parent.image_ops.start_crop_mode)
        self.parent.edit_menu.addAction(self.parent.crop_action)

        self.parent.resize_action = QAction(IC.icon_resize(), tr("Bildgröße ändern (Taste a)"), self.parent)
        self.parent.resize_action.triggered.connect(self.parent.image_ops.resize_current_image)
        self.parent.edit_menu.addAction(self.parent.resize_action)

        self.parent.rotate_action = QAction(IC.icon_rotate(), tr("Bild drehen (Taste d)"), self.parent)
        self.parent.rotate_action.triggered.connect(self.parent.image_ops.rotate_current_image)
        self.parent.edit_menu.addAction(self.parent.rotate_action)

        # Schnelle Transformationen (sofort, ohne Dialog, mit Undo)
        self.parent.rotate_left_action = QAction(IC.icon_rotate_left(), tr("90° links drehen"), self.parent)
        self.parent.rotate_left_action.setShortcut(QKeySequence("Ctrl+Left"))
        self.parent.rotate_left_action.triggered.connect(self.parent.image_ops.rotate_left_90)
        self.parent.edit_menu.addAction(self.parent.rotate_left_action)

        self.parent.rotate_right_action = QAction(IC.icon_rotate_right(), tr("90° rechts drehen"), self.parent)
        self.parent.rotate_right_action.setShortcut(QKeySequence("Ctrl+Right"))
        self.parent.rotate_right_action.triggered.connect(self.parent.image_ops.rotate_right_90)
        self.parent.edit_menu.addAction(self.parent.rotate_right_action)

        self.parent.flip_h_action = QAction(IC.icon_flip_h(), tr("Horizontal spiegeln"), self.parent)
        self.parent.flip_h_action.setShortcut(QKeySequence("Ctrl+Shift+H"))
        self.parent.flip_h_action.triggered.connect(self.parent.image_ops.flip_horizontal)
        self.parent.edit_menu.addAction(self.parent.flip_h_action)

        self.parent.flip_v_action = QAction(IC.icon_flip_v(), tr("Vertikal spiegeln"), self.parent)
        self.parent.flip_v_action.setShortcut(QKeySequence("Ctrl+Shift+V"))
        self.parent.flip_v_action.triggered.connect(self.parent.image_ops.flip_vertical)
        self.parent.edit_menu.addAction(self.parent.flip_v_action)

        self.parent.adjust_action = QAction(IC.icon_adjust(), tr("Bild anpassen… (Taste b)"), self.parent)
        self.parent.adjust_action.triggered.connect(self.parent.image_ops.adjust_current_image)
        self.parent.edit_menu.addAction(self.parent.adjust_action)

        self.parent.edit_menu.addSeparator()

        self.parent.delete_action = QAction(IC.icon_delete(), tr("Datei löschen (Taste del)"), self.parent)
        self.parent.delete_action.setShortcut(QKeySequence.StandardKey.Delete)  # Entf
        self.parent.delete_action.triggered.connect(self.parent.delete_selected_image)
        self.parent.edit_menu.addAction(self.parent.delete_action)

        # ----------------------------------------------------------------
        # Menü: Ansicht  (Ansichten, Zoom, Vollbild, Slideshow, Suche, EXIF)
        # ----------------------------------------------------------------
        self.parent.view_menu = self.parent.menubar.addMenu(tr("&Ansicht"))

        self.parent.viewer_action = QAction(IC.icon_viewer(), tr("Bildanzeige"), self.parent)
        self.parent.viewer_action.setToolTip(tr("Zur Bildanzeige wechseln"))
        self.parent.viewer_action.triggered.connect(lambda: self.parent.switch_view(0))
        self.parent.view_menu.addAction(self.parent.viewer_action)

        self.parent.gallery_action = QAction(IC.icon_gallery(), tr("Galerie öffnen (Taste g)"), self.parent)
        self.parent.gallery_action.setToolTip(tr("Galerie öffnen (Taste g)"))
        self.parent.gallery_action.triggered.connect(self.parent.gallery_handler.show_gallery)
        self.parent.view_menu.addAction(self.parent.gallery_action)

        self.parent.list_view_action = QAction(IC.icon_list_view(), tr("Listenansicht (Taste l)"), self.parent)
        self.parent.list_view_action.setToolTip(tr("Listenansicht (Taste l)"))
        self.parent.list_view_action.triggered.connect(self.parent.toggle_list_view)
        self.parent.view_menu.addAction(self.parent.list_view_action)

        self.parent.view_menu.addSeparator()

        self.parent.zoom_action = QAction(IC.icon_zoom(), tr("Zoom-Modus (Taste z)"), self.parent)
        self.parent.zoom_action.setCheckable(True)
        self.parent.zoom_action.triggered.connect(self.parent.zoom_handler.toggle_zoom_mode)
        self.parent.view_menu.addAction(self.parent.zoom_action)

        self.parent.zoom_in_action = QAction(IC.icon_zoom_in(), tr("Vergrößern (+)"), self.parent)
        self.parent.zoom_in_action.triggered.connect(self.parent.zoom_handler.zoom_in)
        self.parent.view_menu.addAction(self.parent.zoom_in_action)

        self.parent.zoom_out_action = QAction(IC.icon_zoom_out(), tr("Verkleinern (−)"), self.parent)
        self.parent.zoom_out_action.triggered.connect(self.parent.zoom_handler.zoom_out)
        self.parent.view_menu.addAction(self.parent.zoom_out_action)

        self.parent.zoom_fit_action = QAction(IC.icon_zoom_fit(), tr("An Fenster anpassen (0)"), self.parent)
        self.parent.zoom_fit_action.triggered.connect(self.parent.zoom_handler.zoom_to_fit)
        self.parent.view_menu.addAction(self.parent.zoom_fit_action)

        self.parent.zoom_actual_action = QAction(IC.icon_zoom_actual(), tr("Originalgröße 100 % (1)"), self.parent)
        self.parent.zoom_actual_action.triggered.connect(self.parent.zoom_handler.zoom_actual)
        self.parent.view_menu.addAction(self.parent.zoom_actual_action)

        self.parent.fullscreen_action = QAction(IC.icon_fullscreen(), tr("Vollbild (Taste v)"), self.parent)
        self.parent.fullscreen_action.setShortcut(QKeySequence("F11"))
        self.parent.fullscreen_action.triggered.connect(self.parent.toggle_fullscreen)
        self.parent.view_menu.addAction(self.parent.fullscreen_action)

        self.parent.slideshow_action = QAction(IC.icon_slideshow_play(), tr("Slideshow starten (Taste p)"), self.parent)
        self.parent.slideshow_action.triggered.connect(self.parent.slideshow_handler.toggle_slideshow)
        self.parent.view_menu.addAction(self.parent.slideshow_action)

        self.parent.view_menu.addSeparator()

        self.parent.search_action = QAction(IC.icon_search(), tr("Suchen (Taste f)"), self.parent)
        self.parent.search_action.setShortcut(QKeySequence.StandardKey.Find)  # Strg+F
        self.parent.search_action.triggered.connect(self.parent.search_handler.open_search_dialog)
        self.parent.view_menu.addAction(self.parent.search_action)

        self.parent.exif_action = QAction(tr("EXIF-Daten anzeigen (Taste e)"), self.parent)
        self.parent.exif_action.triggered.connect(self.parent.exif_handler.show_exif_data)
        self.parent.view_menu.addAction(self.parent.exif_action)

        # ----------------------------------------------------------------
        # Menü: Hilfe
        # ----------------------------------------------------------------
        self.parent.help_menu = self.parent.menubar.addMenu(tr("&Hilfe"))
        self.parent.shortcuts_action = QAction(tr("⌨️ Tastaturkürzel (Taste h / ?)"), self.parent)
        self.parent.shortcuts_action.setShortcuts([
            QKeySequence("H"),
            QKeySequence(QKeySequence.StandardKey.HelpContents),  # F1
        ])
        self.parent.shortcuts_action.triggered.connect(self.parent.help_handler.show_shortcuts)
        self.parent.help_menu.addAction(self.parent.shortcuts_action)
        self.parent.help_menu.addSeparator()
        about_action = QAction(tr("ℹ️ Über VostiraView"), self.parent)
        about_action.triggered.connect(self.parent.help_handler.show_about)
        self.parent.help_menu.addAction(about_action)

    def create_toolbar(self):
        self.parent.toolbar = QToolBar(tr("Hauptwerkzeuge"))
        self.parent.addToolBar(self.parent.toolbar)

        # Rückgängig / Wiederholen (dieselben Actions wie im Menü Bearbeiten,
        # damit Status und Tooltip automatisch synchron bleiben)
        self.parent.toolbar.addAction(self.parent.undo_action)
        self.parent.toolbar.addAction(self.parent.redo_action)
        self.parent.toolbar.addSeparator()

        # Navigation
        self.parent.prev_btn = QAction(IC.icon_prev(), tr("Vorheriges Bild (←)"), self.parent)
        self.parent.prev_btn.triggered.connect(lambda: self.parent.image_loader.navigate_image(-1))
        self.parent.toolbar.addAction(self.parent.prev_btn)

        self.parent.next_btn = QAction(IC.icon_next(), tr("Nächstes Bild (→)"), self.parent)
        self.parent.next_btn.triggered.connect(lambda: self.parent.image_loader.navigate_image(1))
        self.parent.toolbar.addAction(self.parent.next_btn)

        self.parent.slideshow_play_icon = IC.icon_slideshow_play()
        self.parent.slideshow_stop_icon = IC.icon_slideshow_stop()
        self.parent.slideshow_btn = QAction(self.parent.slideshow_play_icon, tr("Slideshow (p)"), self.parent)
        self.parent.slideshow_btn.triggered.connect(self.parent.slideshow_handler.toggle_slideshow)
        self.parent.toolbar.addAction(self.parent.slideshow_btn)

        self.parent.fullscreen_btn = QAction(IC.icon_fullscreen(), tr("Vollbild (v)"), self.parent)
        self.parent.fullscreen_btn.triggered.connect(self.parent.toggle_fullscreen)
        self.parent.toolbar.addAction(self.parent.fullscreen_btn)

        self.parent.toolbar.addSeparator()

        # Ansichten
        self.parent.viewer_view_btn = QAction(IC.icon_viewer(), tr("Bildanzeige (v)"), self.parent)
        self.parent.viewer_view_btn.setCheckable(True)
        self.parent.viewer_view_btn.setChecked(True)
        self.parent.viewer_view_btn.triggered.connect(lambda: self.parent.switch_view(0))
        self.parent.toolbar.addAction(self.parent.viewer_view_btn)

        self.parent.gallery_btn = QAction(IC.icon_gallery(), tr("Galerieansicht (g)"), self.parent)
        self.parent.gallery_btn.setCheckable(True)
        self.parent.gallery_btn.triggered.connect(lambda: self.parent.switch_view(1))
        self.parent.toolbar.addAction(self.parent.gallery_btn)

        self.parent.list_view_btn = QAction(IC.icon_list_view(), tr("Listenansicht (l)"), self.parent)
        self.parent.list_view_btn.setCheckable(True)
        self.parent.list_view_btn.triggered.connect(lambda: self.parent.switch_view(3))
        self.parent.toolbar.addAction(self.parent.list_view_btn)

        self.parent.search_btn = QAction(IC.icon_search(), tr("Suche (f)"), self.parent)
        self.parent.search_btn.triggered.connect(self.parent.search_handler.open_search_dialog)
        self.parent.toolbar.addAction(self.parent.search_btn)

        self.parent.toolbar.addSeparator()

        # Datei (immer sichtbar)
        self.parent.save_as_btn = QAction(IC.icon_save_as(), tr("Speichern unter (s)"), self.parent)
        self.parent.save_as_btn.triggered.connect(self.parent.file_ops.save_image_as)
        self.parent.toolbar.addAction(self.parent.save_as_btn)

        self.parent.rename_btn = QAction(IC.icon_rename(), tr("Umbenennen (u)"), self.parent)
        self.parent.rename_btn.triggered.connect(self.parent.rename_selected_image)
        self.parent.toolbar.addAction(self.parent.rename_btn)

        self.parent.toolbar.addSeparator()

        self.parent.copy_btn = QAction(IC.icon_copy(), tr("Kopieren (Ctrl+C)"), self.parent)
        self.parent.copy_btn.triggered.connect(self.parent.clipboard_handler.copy_selected_images)
        self.parent.toolbar.addAction(self.parent.copy_btn)

        self.parent.cut_btn = QAction(IC.icon_cut(), tr("Ausschneiden (Ctrl+X)"), self.parent)
        self.parent.cut_btn.triggered.connect(self.parent.clipboard_handler.cut_selected_images)
        self.parent.toolbar.addAction(self.parent.cut_btn)

        self.parent.delete_btn = QAction(IC.icon_delete(), tr("Löschen (Del)"), self.parent)
        self.parent.delete_btn.triggered.connect(self.parent.delete_selected_image)
        self.parent.toolbar.addAction(self.parent.delete_btn)

        self.parent.toolbar.addSeparator()

        # Bearbeitung (nur Viewer)
        self.parent.crop_btn = QAction(IC.icon_crop(), tr("Zuschneiden (c)"), self.parent)
        self.parent.crop_btn.triggered.connect(self.parent.image_ops.start_crop_mode)
        self.parent.toolbar.addAction(self.parent.crop_btn)

        self.parent.resize_btn = QAction(IC.icon_resize(), tr("Größe ändern (a)"), self.parent)
        self.parent.resize_btn.triggered.connect(self.parent.image_ops.resize_current_image)
        self.parent.toolbar.addAction(self.parent.resize_btn)

        self.parent.rotate_btn = QAction(IC.icon_rotate(), tr("Drehen (d)"), self.parent)
        self.parent.rotate_btn.triggered.connect(self.parent.image_ops.rotate_current_image)
        self.parent.toolbar.addAction(self.parent.rotate_btn)

        # Schnelle Transformationen
        self.parent.rotate_left_btn = QAction(IC.icon_rotate_left(), tr("90° links (Strg+←)"), self.parent)
        self.parent.rotate_left_btn.triggered.connect(self.parent.image_ops.rotate_left_90)
        self.parent.toolbar.addAction(self.parent.rotate_left_btn)

        self.parent.rotate_right_btn = QAction(IC.icon_rotate_right(), tr("90° rechts (Strg+→)"), self.parent)
        self.parent.rotate_right_btn.triggered.connect(self.parent.image_ops.rotate_right_90)
        self.parent.toolbar.addAction(self.parent.rotate_right_btn)

        self.parent.flip_h_btn = QAction(IC.icon_flip_h(), tr("Horizontal spiegeln"), self.parent)
        self.parent.flip_h_btn.triggered.connect(self.parent.image_ops.flip_horizontal)
        self.parent.toolbar.addAction(self.parent.flip_h_btn)

        self.parent.flip_v_btn = QAction(IC.icon_flip_v(), tr("Vertikal spiegeln"), self.parent)
        self.parent.flip_v_btn.triggered.connect(self.parent.image_ops.flip_vertical)
        self.parent.toolbar.addAction(self.parent.flip_v_btn)

        self.parent.adjust_btn = QAction(IC.icon_adjust(), tr("Bild anpassen (b)"), self.parent)
        self.parent.adjust_btn.triggered.connect(self.parent.image_ops.adjust_current_image)
        self.parent.toolbar.addAction(self.parent.adjust_btn)

        self.parent.zoom_btn = QAction(IC.icon_zoom(), tr("Zoom-Modus (z)"), self.parent)
        self.parent.zoom_btn.setCheckable(True)
        self.parent.zoom_btn.setChecked(False)
        self.parent.zoom_btn.triggered.connect(self.parent.zoom_handler.toggle_zoom_mode)
        self.parent.toolbar.addAction(self.parent.zoom_btn)

        self.parent.zoom_in_btn = QAction(IC.icon_zoom_in(), tr("Vergrößern (+)"), self.parent)
        self.parent.zoom_in_btn.triggered.connect(self.parent.zoom_handler.zoom_in)
        self.parent.toolbar.addAction(self.parent.zoom_in_btn)

        self.parent.zoom_out_btn = QAction(IC.icon_zoom_out(), tr("Verkleinern (−)"), self.parent)
        self.parent.zoom_out_btn.triggered.connect(self.parent.zoom_handler.zoom_out)
        self.parent.toolbar.addAction(self.parent.zoom_out_btn)

        self.parent.zoom_fit_btn = QAction(IC.icon_zoom_fit(), tr("An Fenster anpassen (0)"), self.parent)
        self.parent.zoom_fit_btn.triggered.connect(self.parent.zoom_handler.zoom_to_fit)
        self.parent.toolbar.addAction(self.parent.zoom_fit_btn)

        self.parent.zoom_actual_btn = QAction(IC.icon_zoom_actual(), tr("Originalgröße 100 % (1)"), self.parent)
        self.parent.zoom_actual_btn.triggered.connect(self.parent.zoom_handler.zoom_actual)
        self.parent.toolbar.addAction(self.parent.zoom_actual_btn)

        self.parent.toolbar.addSeparator()

        # Sortierung
        self.parent.sort_btn = QAction(IC.icon_sort(), tr("Sortieren"), self.parent)
        sort_menu = QMenu(self.parent)
        sort_name_asc = QAction(tr("↑ Name"), self.parent)
        sort_name_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("name", "asc"))
        sort_menu.addAction(sort_name_asc)
        sort_name_desc = QAction(tr("↓ Name"), self.parent)
        sort_name_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("name", "desc"))
        sort_menu.addAction(sort_name_desc)
        sort_date_asc = QAction(tr("↑ Datum"), self.parent)
        sort_date_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("date", "asc"))
        sort_menu.addAction(sort_date_asc)
        sort_date_desc = QAction(tr("↓ Datum"), self.parent)
        sort_date_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("date", "desc"))
        sort_menu.addAction(sort_date_desc)
        sort_size_asc = QAction(tr("↑ Größe"), self.parent)
        sort_size_asc.triggered.connect(lambda: self.parent.file_ops.sort_images("size", "asc"))
        sort_menu.addAction(sort_size_asc)
        sort_size_desc = QAction(tr("↓ Größe"), self.parent)
        sort_size_desc.triggered.connect(lambda: self.parent.file_ops.sort_images("size", "desc"))
        sort_menu.addAction(sort_size_desc)
        self.parent.sort_btn.setMenu(sort_menu)
        self.parent.toolbar.addAction(self.parent.sort_btn)
