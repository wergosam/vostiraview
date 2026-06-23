"""Bild-Export / Format-Konvertierung für VostiraView.

Stellt die unterstützten Speicherformate bereit und speichert Bilder
formatgerecht über Pillow (inkl. korrekter Behandlung von Transparenz für
Formate ohne Alpha-Kanal wie JPEG/BMP). Quelle kann eine Datei, ein PIL-Bild
oder eine QPixmap sein.
"""
import os
import io
from PIL import Image
from PyQt6.QtCore import QBuffer

from config import load_config

# (Anzeigename, [Erweiterungen ohne Punkt], Pillow-Formatname)
SUPPORTED_FORMATS = [
    ("PNG", ["png"], "PNG"),
    ("JPEG", ["jpg", "jpeg"], "JPEG"),
    ("WebP", ["webp"], "WEBP"),
    ("BMP", ["bmp"], "BMP"),
    ("GIF", ["gif"], "GIF"),
    ("TIFF", ["tif", "tiff"], "TIFF"),
    ("ICO", ["ico"], "ICO"),
]

# Formate ohne Alpha-Unterstützung -> vor dem Speichern nach RGB wandeln
_NO_ALPHA = {"JPEG", "BMP"}


def get_export_quality():
    """Qualität (1–100) für verlustbehaftete Formate (JPEG/WebP) aus der Config."""
    try:
        q = int(load_config().get("export_quality", 95))
    except (TypeError, ValueError):
        return 95
    return max(1, min(100, q))


def build_filter_string():
    """Baut den Qt-Filter-String für den Speichern-Dialog (alle Formate)."""
    all_exts = []
    parts = []
    for name, exts, _ in SUPPORTED_FORMATS:
        pattern = " ".join(f"*.{e}" for e in exts)
        parts.append(f"{name} ({pattern})")
        all_exts.extend(f"*.{e}" for e in exts)
    combined = f"Alle unterstützten Bilder ({' '.join(all_exts)})"
    return ";;".join([combined] + parts)


def format_for_extension(ext):
    """Pillow-Formatname für eine Dateiendung oder None."""
    ext = ext.lower().lstrip(".")
    for _name, exts, pil_fmt in SUPPORTED_FORMATS:
        if ext in exts:
            return pil_fmt
    return None


def primary_extension_for_filter(selected_filter):
    """Standard-Endung für einen ausgewählten Filter (z. B. 'JPEG (...)' -> 'jpg')."""
    for name, exts, _ in SUPPORTED_FORMATS:
        if selected_filter.startswith(name + " "):
            return exts[0]
    return None


def ensure_extension(file_path, selected_filter):
    """Hängt eine passende Endung an, falls im Pfad keine vorhanden ist.

    Gibt (pfad, endung_mit_punkt) zurück.
    """
    ext = os.path.splitext(file_path)[1]
    if ext:
        return file_path, ext
    primary = primary_extension_for_filter(selected_filter)
    if primary:
        return f"{file_path}.{primary}", f".{primary}"
    return file_path, ext


def same_format(src_ext, dst_ext):
    """True, wenn Quell- und Zielendung dasselbe Format meinen (jpg == jpeg)."""
    src = format_for_extension(src_ext)
    dst = format_for_extension(dst_ext)
    return src is not None and src == dst


def _prepare(img, pil_format):
    """Bereitet ein PIL-Bild für das Zielformat vor (Alpha-Behandlung)."""
    if pil_format in _NO_ALPHA:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")
    return img


def save_pil_image(img, dst_path, pil_format, quality=None):
    """Speichert ein PIL-Bild im angegebenen Format (mit Alpha-Behandlung/Qualität)."""
    if pil_format is None:
        pil_format = "PNG"
    if quality is None:
        quality = get_export_quality()
    img = _prepare(img, pil_format)
    save_kwargs = {}
    if pil_format in ("JPEG", "WEBP"):
        save_kwargs["quality"] = quality
    img.save(dst_path, format=pil_format, **save_kwargs)


def convert_and_save(src_path, dst_path, pil_format, quality=None):
    """Konvertiert eine Bilddatei und speichert sie im angegebenen Format."""
    save_pil_image(Image.open(src_path), dst_path, pil_format, quality)


def save_pixmap_as(pixmap, dst_path, pil_format, quality=None):
    """Speichert eine QPixmap formatgerecht (z. B. nach Rotate/Crop).

    Die QPixmap wird verlustfrei über PNG nach PIL überführt (Alpha bleibt
    erhalten) und dann im Zielformat gespeichert. Gibt True bei Erfolg zurück.
    """
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.ReadWrite)
    if not pixmap.save(buffer, "PNG"):
        buffer.close()
        return False
    data = bytes(buffer.data())
    buffer.close()
    try:
        img = Image.open(io.BytesIO(data)).copy()
        save_pil_image(img, dst_path, pil_format, quality)
        return True
    except Exception as e:
        print(f"Fehler beim Speichern von {dst_path}: {e}")
        return False
