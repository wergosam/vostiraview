"""Stapelverarbeitung: mehrere Bilder konvertieren und/oder verkleinern.

Nutzt die Speicher-/Konvertierungslogik aus image_export (korrekte Alpha-
Behandlung, Qualität für JPEG/WebP).
"""
import os
from PIL import Image

from modules.image_export import (save_pil_image, get_export_quality,
                                   format_for_extension, SUPPORTED_FORMATS)


def extension_for_format(pil_format):
    """Standard-Dateiendung für einen Pillow-Formatnamen."""
    for _name, exts, fmt in SUPPORTED_FORMATS:
        if fmt == pil_format:
            return exts[0]
    return None


def _unique_path(path):
    """Hängt bei Bedarf _1, _2 … an, um vorhandene Dateien nicht zu überschreiben."""
    if not os.path.exists(path):
        return path
    base, ext = os.path.splitext(path)
    i = 1
    while True:
        candidate = f"{base}_{i}{ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1


def process_batch(paths, output_dir, target_format=None, max_size=None,
                  quality=None, on_progress=None, should_cancel=None):
    """Konvertiert/verkleinert Bilder im Stapel.

    target_format: Pillow-Format (z. B. 'JPEG') oder None = Originalformat behalten.
    max_size:      längste Seite in Pixeln oder None = Größe unverändert.
    quality:       für JPEG/WebP; None = Wert aus den Einstellungen.

    Gibt (anzahl_erfolg, fehler_liste) zurück; fehler_liste enthält
    (pfad, fehlertext)-Tupel.
    """
    os.makedirs(output_dir, exist_ok=True)
    if quality is None:
        quality = get_export_quality()

    ok = 0
    failed = []
    total = len(paths)
    for i, src in enumerate(paths):
        if should_cancel and should_cancel():
            break
        try:
            base = os.path.splitext(os.path.basename(src))[0]
            src_ext = os.path.splitext(src)[1]
            if target_format:
                fmt = target_format
                out_ext = extension_for_format(fmt)
            else:
                fmt = format_for_extension(src_ext) or "PNG"
                out_ext = src_ext.lstrip(".").lower() or "png"

            with Image.open(src) as img:
                if max_size and max(img.size) > max_size:
                    img.thumbnail((max_size, max_size), Image.LANCZOS)
                dst = _unique_path(os.path.join(output_dir, f"{base}.{out_ext}"))
                save_pil_image(img, dst, fmt, quality)

            ok += 1
            if on_progress:
                on_progress(i + 1, total)
        except Exception as e:
            failed.append((src, str(e)))
            if on_progress:
                on_progress(i + 1, total)

    return ok, failed
