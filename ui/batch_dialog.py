"""Dialog für die Stapelverarbeitung (Konvertieren / Verkleinern)."""
import os
import threading
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QHBoxLayout,
                             QComboBox, QCheckBox, QSpinBox, QLineEdit,
                             QPushButton, QLabel, QDialogButtonBox, QProgressDialog,
                             QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, QObject, QEventLoop, pyqtSignal

from modules.image_export import SUPPORTED_FORMATS, get_export_quality
from modules.batch_processor import process_batch
from i18n import tr


class _BatchWorker(QObject):
    """Führt process_batch in einem eigenen Thread aus.

    Dadurch bleibt die GUI während der Verarbeitung responsiv, ohne dass
    QApplication.processEvents() im Hauptthread aufgerufen werden muss
    (das bei langen Stapeln zu Reentrancy-Problemen führen kann, z.B. wenn
    der Nutzer währenddessen andere Aktionen auslöst).
    """

    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int, list)
    error = pyqtSignal(str)

    def __init__(self, paths, output_dir, target_format, max_size, quality):
        super().__init__()
        self._paths = paths
        self._output_dir = output_dir
        self._target_format = target_format
        self._max_size = max_size
        self._quality = quality
        self._cancel_event = threading.Event()

    def cancel(self):
        """Thread-sicher von außen aufrufbar (z.B. aus dem GUI-Thread)."""
        self._cancel_event.set()

    def run(self):
        try:
            ok, failed = process_batch(
                self._paths, self._output_dir,
                target_format=self._target_format,
                max_size=self._max_size,
                quality=self._quality,
                on_progress=lambda done, total: self.progress.emit(done, total),
                should_cancel=self._cancel_event.is_set,
            )
            self.finished.emit(ok, failed)
        except Exception as e:
            self.error.emit(str(e))


class BatchDialog(QDialog):
    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self._paths = paths
        self.setWindowTitle(tr("Stapelverarbeitung"))
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"{len(paths)} " + tr("Bild(er) ausgewählt")))

        form = QFormLayout()

        # Zielformat
        self.format_combo = QComboBox()
        self.format_combo.addItem(tr("Original beibehalten"), None)
        for name, _exts, pil_fmt in SUPPORTED_FORMATS:
            self.format_combo.addItem(name, pil_fmt)
        form.addRow(tr("Zielformat:"), self.format_combo)

        # Größe begrenzen
        size_row = QHBoxLayout()
        self.resize_check = QCheckBox(tr("Längste Seite begrenzen auf"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(16, 20000)
        self.size_spin.setSuffix(" px")
        self.size_spin.setValue(1920)
        self.size_spin.setEnabled(False)
        self.resize_check.toggled.connect(self.size_spin.setEnabled)
        size_row.addWidget(self.resize_check)
        size_row.addWidget(self.size_spin)
        size_row.addStretch(1)
        form.addRow(tr("Größe:"), size_row)

        # Qualität (JPEG/WebP)
        self.quality_spin = QSpinBox()
        self.quality_spin.setRange(1, 100)
        self.quality_spin.setSuffix(" %")
        self.quality_spin.setValue(get_export_quality())
        self.quality_spin.setToolTip(tr("Wirkt nur für JPEG/WebP."))
        form.addRow(tr("Qualität (JPEG/WebP):"), self.quality_spin)

        # Zielordner
        first_dir = os.path.dirname(paths[0]) if paths else os.path.expanduser("~")
        self.out_edit = QLineEdit(os.path.join(first_dir, "konvertiert"))
        browse = QPushButton(tr("Durchsuchen…"))
        browse.clicked.connect(self._browse)
        out_row = QHBoxLayout()
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(browse)
        form.addRow(tr("Zielordner:"), out_row)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("Verarbeiten"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(
            self, tr("Zielordner wählen"), self.out_edit.text() or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly)
        if d:
            self.out_edit.setText(d)

    def options(self):
        return {
            "target_format": self.format_combo.currentData(),
            "max_size": self.size_spin.value() if self.resize_check.isChecked() else None,
            "quality": self.quality_spin.value(),
            "output_dir": self.out_edit.text().strip(),
        }

    @staticmethod
    def _would_overwrite_originals(paths, output_dir, target_format):
        """Prüft, ob die Verarbeitung mit hoher Wahrscheinlichkeit die
        Originaldateien überschreiben würde (gleicher Ordner, gleiches Format)."""
        if target_format is not None:
            return False
        src_dirs = {os.path.dirname(os.path.abspath(p)) for p in paths}
        return os.path.abspath(output_dir) in src_dirs

    @classmethod
    def run(cls, parent, paths):
        """Zeigt den Dialog und führt bei Bestätigung die Stapelverarbeitung aus."""
        dlg = cls(paths, parent)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        opt = dlg.options()
        if not opt["output_dir"]:
            QMessageBox.warning(parent, tr("Stapelverarbeitung"), tr("Bitte einen Zielordner angeben."))
            return

        if cls._would_overwrite_originals(paths, opt["output_dir"], opt["target_format"]):
            reply = QMessageBox.question(
                parent, tr("Stapelverarbeitung"),
                tr("Der Zielordner entspricht dem Quellordner. Vorhandene Originaldateien "
                   "könnten überschrieben werden. Trotzdem fortfahren?"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        progress = QProgressDialog(tr("Verarbeite Bilder…"), tr("Abbrechen"), 0, len(paths), parent)
        progress.setWindowTitle(tr("Stapelverarbeitung"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)

        thread = QThread(parent)
        worker = _BatchWorker(
            paths, opt["output_dir"],
            target_format=opt["target_format"],
            max_size=opt["max_size"],
            quality=opt["quality"],
        )
        worker.moveToThread(thread)

        result = {"ok": 0, "failed": [], "error": None}
        loop = QEventLoop()

        def on_progress(done, total):
            progress.setValue(done)

        def on_finished(ok, failed):
            result["ok"] = ok
            result["failed"] = failed
            loop.quit()

        def on_error(message):
            result["error"] = message
            loop.quit()

        progress.canceled.connect(worker.cancel)
        worker.progress.connect(on_progress)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        thread.started.connect(worker.run)
        thread.start()

        loop.exec()  # blockiert nur diesen Aufruf, GUI bleibt responsiv

        thread.quit()
        thread.wait()
        progress.setValue(len(paths))

        if result["error"] is not None:
            QMessageBox.critical(
                parent, tr("Stapelverarbeitung"),
                tr("Fehler bei der Verarbeitung:") + f"\n{result['error']}"
            )
            return

        ok, failed = result["ok"], result["failed"]
        msg = f"{ok} " + tr("Bild(er) verarbeitet.") + "\n" + tr("Gespeichert in:") + \
            f"\n{opt['output_dir']}"
        if failed:
            msg += f"\n\n{len(failed)} " + tr("fehlgeschlagen:") + "\n" + \
                "\n".join(os.path.basename(p) for p, _ in failed[:10])
            if len(failed) > 10:
                msg += "\n…"
        QMessageBox.information(parent, tr("Stapelverarbeitung abgeschlossen"), msg)
