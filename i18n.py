"""Leichtgewichtige Mehrsprachigkeit für VostiraView.

Der deutsche Originaltext dient als Schlüssel. `tr(text)` liefert die
Übersetzung der aktuellen Sprache oder – falls keine vorhanden – den
deutschen Originaltext (keine Lücken). Neue Sprachen/Strings lassen sich
durch Ergänzen von _TRANSLATIONS hinzufügen.
"""

_lang = "de"

_LANGUAGES = [("de", "Deutsch"), ("en", "English")]
_LANGUAGE_CODES = {code for code, _ in _LANGUAGES}


def available_languages():
    """Liste (code, Anzeigename) der verfügbaren Sprachen."""
    return _LANGUAGES


def set_language(code):
    global _lang
    _lang = code if code in _LANGUAGE_CODES else "de"


def get_language():
    return _lang


def init_language():
    """Lädt die Sprache aus der Konfiguration (beim Programmstart aufrufen)."""
    try:
        from config import load_config
        set_language(load_config().get("language", "de"))
    except Exception:
        set_language("de")


def tr(text):
    """Übersetzt einen deutschen Originaltext in die aktuelle Sprache."""
    if _lang == "de":
        return text
    return _TRANSLATIONS.get(_lang, {}).get(text, text)


_TRANSLATIONS = {
    "en": {
        # --- Menütitel ---
        "&Datei": "&File",
        "&Bearbeiten": "&Edit",
        "&Ansicht": "&View",
        "&Hilfe": "&Help",
        # --- Datei-Menü ---
        "Datei öffnen (Taste o)": "Open file (key o)",
        "Bildverzeichnis wählen": "Choose image folder",
        "Zuletzt verwendet": "Recently used",
        "Speichern unter (Taste s)": "Save as (key s)",
        "Umbenennen (Taste u)": "Rename (key u)",
        "Bilder sortieren": "Sort images",
        "Name (aufsteigend)": "Name (ascending)",
        "Name (absteigend)": "Name (descending)",
        "Datum (aufsteigend)": "Date (ascending)",
        "Datum (absteigend)": "Date (descending)",
        "Größe (aufsteigend)": "Size (ascending)",
        "Größe (absteigend)": "Size (descending)",
        "In Ordner verschieben…": "Move to folder…",
        "In Ordner kopieren…": "Copy to folder…",
        "Stapelverarbeitung… (Galerie/Liste)": "Batch processing… (gallery/list)",
        "Markierte Bilder konvertieren/verkleinern": "Convert/resize selected images",
        "⚙️ Einstellungen": "⚙️ Settings",
        "🗑️ Papierkorb verwalten…": "🗑️ Manage trash…",
        "🗑️ Papierkorb leeren": "🗑️ Empty trash",
        "Beenden (Taste x)": "Quit (key x)",
        # --- Bearbeiten-Menü ---
        "Rückgängig (Strg+Z)": "Undo (Ctrl+Z)",
        "Wiederholen (Strg+Y)": "Redo (Ctrl+Y)",
        "Rückgängig": "Undo",
        "Wiederholen": "Redo",
        "Kopieren (Strg+C)": "Copy (Ctrl+C)",
        "Ausschneiden (Strg+X)": "Cut (Ctrl+X)",
        "Einfügen (Strg+V)": "Paste (Ctrl+V)",
        "Bild zuschneiden (Taste c)": "Crop image (key c)",
        "Bildgröße ändern (Taste a)": "Resize image (key a)",
        "Bild drehen (Taste d)": "Rotate image (key d)",
        "90° links drehen": "Rotate 90° left",
        "90° rechts drehen": "Rotate 90° right",
        "Horizontal spiegeln": "Flip horizontal",
        "Vertikal spiegeln": "Flip vertical",
        "Bild anpassen… (Taste b)": "Adjust image… (key b)",
        "Datei löschen (Taste del)": "Delete file (key Del)",
        # --- Undo-Beschreibungen (dynamisch) ---
        "Drehen": "Rotate",
        "Größe ändern": "Resize",
        "Zuschneiden": "Crop",
        "Löschen": "Delete",
        "Verschieben": "Move",
        "Anpassen": "Adjust",
        "Metadaten entfernen": "Remove metadata",
        "90° links gedreht": "Rotated 90° left",
        "90° rechts gedreht": "Rotated 90° right",
        "Horizontal gespiegelt": "Flipped horizontally",
        "Vertikal gespiegelt": "Flipped vertically",
        # --- Ansicht-Menü ---
        "Bildanzeige": "Image view",
        "Zur Bildanzeige wechseln": "Switch to image view",
        "Galerie öffnen (Taste g)": "Open gallery (key g)",
        "Listenansicht (Taste l)": "List view (key l)",
        "Zoom-Modus (Taste z)": "Zoom mode (key z)",
        "Vergrößern (+)": "Zoom in (+)",
        "Verkleinern (−)": "Zoom out (−)",
        "An Fenster anpassen (0)": "Fit to window (0)",
        "Originalgröße 100 % (1)": "Actual size 100% (1)",
        "Vollbild (Taste v)": "Fullscreen (key v)",
        "Slideshow starten (Taste p)": "Start slideshow (key p)",
        "Suchen (Taste f)": "Search (key f)",
        "EXIF-Daten anzeigen (Taste e)": "Show EXIF data (key e)",
        # --- Hilfe-Menü ---
        "⌨️ Tastaturkürzel (Taste h / ?)": "⌨️ Keyboard shortcuts (key h / ?)",
        "ℹ️ Über VostiraView": "ℹ️ About VostiraView",
        # --- Toolbar ---
        "Hauptwerkzeuge": "Main tools",
        "Vorheriges Bild (←)": "Previous image (←)",
        "Nächstes Bild (→)": "Next image (→)",
        "Slideshow (p)": "Slideshow (p)",
        "Vollbild (v)": "Fullscreen (v)",
        "Bildanzeige (v)": "Image view (v)",
        "Galerieansicht (g)": "Gallery view (g)",
        "Listenansicht (l)": "List view (l)",
        "Suche (f)": "Search (f)",
        "Speichern unter (s)": "Save as (s)",
        "Umbenennen (u)": "Rename (u)",
        "Kopieren (Ctrl+C)": "Copy (Ctrl+C)",
        "Ausschneiden (Ctrl+X)": "Cut (Ctrl+X)",
        "Löschen (Del)": "Delete (Del)",
        "Zuschneiden (c)": "Crop (c)",
        "Größe ändern (a)": "Resize (a)",
        "Drehen (d)": "Rotate (d)",
        "90° links (Strg+←)": "90° left (Ctrl+←)",
        "90° rechts (Strg+→)": "90° right (Ctrl+→)",
        "Bild anpassen (b)": "Adjust image (b)",
        "Zoom-Modus (z)": "Zoom mode (z)",
        "Sortieren": "Sort",
        "↑ Name": "↑ Name",
        "↓ Name": "↓ Name",
        "↑ Datum": "↑ Date",
        "↓ Datum": "↓ Date",
        "↑ Größe": "↑ Size",
        "↓ Größe": "↓ Size",
        # --- Einstellungs-Dialog ---
        "Einstellungen": "Settings",
        "Allgemein": "General",
        "Ansicht": "View",
        "Slideshow": "Slideshow",
        "Bildverzeichnis:": "Image folder:",
        "Durchsuchen...": "Browse...",
        "Ordner automatisch auf neue/gelöschte Bilder überwachen":
            "Watch folder for new/deleted images automatically",
        "Auto-Aktualisierung:": "Auto-refresh:",
        "Papierkorb-Ordner:": "Trash folder:",
        "Papierkorb-Limit:": "Trash limit:",
        "Unbegrenzt": "Unlimited",
        "Bearbeitungen (Drehen/Zuschneiden/Größe) direkt im Original speichern":
            "Save edits (rotate/crop/resize) directly to the original",
        "Schnellbearbeitung:": "Quick edit:",
        "Thumbnail-Größe:": "Thumbnail size:",
        "Standard-Sortierung:": "Default sorting:",
        "Start-Fenstergröße:": "Initial window size:",
        "Speicherqualität (JPEG/WebP):": "Save quality (JPEG/WebP):",
        "Intervall:": "Interval:",
        "Sprache:": "Language:",
        "Name": "Name",
        "Datum": "Date",
        "Größe": "Size",
        "Aufsteigend": "Ascending",
        "Absteigend": "Descending",
        "Dateien": "files",
        "Sekunden": "seconds",
        "Sprache geändert": "Language changed",
        "Bitte starten Sie das Programm neu, damit die neue Sprache wirksam wird.":
            "Please restart the program for the new language to take effect.",

        # --- Allgemeine Begriffe / Buttons ---
        "Fehler": "Error",
        "Erfolg": "Success",
        "Abbrechen": "Cancel",
        "Schließen": "Close",
        "Durchsuchen…": "Browse…",
        "Bild(er) ausgewählt": "image(s) selected",
        "Nicht möglich": "Not possible",
        "Funktion nicht verfügbar.": "Function not available.",

        # --- Anpassen-Dialog ---
        "Bild anpassen": "Adjust image",
        "Helligkeit": "Brightness",
        "Kontrast": "Contrast",
        "Sättigung": "Saturation",
        "Schärfe": "Sharpness",
        "Zurücksetzen": "Reset",

        # --- Stapelverarbeitung-Dialog ---
        "Stapelverarbeitung": "Batch processing",
        "Zielformat:": "Target format:",
        "Original beibehalten": "Keep original",
        "Längste Seite begrenzen auf": "Limit longest side to",
        "Qualität (JPEG/WebP):": "Quality (JPEG/WebP):",
        "Wirkt nur für JPEG/WebP.": "Applies to JPEG/WebP only.",
        "Zielordner:": "Target folder:",
        "Verarbeiten": "Process",
        "Bitte einen Zielordner angeben.": "Please specify a target folder.",
        "Verarbeite Bilder…": "Processing images…",
        "Zielordner wählen": "Choose target folder",
        "Stapelverarbeitung abgeschlossen": "Batch processing finished",
        "Bild(er) verarbeitet.": "image(s) processed.",
        "Gespeichert in:": "Saved to:",
        "fehlgeschlagen:": "failed:",
        "Bitte zuerst Bilder in der Galerie- oder Listenansicht markieren.":
            "Please first select images in the gallery or list view.",

        # --- In Ordner verschieben/kopieren ---
        "In Ordner verschieben": "Move to folder",
        "In Ordner kopieren": "Copy to folder",
        "Bitte zuerst ein oder mehrere Bilder auswählen.":
            "Please first select one or more images.",
        "Bild(er) kopiert nach": "image(s) copied to",
        "Bild(er) verschoben nach": "image(s) moved to",

        # --- Papierkorb-Verwaltung ---
        "Papierkorb verwalten": "Manage trash",
        "Ursprünglicher Ort": "Original location",
        "Gelöscht": "Deleted",
        "— (unbekannt)": "— (unknown)",
        "Wiederherstellen": "Restore",
        "Endgültig löschen": "Delete permanently",
        "Papierkorb leeren": "Empty trash",
        "Der Papierkorb ist leer.": "The trash is empty.",
        "Datei(en) im Papierkorb.": "file(s) in trash.",
        "Datei(en) endgültig löschen? Dies kann nicht rückgängig gemacht werden.":
            "Delete file(s) permanently? This cannot be undone.",
        "Alle Dateien endgültig löschen? Dies kann nicht rückgängig gemacht werden.":
            "Delete all files permanently? This cannot be undone.",
        "Datei(en) wiederhergestellt": "file(s) restored",
        "Papierkorb": "Trash",
        "Der Papierkorb ist bereits leer.": "The trash is already empty.",
        "Papierkorb geleert": "Trash emptied",
        "Liste der zuletzt verwendeten Ordner geleert": "Recent folders list cleared",
        "(keine)": "(none)",
        "Liste leeren": "Clear list",

        # --- EXIF-Dialog ---
        "EXIF-Daten": "EXIF data",
        "📊 EXIF-Daten": "📊 EXIF data",
        "📝 Rohdaten": "📝 Raw data",
        "Keine EXIF-Daten": "No EXIF data",
        "Keine EXIF-Daten gefunden.": "No EXIF data found.",
        "Tag": "Tag",
        "Wert": "Value",
        "🧹 Metadaten entfernen…": "🧹 Remove metadata…",
        "Speichert das Bild ohne EXIF-/Metadaten (Datenschutz).":
            "Saves the image without EXIF/metadata (privacy).",
        "🗺 Auf Karte anzeigen": "🗺 Show on map",
        "– in OpenStreetMap öffnen": "– open in OpenStreetMap",

        # --- Tastaturkürzel-Hilfe ---
        "Tastaturkürzel": "Keyboard shortcuts",
        "Taste": "Key",
        "Funktion": "Function",
        "— Navigation —": "— Navigation —",
        "— Ansicht —": "— View —",
        "— Datei —": "— File —",
        "— Bearbeiten —": "— Edit —",
        "— Hilfe —": "— Help —",
        "Vorheriges / Nächstes Bild": "Previous / Next image",
        "Slideshow starten / stoppen": "Start / stop slideshow",
        "Galerie öffnen": "Open gallery",
        "Listenansicht öffnen": "Open list view",
        "Vollbild umschalten": "Toggle fullscreen",
        "Zoom-Modus umschalten": "Toggle zoom mode",
        "Vergrößern / Verkleinern": "Zoom in / out",
        "An Fenster anpassen": "Fit to window",
        "Originalgröße 100 %": "Actual size 100%",
        "Zoom zurücksetzen": "Reset zoom",
        "Suche öffnen": "Open search",
        "EXIF-Daten anzeigen": "Show EXIF data",
        "Datei öffnen": "Open file",
        "Speichern unter": "Save as",
        "Umbenennen": "Rename",
        "Einstellungen": "Settings",
        "Beenden": "Quit",
        "Rückgängig / Wiederholen": "Undo / Redo",
        "Kopieren / Ausschneiden / Einfügen": "Copy / Cut / Paste",
        "Drehen (Dialog)": "Rotate (dialog)",
        "90° links / rechts drehen": "Rotate 90° left / right",
        "Horizontal / Vertikal spiegeln": "Flip horizontal / vertical",
        "Bild anpassen": "Adjust image",
        "Diese Hilfe anzeigen": "Show this help",

        # --- Über-Dialog ---
        "Bildbetrachter mit Bearbeitungsfunktionen": "Image viewer with editing features",
        "Funktionen": "Features",
        "Anzeigen & Navigieren": "View & navigate",
        "Zuschneiden, Drehen, Skalieren": "Crop, rotate, scale",
        "Vergleichsmodus (Vorher/Nachher)": "Compare mode (before/after)",
        "EXIF-Daten": "EXIF data",
        "Zoom mit Mausrad": "Zoom with mouse wheel",
        "Galerie-Ansicht": "Gallery view",
        "Listen-Ansicht": "List view",
        "💡 Drücke <b>H</b> oder <b>?</b> für alle Tastaturkürzel.":
            "💡 Press <b>H</b> or <b>?</b> for all keyboard shortcuts.",
        "👤 Entwickelt von Jürg Rechsteiner (Schweiz)":
            "👤 Developed by Jürg Rechsteiner (Switzerland)",
        "🐍 Erstellt mit Python und PyQt6": "🐍 Built with Python and PyQt6",

        # --- Meldungen: Bildoperationen ---
        "Kein Bild ausgewählt.": "No image selected.",
        "Kein Bild zum Zuschneiden ausgewählt.": "No image selected to crop.",
        "Kein Bild zum Drehen ausgewählt.": "No image selected to rotate.",
        "Kein Bild zum Ändern der Größe.": "No image to resize.",
        "Kein Bild zum Anpassen ausgewählt.": "No image selected to adjust.",
        "Kein Bild zum Löschen vorhanden.": "No image available to delete.",
        "Bild erfolgreich geändert.": "Image changed successfully.",
        "Das gedrehte Bild konnte nicht gespeichert werden.":
            "The rotated image could not be saved.",
        "Gedrehtes Bild speichern": "Save rotated image",
        "Zugeschnittenes Bild speichern": "Save cropped image",
        "Bild zugeschnitten und gespeichert.": "Image cropped and saved.",
        "Konnte nicht speichern.": "Could not save.",
        "Original überschreiben?": "Overwrite original?",
        "Bilder löschen": "Delete images",
        "Möchten Sie die ausgewählten Bilder wirklich löschen?":
            "Do you really want to delete the selected images?",
        "Bild löschen": "Delete image",
        "Möchten Sie das aktuelle Bild wirklich löschen?":
            "Do you really want to delete the current image?",
        "Bild wurde in den Papierkorb verschoben.": "Image moved to trash.",
        "gespeichert.": "saved.",
        "Rückgängig mit Strg+Z": "Undo with Ctrl+Z",
        "Bild wurde um {a}° gedreht.": "Image rotated by {a}°.",
        "Ein Fehler ist aufgetreten:": "An error occurred:",
        "Konnte nicht speichern:": "Could not save:",
        "Fehler beim Löschen des Bildes:": "Error deleting the image:",
        "Die Originaldatei „{name}“ wird durch die bearbeitete Version ersetzt. "
        "Eine Sicherung wird im Papierkorb abgelegt und kann mit Rückgängig "
        "(Strg+Z) wiederhergestellt werden. Fortfahren?":
            "The original file “{name}” will be replaced by the edited version. "
            "A backup is kept in the trash and can be restored with Undo "
            "(Ctrl+Z). Continue?",

        # --- Meldungen: Datei ---
        "Kein Bild zum Speichern": "No image to save",
        "Bild gespeichert:": "Image saved:",
        "Bild speichern unter": "Save image as",
        "Kein Bild zum Umbenennen ausgewählt.": "No image selected to rename.",
        "Bild umbenennen": "Rename image",
        "Neuer Name (ohne Erweiterung):": "New name (without extension):",
        "Name unverändert": "Name unchanged",
        "Datei existiert": "File exists",
        "Umbenannt in:": "Renamed to:",
        "Sortiert nach": "Sorted by",
        "Das Bild konnte nicht gespeichert werden:": "The image could not be saved:",
        "Das Bild konnte nicht umbenannt werden:": "The image could not be renamed:",
        "Die Datei „{name}“ existiert bereits. Überschreiben?":
            "The file “{name}” already exists. Overwrite?",
        "Bildverzeichnis auswählen": "Choose image folder",
        "Papierkorb-Ordner auswählen": "Choose trash folder",

        # --- Meldungen: Zwischenablage ---
        "Keine Auswahl": "No selection",
        "Bitte wählen Sie zuerst Bilder in der Galerie aus (mit Checkbox).":
            "Please select images in the gallery first (using the checkbox).",
        "Kein Bild": "No image",
        "Kein Bild zum Kopieren vorhanden.": "No image to copy.",
        "Kopiert": "Copied",
        "Ausgeschnitten": "Cut",
        "Bilder einfügen": "Paste images",
        "Keine Bilder": "No images",
        "Die Zwischenablage enthält keine Bilddateien.":
            "The clipboard contains no image files.",
        "Die Zwischenablage enthält keine Bilder.":
            "The clipboard contains no images.",
        "Bild(er)": "image(s)",
        "Bild": "Image",
        "Bilder": "images",
        "📁 Kopieren": "📁 Copy",
        "👁️ Nur anzeigen": "👁️ View only",
        "📁 In Galerie kopieren - Zum Viewer-Ordner hinzufügen\n👁️‍🗨️ Nur anzeigen - Originale bleiben wo sie sind":
            "📁 Copy to gallery – add to the viewer folder\n👁️‍🗨️ View only – originals stay where they are",
        "Bilder eingefügt": "images pasted",
        "Bilder angezeigt": "images shown",
        "Bild kopiert:": "Image copied:",
        "Bild ausgeschnitten:": "Image cut:",
        "Möchten Sie die ausgewählten Bilder einfügen?": "Paste the selected images?",

        # --- Slideshow / Laden ---
        "Verzeichnis aktualisiert": "Directory updated",
        "Keine Bilder in diesem Ordner": "No images in this folder",
        "Bild geladen:": "Image loaded:",
        "Konnte Bild nicht laden:": "Could not load image:",
        "Bild nicht gefunden.": "Image not found.",
        "Kein Bild geladen": "No image loaded",
        "Keine Bildinformationen": "No image information",
        "Zoom: An Fenster anpassen": "Zoom: fit to window",
        # Drag&Drop / Galerie
        "👁️ Direkt anzeigen": "👁️ View directly",
        "📁 In Galerie kopieren": "📁 Copy to gallery",
        "👁️‍🗨️ Nur anzeigen": "👁️‍🗨️ View only",
        "📁 Alle kopieren": "📁 Copy all",
        "Bild in Galerie kopiert:": "Image copied to gallery:",
        "Bild in Galerie angezeigt:": "Image shown in gallery:",
        "Bilder in Galerie kopiert": "images copied to gallery",
        "Bilder in Galerie angezeigt": "images shown in gallery",
        "Bild(er) in Galerie hinzugefügt": "image(s) added to gallery",
        # Auswahl/Liste
        "Bitte wählen Sie ein Bild aus.": "Please select an image.",
        "Das ausgewählte Bild ist nicht in der Liste.": "The selected image is not in the list.",
        # Kontextmenü Viewer
        "Dateiname kopieren": "Copy file name",
        "Pfad kopieren": "Copy path",
        # Drop-Dialoge
        "Bild geöffnet": "Image opened",
        "Bilder geöffnet": "Images opened",
        "Sie haben das Bild „{name}“ geöffnet.": "You opened the image “{name}”.",
        "Sie haben {count} Bilder geöffnet.": "You opened {count} images.",
        "Was möchten Sie tun?\n\n👁️ Direkt anzeigen\n📁 In Galerie kopieren\n👁️‍🗨️ Nur in Galerie anzeigen":
            "What would you like to do?\n\n👁️ View directly\n📁 Copy to gallery\n👁️‍🗨️ View in gallery only",
        "Was möchten Sie tun?\n\n📁 In Galerie kopieren\n👁️‍🗨️ Nur in Galerie anzeigen":
            "What would you like to do?\n\n📁 Copy to gallery\n👁️‍🗨️ View in gallery only",
        # Resize-Dialog
        "Bildgröße ändern": "Resize image",
        "Breite (Pixel):": "Width (pixels):",
        "Höhe (Pixel):": "Height (pixels):",
        "Wenn Skalierung (%) angegeben, werden Pixel-Werte ignoriert.":
            "If a scale (%) is given, pixel values are ignored.",
        "Skalierung (%):": "Scale (%):",
        "Proportionen beibehalten": "Keep proportions",
        "Ungültige Eingabe. Bitte nur Zahlen eingeben.":
            "Invalid input. Please enter numbers only.",
        "Bild speichern": "Save image",
        # Rotation-Dialog
        "Bild drehen": "Rotate image",
        "Modus": "Mode",
        "Fester Winkel": "Fixed angle",
        "Benutzerdefiniert": "Custom",
        "Fester Winkel:": "Fixed angle:",
        "Benutzerdefinierter Winkel:": "Custom angle:",
        # Suche
        "Suchergebnisse": "Search results",
        "Suchen:": "Search:",
        "Suchbegriff eingeben...": "Enter search term...",
        "Es sind keine Bilder zum Durchsuchen vorhanden.": "There are no images to search.",
        "Das ausgewählte Bild wurde nicht gefunden:": "The selected image was not found:",
        # Crop-Widget
        "Bild laden": "Load image",
        "Zuschneiden aktivieren": "Enable cropping",
        "Bild wurde erfolgreich gespeichert.": "Image saved successfully.",
        "Fehler beim Speichern:": "Error while saving:",
        "Kein Auswahlbereich": "No selection area",
        "Kein Originalbild gefunden": "No original image found",
        # Settings-Browse
        "Bildverzeichnis auswählen": "Choose image folder",
    }
}
