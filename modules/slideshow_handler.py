from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox


class SlideshowHandler:
    def __init__(self, parent, interval=3000):
        self.parent = parent
        self.interval = interval
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_image)
        self.active = False

    def toggle_slideshow(self):
        if self.active:
            self.stop_slideshow()
        else:
            self.start_slideshow()

    def start_slideshow(self):
        if not self.parent.image_loader.image_paths:
            QMessageBox.warning(self.parent, "Keine Bilder", "Es sind keine Bilder zum Anzeigen vorhanden.")
            return
        self.active = True
        self.timer.start(self.interval)
        # Icon in der Toolbar aktualisieren (falls vorhanden)
        if hasattr(self.parent, 'slideshow_btn'):
            self.parent.slideshow_btn.setIcon(self.parent.slideshow_stop_icon)
            self.parent.slideshow_btn.setText("Slideshow stoppen")
        self.parent.statusBar.showMessage("Slideshow gestartet", 2000)

    def stop_slideshow(self):
        self.active = False
        self.timer.stop()
        if hasattr(self.parent, 'slideshow_btn'):
            self.parent.slideshow_btn.setIcon(self.parent.slideshow_play_icon)
            self.parent.slideshow_btn.setText("Slideshow starten")
        self.parent.statusBar.showMessage("Slideshow gestoppt", 2000)

    def next_image(self):
        self.parent.image_loader.navigate_image(1)

    def set_interval(self, interval_ms):
        self.interval = interval_ms
        if self.active:
            self.timer.stop()
            self.timer.start(self.interval)