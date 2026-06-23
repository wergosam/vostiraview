import os
from PyQt6.QtWidgets import QMessageBox
from utils import resource_path


class GalleryHandler:
    """Verwaltet die Galerie-Interaktion."""
    
    def __init__(self, parent):
        self.parent = parent
        
    def show_gallery(self):
        """Wechselt zwischen ImageViewer und Galerie."""
        current_index = self.parent.stacked_widget.currentIndex()

        if current_index == 0:  # Wechsel zur Galerie
            self.parent.gallery_widget.MAX_COLUMNS = self.parent.gallery_widget.calculate_columns()
            self.parent.gallery_widget.rearrange_gallery()
            self.parent.image_info_label.hide()
            self.parent.stacked_widget.setCurrentIndex(1)
            self.parent.gallery_btn.setText("Bildanzeige öffnen")
        else:  # Zurück zum ImageViewer
            self.parent.gallery_widget.MAX_COLUMNS = self.parent.gallery_widget.default_columns
            self.parent.gallery_widget.rearrange_gallery()
            self.parent.image_info_label.show()
            self.parent.stacked_widget.setCurrentIndex(0)
            self.parent.gallery_btn.setText("Galerie öffnen")

        self.parent.update_toolbar_buttons()
        self.parent.update_menu_items()
        
    def handle_gallery_image_click(self, image_path):
        """Bild aus Galerie anzeigen & zurück zum Viewer wechseln."""
        current_sort_criterion = getattr(self.parent, 'current_sort_criterion', 'name')
        self.parent.image_loader.update_directory(self.parent.image_loader.image_directory)
        self.parent.gallery_widget.update_directory(
            self.parent.image_loader.image_directory, current_sort_criterion
        )

        if image_path and os.path.exists(image_path):
            if image_path in self.parent.image_loader.image_paths:
                self.parent.image_loader.current_index = self.parent.image_loader.image_paths.index(image_path)
            else:
                self.parent.image_loader.image_paths.append(image_path)
                self.parent.image_loader.current_index = len(self.parent.image_loader.image_paths) - 1

            self.parent.image_loader.load_image(resource_path(image_path))
            self.parent.stacked_widget.setCurrentIndex(0)