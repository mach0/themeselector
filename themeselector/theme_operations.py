# -*- coding: utf-8 -*-
"""Theme CRUD operations mixin for the ThemeSelector plugin."""

from typing import List, Optional
from qgis.core import QgsLayoutItemMap, QgsProject
from qgis.gui import QgsNewNameDialog
from .compat import CASE_SENSITIVE

class ThemeOperationsMixin:
    """Mixin that provides theme create / rename / duplicate / remove / replace."""

    def get_new_theme_name(self, title: str, initial: str, existing: List[str]) -> Optional[str]:
        """Show a dialog and return the validated name."""
        # Note: self.iface is expected from the host class
        dlg = QgsNewNameDialog('', initial, [], existing, CASE_SENSITIVE, self.iface.mainWindow())
        dlg.setWindowTitle(title)
        dlg.setAllowEmptyName(False)
        if dlg.exec():
            name = dlg.name().strip()
            return name if name else None
        return None

    def create_or_copy_theme(self, operation: str, source_theme: Optional[str] = None, 
                             initial_name: str = '') -> None:
        """Shared backend for add, rename, and duplicate."""
        collection, root, model = self._get_map_context()
        existing = collection.mapThemes()

        if operation == 'rename' and source_theme:
            existing = [t for t in existing if t != source_theme]

        name = self.get_new_theme_name(
            title=self.tr(f'{operation.capitalize()} Theme'),
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
        self.create_or_copy_theme(operation='rename', source_theme=old_name, initial_name=old_name)

    def duplicate_maptheme(self) -> None:
        """Duplicate the currently selected theme."""
        theme = self.get_current_theme()
        self.create_or_copy_theme(operation='duplicate', source_theme=theme, initial_name=f'{theme}_copy')

    def remove_maptheme(self) -> None:
        """Remove the currently selected theme."""
        QgsProject.instance().mapThemeCollection().removeMapTheme(self.get_current_theme())
        self.populate()

    def replace_maptheme(self) -> None:
        """Overwrite the selected theme with the current layer state."""
        collection, root, model = self._get_map_context()
        collection.update(
            self.get_current_theme(),
            collection.createThemeFromCurrentState(root, model),
        )
        self.check_theme_sync()
