# -*- coding: utf-8 -*-
"""Theme synchronization and detection mixin for the ThemeSelector plugin."""

from qgis.core import QgsProject, Qgis
from .utils import get_current_visibility, theme_matches_map

class ThemeSyncMixin:
    """Mixin for detecting active themes and managing UI sync indicators."""

    def check_theme_sync(self) -> None:
        """Update the combo-box style to reflect whether layers match a saved theme.

        Bypasses createThemeFromCurrentState to avoid Qt/C++ enumeration warnings.
        """
        if getattr(self, '_project_is_saving', False):
            return

        collection, root, model = self._get_map_context()
        if not collection or not root:
            return

        available_themes = collection.mapThemes()
        if not available_themes:
            self.dockwidget.PresetComboBox.setStyleSheet('')
            return

        try:
            # Manual visibility extraction - SAFE and SILENT during save/load
            current_vis = get_current_visibility(root)
            
            synced = False
            for theme_name in available_themes:
                stored_state = collection.mapThemeState(theme_name)
                if theme_matches_map(stored_state, current_vis):
                    synced = True
                    break
            
            # Apply colorization based on sync state
            if synced:
                self.dockwidget.PresetComboBox.setStyleSheet('')
            else:
                self.dockwidget.PresetComboBox.setStyleSheet(
                    'QComboBox { background-color: #ffcccc; color: #cc0000; }'
                )
        except (AttributeError, RuntimeError):
            # Safe fallback: if something is unstable, just clear the styling
            self.dockwidget.PresetComboBox.setStyleSheet('')

    def _detect_active_theme(self) -> str:
        """Return the theme whose stored state matches the current visibility state."""
        try:
            collection, root, _ = self._get_map_context()
            if not collection or not root:
                return ''
                
            current_vis = get_current_visibility(root)
            for theme_name in collection.mapThemes():
                stored_state = collection.mapThemeState(theme_name)
                if theme_matches_map(stored_state, current_vis):
                    return theme_name
        except (AttributeError, RuntimeError):
            pass
        return ''
