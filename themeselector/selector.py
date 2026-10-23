"""ThemeSelector: A QGIS plugin to manage map themes from the desktop."""

from __future__ import annotations

import os

from qgis.core import Qgis, QgsMessageLog, QgsProject
from qgis.PyQt.QtCore import (
    QCoreApplication,
    QLocale,
    QSettings,
    QSize,
    QTimer,
    QTranslator,
)
from qgis.PyQt.QtGui import QIcon

from .compat import LEFT_DOCK_WIDGET_AREA, MATCH_FIXED_STRING
from .selector_dockwidget import SelectorDockWidget
from .theme_operations import ThemeOperationsMixin
from .theme_sync import ThemeSyncMixin


class Selector(ThemeOperationsMixin, ThemeSyncMixin):
    """QGIS Plugin Orchestrator for Theme Selection."""

    def __init__(self, iface) -> None:
        """Initialize the plugin."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self._connected_layers = set()
        self._project_is_saving = False

        # Debounce timer for UI updates to avoid "event storms"
        # during project save/load
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.debounced_update)

        # Translation / Locale setup
        user_locale = QSettings().value('locale/userLocale', '')
        if not user_locale:
            user_locale = QLocale.system().name()
        locale = str(user_locale)[0:2] if user_locale else 'en'

        locale_path = os.path.join(self.plugin_dir, 'i18n', f'{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dockwidget = SelectorDockWidget()
        self.action = self.dockwidget.toggleViewAction()

        # Restore widget size
        settings = QSettings()
        default_size = QSize(300, 200)
        self.dockwidget.resize(
            settings.value('ThemeSelector/size', default_size)
        )

    def tr(self, message: str) -> str:
        """Translate message using Qt translation system."""
        return QCoreApplication.translate('Selector', message)

    def log(self, message: str, level=None) -> None:
        """Log message to QGIS message log."""
        if level is None:
            level = getattr(
                Qgis.MessageLevel, 'Warning', getattr(Qgis, 'Warning', 1)
            )
        QgsMessageLog.logMessage(message, 'ThemeSelector', level)

    def _get_map_context(self):
        """Helper to get current theme collection, root node, and model."""
        project = QgsProject.instance()
        tree_view = (
            self.iface.layerTreeView()
            if self.iface and hasattr(self.iface, 'layerTreeView')
            else None
        )
        model = (
            tree_view.layerTreeModel()
            if tree_view and hasattr(tree_view, 'layerTreeModel')
            else None
        )
        return (
            project.mapThemeCollection(),
            project.layerTreeRoot(),
            model,
        )

    def initGui(self) -> None:
        """Initialize plugin GUI elements."""
        self.iface.addDockWidget(LEFT_DOCK_WIDGET_AREA, self.dockwidget)
        self.dockwidget.show()

        icon_path = os.path.join(self.plugin_dir, 'img', 'selector.svg')
        self.action.setIcon(QIcon(icon_path))
        self.action.setText(self.tr('Theme&Selector'))
        self.iface.addToolBarIcon(self.action)

        self.populate()
        self.connect_signals()

    def unload(self) -> None:
        """Unload plugin, remove GUI parts and save settings."""
        self.update_timer.stop()
        self.disconnect_signals()
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)
        QSettings().setValue('ThemeSelector/size', self.dockwidget.size())

    def disconnect_signals(self) -> None:
        """Disconnect all signals to ensure a clean unload."""
        project = QgsProject.instance()

        # Disconnect project signals
        try:
            project.cleared.disconnect(self.on_project_cleared)
        except (AttributeError, RuntimeError, TypeError):
            pass
        try:
            project.readProject.disconnect(self.trigger_update)
            project.writeProject.disconnect(self._on_write_project)
            project.projectSaved.disconnect(self._on_project_saved)
            project.mapThemeCollection().mapThemesChanged.disconnect(
                self.trigger_update
            )
            project.layerWillBeRemoved.disconnect(self._on_layer_removed)
        except (AttributeError, RuntimeError, TypeError):
            pass

        # Disconnect canvas signals
        try:
            if (self.iface and hasattr(self.iface, 'mapCanvas')
                    and self.iface.mapCanvas()):
                self.iface.mapCanvas().layersChanged.disconnect(
                    self.trigger_update
                )
        except (AttributeError, RuntimeError, TypeError):
            pass

        # Disconnect layer tree signals
        try:
            root = project.layerTreeRoot()
            if root:
                root.addedChildren.disconnect(self.trigger_update)
                root.removedChildren.disconnect(self.trigger_update)
                root.visibilityChanged.disconnect(self.trigger_update)
        except (AttributeError, RuntimeError, TypeError):
            pass

        # Disconnect layer signals
        for layer_id in list(self._connected_layers):
            layer = project.mapLayer(layer_id)
            if layer:
                try:
                    layer.styleChanged.disconnect(self.trigger_update)
                except (AttributeError, RuntimeError, TypeError):
                    pass
        self._connected_layers.clear()

        # Disconnect UI signals
        dw = self.dockwidget
        try:
            dw.PresetComboBox.currentIndexChanged.disconnect(
                self.apply_selected_theme
            )
            dw.pushButton_replace.clicked.disconnect(self.replace_maptheme)
            dw.pushButton_add.clicked.disconnect(self.add_maptheme)
            dw.pushButton_remove.clicked.disconnect(self.remove_maptheme)
            dw.pushButton_rename.clicked.disconnect(self.rename_maptheme)
            dw.pushButton_duplicate.clicked.disconnect(self.duplicate_maptheme)
            dw.pushButton_up.clicked.disconnect(self.theme_up)
            dw.pushButton_down.clicked.disconnect(self.theme_down)
        except (AttributeError, RuntimeError, TypeError):
            pass

    def connect_signals(self) -> None:
        """Connect project and UI signals."""
        project = QgsProject.instance()
        project.cleared.connect(self.on_project_cleared)

        # Signals trigger debounce timer instead of immediate, heavy updates
        project.readProject.connect(self.trigger_update)
        project.writeProject.connect(self._on_write_project)
        project.projectSaved.connect(self._on_project_saved)
        project.mapThemeCollection().mapThemesChanged.connect(
            self.trigger_update
        )
        project.layerWillBeRemoved.connect(self._on_layer_removed)

        if (self.iface and hasattr(self.iface, 'mapCanvas')
                and self.iface.mapCanvas()):
            self.iface.mapCanvas().layersChanged.connect(self.trigger_update)

        root = project.layerTreeRoot()
        if root:
            root.addedChildren.connect(self.trigger_update)
            root.removedChildren.connect(self.trigger_update)
            root.visibilityChanged.connect(self.trigger_update)

        # UI connections
        dw = self.dockwidget
        dw.PresetComboBox.currentIndexChanged.connect(
            self.apply_selected_theme
        )
        dw.pushButton_replace.clicked.connect(self.replace_maptheme)
        dw.pushButton_add.clicked.connect(self.add_maptheme)
        dw.pushButton_remove.clicked.connect(self.remove_maptheme)
        dw.pushButton_rename.clicked.connect(self.rename_maptheme)
        dw.pushButton_duplicate.clicked.connect(self.duplicate_maptheme)

        img_dir = os.path.join(self.plugin_dir, 'img')
        icon_up = os.path.join(img_dir, 'mActionArrowLeft.svg')
        icon_down = os.path.join(img_dir, 'mActionArrowRight.svg')
        dw.pushButton_up.setIcon(QIcon(icon_up))
        dw.pushButton_down.setIcon(QIcon(icon_down))
        dw.pushButton_up.clicked.connect(self.theme_up)
        dw.pushButton_down.clicked.connect(self.theme_down)

        self.trigger_update()

    # --- Project Save Guards ---
    def _on_write_project(self, doc) -> None:
        """Set flag when QGIS starts writing project."""
        self._project_is_saving = True
        self.update_timer.stop()  # Kill any pending updates during save

    def _on_project_saved(self) -> None:
        """Clear flag and refresh sync once write is complete."""
        self._project_is_saving = False
        self.trigger_update()

    # --- Debounced Update Logic ---
    def trigger_update(self) -> None:
        """Request a UI update. Restarts the debounce timer."""
        if self._project_is_saving:
            return
        self.update_timer.start(250)  # 250ms debounce

    def debounced_update(self) -> None:
        """Actually perform the UI refresh after the debounce interval."""
        if self._project_is_saving:
            return
        self.populate()

    # --- UI Update Helpers ---
    def _on_layer_removed(self, layer_id: str) -> None:
        self._connected_layers.discard(layer_id)

    def on_project_cleared(self) -> None:
        """Clear combo box and reset state when project is cleared."""
        self._connected_layers.clear()
        self.clear()

    def update_button_state(self) -> None:
        """Enable or disable toolbar buttons based on current state."""
        has_layers = bool(QgsProject.instance().mapLayers())
        has_themes = self.dockwidget.PresetComboBox.count() > 0

        self.dockwidget.pushButton_add.setEnabled(has_layers)
        enabled = has_layers and has_themes
        for btn in (
            self.dockwidget.pushButton_remove,
            self.dockwidget.pushButton_replace,
            self.dockwidget.pushButton_rename,
            self.dockwidget.pushButton_duplicate,
        ):
            btn.setEnabled(enabled)

        # Ensure style changes trigger sync check
        for layer_id, layer in QgsProject.instance().mapLayers().items():
            if layer_id not in self._connected_layers:
                try:
                    layer.styleChanged.connect(self.trigger_update)
                    self._connected_layers.add(layer_id)
                except (AttributeError, RuntimeError) as exc:
                    self.log(
                        f'Layer signal connection failed: {layer_id} - {exc}'
                    )

        self.check_theme_sync()

    def clear(self) -> None:
        """Clear combo box."""
        self.dockwidget.PresetComboBox.clear()
        self.set_buttons_enabled(False)

    def populate(self) -> None:
        """Repopulate the theme combo box."""
        if self._project_is_saving:
            return

        self.dockwidget.PresetComboBox.blockSignals(True)
        try:
            current_selected = self.get_current_theme()
            self.clear()
            themes: list[str] = self.dockwidget.getAvailableThemes()
            for theme in themes:
                self.dockwidget.PresetComboBox.addItem(theme)

            if self.dockwidget.PresetComboBox.count() > 0:
                active = self._detect_active_theme()
                if active:
                    index = self.dockwidget.PresetComboBox.findText(
                        active, MATCH_FIXED_STRING
                    )
                elif current_selected:
                    index = self.dockwidget.PresetComboBox.findText(
                        current_selected, MATCH_FIXED_STRING
                    )
                else:
                    index = 0
                self.dockwidget.PresetComboBox.setCurrentIndex(max(0, index))
        finally:
            self.dockwidget.PresetComboBox.blockSignals(False)

        self.update_button_state()

    # --- UI Navigation Helpers ---
    def get_current_theme(self) -> str:
        """Return the name of the currently selected theme."""
        return self.dockwidget.PresetComboBox.currentText()

    def theme_up(self) -> None:
        """Select previous theme in combo box."""
        idx = self.dockwidget.PresetComboBox.currentIndex()
        if idx > 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(idx - 1)

    def theme_down(self) -> None:
        """Select next theme in combo box."""
        idx = self.dockwidget.PresetComboBox.currentIndex()
        if idx < self.dockwidget.PresetComboBox.count() - 1:
            self.dockwidget.PresetComboBox.setCurrentIndex(idx + 1)

    def apply_selected_theme(self) -> None:
        """Apply the currently selected theme to the map."""
        theme = self.get_current_theme()
        if not theme:
            return
        collection, root, model = self._get_map_context()
        if not collection or not root:
            return
        collection.applyTheme(theme, root, model)
        self.check_theme_sync()

    def set_combo_text(self, name: str) -> None:
        """Set combo box selection by theme name."""
        index = self.dockwidget.PresetComboBox.findText(
            name, MATCH_FIXED_STRING
        )
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable theme action buttons."""
        btns = (
            self.dockwidget.pushButton_remove,
            self.dockwidget.pushButton_replace,
            self.dockwidget.pushButton_add,
            self.dockwidget.pushButton_rename,
            self.dockwidget.pushButton_duplicate,
        )
        for btn in btns:
            btn.setEnabled(enabled)
