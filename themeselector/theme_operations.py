"""Theme CRUD operations mixin for the ThemeSelector plugin."""

from __future__ import annotations

from qgis.core import QgsLayoutItemMap, QgsProject
from qgis.gui import QgsNewNameDialog
from qgis.PyQt.QtCore import QCoreApplication

from .compat import CASE_SENSITIVE


class ThemeOperationsMixin:
    """Mixin providing theme create / rename / duplicate / remove / replace."""

    def tr(self, message: str) -> str:
        """Translate message using Qt translation system."""
        return QCoreApplication.translate('ThemeOperationsMixin', message)

    def get_new_theme_name(
        self,
        title: str,
        initial: str,
        existing: list[str]
    ) -> str | None:
        """Show a dialog and return the validated name."""
        parent = (
            self.iface.mainWindow()
            if self.iface and hasattr(self.iface, 'mainWindow')
            else None
        )
        dlg = QgsNewNameDialog(
            '', initial, [], existing, CASE_SENSITIVE, parent
        )
        dlg.setWindowTitle(title)
        dlg.setAllowEmptyName(False)
        if dlg.exec():
            name = dlg.name().strip()
            return name if name else None
        return None

    def create_or_copy_theme(
        self,
        operation: str,
        source_theme: str | None = None,
        initial_name: str = ''
    ) -> None:
        """Shared backend for add, rename, and duplicate."""
        collection, root, model = self._get_map_context()
        if not collection or not root:
            return

        existing = collection.mapThemes()

        if operation == 'rename' and source_theme:
            existing = [t for t in existing if t != source_theme]

        titles = {
            'add': self.tr('Add Theme'),
            'rename': self.tr('Rename Theme'),
            'duplicate': self.tr('Duplicate Theme'),
        }
        title = titles.get(operation, self.tr('Theme'))

        name = self.get_new_theme_name(
            title=title,
            initial=initial_name,
            existing=existing,
        )
        if not name:
            return

        if operation == 'add':
            state = collection.createThemeFromCurrentState(root, model)
            collection.insert(name, state)
            collection.applyTheme(name, root, model)

        elif operation == 'rename' and source_theme:
            collection.renameMapTheme(source_theme, name)
            for layout in QgsProject.instance().layoutManager().layouts():
                for item in layout.items():
                    if isinstance(item, QgsLayoutItemMap):
                        item.refresh()

        elif operation == 'duplicate' and source_theme:
            state = collection.mapThemeState(source_theme)
            collection.insert(name, state)

        self.populate()
        self.set_combo_text(name)

    def add_maptheme(self) -> None:
        """Create a new theme from the current layer state."""
        self.create_or_copy_theme(operation='add', initial_name='')

    def rename_maptheme(self) -> None:
        """Rename the currently selected theme."""
        old_name = self.get_current_theme()
        if not old_name:
            return
        self.create_or_copy_theme(
            operation='rename',
            source_theme=old_name,
            initial_name=old_name
        )

    def duplicate_maptheme(self) -> None:
        """Duplicate the currently selected theme."""
        theme = self.get_current_theme()
        if not theme:
            return
        self.create_or_copy_theme(
            operation='duplicate',
            source_theme=theme,
            initial_name=f'{theme}_copy'
        )

    def remove_maptheme(self) -> None:
        """Remove the currently selected theme."""
        theme = self.get_current_theme()
        if not theme:
            return
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        self.populate()

    def replace_maptheme(self) -> None:
        """Overwrite the selected theme with the current layer state."""
        theme = self.get_current_theme()
        if not theme:
            return
        collection, root, model = self._get_map_context()
        if not collection or not root:
            return
        collection.update(
            theme,
            collection.createThemeFromCurrentState(root, model),
        )
        self.check_theme_sync()
