class Command:
    """Eine umkehrbare Operation mit Rückgängig- und Wiederholen-Funktion.

    `description` wird im Menü angezeigt (z. B. "Drehen"), `undo` stellt den
    vorherigen Zustand wieder her, `redo` wendet die Operation erneut an.
    """

    def __init__(self, description, undo, redo):
        self.description = description
        self.undo = undo
        self.redo = redo


class UndoManager:
    """Verwaltet Rückgängig-/Wiederholen-Stapel für umkehrbare Operationen.

    Operationen (Drehen, Zuschneiden, Größe ändern, Löschen) rufen `push()`
    mit je einer Rückgängig- und einer Wiederholen-Funktion auf. Eine neue
    Operation verwirft die Wiederholen-Historie (Standardverhalten).
    """

    def __init__(self, parent, max_steps=20):
        self.parent = parent
        self.max_steps = max_steps
        self._undo_stack = []
        self._redo_stack = []

    def push(self, description, undo, redo):
        """Hinterlegt eine umkehrbare Operation (bereits ausgeführt)."""
        self._undo_stack.append(Command(description, undo, redo))
        if len(self._undo_stack) > self.max_steps:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self.parent.update_undo_redo_actions()

    def can_undo(self):
        return bool(self._undo_stack)

    def can_redo(self):
        return bool(self._redo_stack)

    def peek_undo(self):
        return self._undo_stack[-1].description if self._undo_stack else None

    def peek_redo(self):
        return self._redo_stack[-1].description if self._redo_stack else None

    def undo(self):
        """Macht die zuletzt ausgeführte Operation rückgängig."""
        if not self._undo_stack:
            return False
        cmd = self._undo_stack.pop()
        try:
            cmd.undo()
            self._redo_stack.append(cmd)
            self.parent.statusBar.showMessage(
                f"Rückgängig: {cmd.description}", 3000)
            return True
        except Exception as e:
            print(f"Fehler beim Rückgängigmachen ({cmd.description}): {e}")
            return False
        finally:
            self.parent.update_undo_redo_actions()

    def redo(self):
        """Wiederholt die zuletzt rückgängig gemachte Operation."""
        if not self._redo_stack:
            return False
        cmd = self._redo_stack.pop()
        try:
            cmd.redo()
            self._undo_stack.append(cmd)
            self.parent.statusBar.showMessage(
                f"Wiederholen: {cmd.description}", 3000)
            return True
        except Exception as e:
            print(f"Fehler beim Wiederholen ({cmd.description}): {e}")
            return False
        finally:
            self.parent.update_undo_redo_actions()

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        self.parent.update_undo_redo_actions()
