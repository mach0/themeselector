"""Theme synchronization and detection mixin for the ThemeSelector plugin."""

from qgis.core import Qgis

from .utils import get_current_visibility, theme_matches_map


class ThemeSyncMixin:
    """Mixin for detecting active themes and managing UI sync indicators."""

    def check_theme_sync(self) -> None:
        """Update the combo-box style to reflect theme match state.

        Bypasses createThemeFromCurrentState to avoid Qt/C++ enumeration
        warnings.
        """
        if getattr(self, '_project_is_saving', False):
            return

        if not hasattr(self, 'dockwidget') or not self.dockwidget:
            return

        collection, root, _model = self._get_map_context()
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
            current_theme = (
                self.get_current_theme()
                if hasattr(self, 'get_current_theme')
                else ''
            )
            if current_theme and current_theme in available_themes:
                stored_state = collection.mapThemeState(current_theme)
                if theme_matches_map(stored_state, current_vis):
                    synced = True

            if not synced:
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
        except (AttributeError, RuntimeError) as exc:
            # Safe fallback: if something is unstable, just clear the styling
            if hasattr(self, 'log'):
                self.log(f'Theme sync check failed: {exc}', Qgis.Warning)
            self.dockwidget.PresetComboBox.setStyleSheet('')

    def _detect_active_theme(self) -> str:
        """Return theme whose stored state matches current visibility."""
        try:
            collection, root, _model = self._get_map_context()
            if not collection or not root:
                return ''

            current_vis = get_current_visibility(root)
            for theme_name in collection.mapThemes():
                stored_state = collection.mapThemeState(theme_name)
                if theme_matches_map(stored_state, current_vis):
                    return theme_name
        except (AttributeError, RuntimeError) as exc:
            if hasattr(self, 'log'):
                self.log(f'Active theme detection failed: {exc}', Qgis.Warning)
        return ''
