# -*- coding: utf-8 -*-
"""ThemeSelector: A QGIS plugin to manage map themes from the desktop."""

import os
from typing import List

from qgis.utils import iface
from qgis.PyQt.QtCore import QCoreApplication, QFileInfo, QSettings, QSize, QTimer, QTranslator
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsMessageLog, QgsProject, Qgis

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

        # Debounce timer for UI updates to avoid "event storms" during project save/load
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.debounced_update)

        # Translation / Locale setup
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'{locale}.qm')
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dockwidget = SelectorDockWidget()
        self.action = self.dockwidget.toggleViewAction()

        # Restore widget size
        settings = QSettings()
        self.dockwidget.resize(settings.value('ThemeSelector/size', QSize(300, 200)))

    def tr(self, message: str) -> str:
        """Translate message using Qt translation system."""
        return QCoreApplication.translate('Selector', message)

    def log(self, message: str, level: Qgis.MessageLevel = Qgis.Warning) -> None:
        """Log message to QGIS message log."""
        QgsMessageLog.logMessage(message, 'ThemeSelector', level)

    def _get_map_context(self):
        """Helper to get current theme collection, root node, and tree model."""
        return (
            QgsProject.instance().mapThemeCollection(),
            QgsProject.instance().layerTreeRoot(),
            iface.layerTreeView().layerTreeModel(),
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
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)
        QSettings().setValue('ThemeSelector/size', self.dockwidget.size())

    def connect_signals(self) -> None:
        """Connect project and UI signals."""
        project = QgsProject.instance()
        project.cleared.connect(self.clear)
        
        # Many signals now trigger the debounce timer instead of immediate, heavy updates
        project.readProject.connect(self.trigger_update)
        project.writeProject.connect(self._on_write_project)
        project.projectSaved.connect(self._on_project_saved)
        project.mapThemeCollection().mapThemesChanged.connect(self.trigger_update)
        project.layerWillBeRemoved.connect(self._on_layer_removed)

        self.iface.mapCanvas().layersChanged.connect(self.trigger_update)

        root = project.layerTreeRoot()
        root.addedChildren.connect(self.trigger_update)
        root.removedChildren.connect(self.trigger_update)
        root.visibilityChanged.connect(self.trigger_update)

        # UI connections - these remain instant for responsiveness
        dw = self.dockwidget
        dw.PresetComboBox.currentIndexChanged.connect(self.apply_selected_theme)
        dw.pushButton_replace.clicked.connect(self.replace_maptheme)
        dw.pushButton_add.clicked.connect(self.add_maptheme)
        dw.pushButton_remove.clicked.connect(self.remove_maptheme)
        dw.pushButton_rename.clicked.connect(self.rename_maptheme)
        dw.pushButton_duplicate.clicked.connect(self.duplicate_maptheme)

        img_dir = os.path.join(self.plugin_dir, 'img')
        dw.pushButton_up.setIcon(QIcon(os.path.join(img_dir, 'mActionArrowLeft.svg')))
        dw.pushButton_down.setIcon(QIcon(os.path.join(img_dir, 'mActionArrowRight.svg')))
        dw.pushButton_up.clicked.connect(self.theme_up)
        dw.pushButton_down.clicked.connect(self.theme_down)

        self.trigger_update()

    # --- Project Save Guards ---
    def _on_write_project(self, doc) -> None:
        """Set flag when QGIS starts writing project."""
        self._project_is_saving = True
        self.update_timer.stop() # Kill any pending updates during save

    def _on_project_saved(self) -> None:
        """Clear flag and refresh sync once write is complete."""
        self._project_is_saving = False
        self.trigger_update()

    # --- Debounced Update Logic ---
    def trigger_update(self) -> None:
        """Request a UI update. Restarts the debounce timer."""
        if self._project_is_saving:
            return
        self.update_timer.start(250) # 250ms debounce

    def debounced_update(self) -> None:
        """Actually perform the UI refresh after the debounce interval."""
        if self._project_is_saving:
            return
        self.populate()

    # --- UI Update Helpers ---
    def _on_layer_removed(self, layer_id: str) -> None:
        self._connected_layers.discard(layer_id)

    def on_layer_tree_changed(self, parent, start, end) -> None:
        self.trigger_update()

    def update_button_state(self) -> None:
        """Enable or disable toolbar buttons based on current project state."""
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
                    self.log(f'Layer signal connection failed: {layer_id} - {exc}', Qgis.Warning)

        self.check_theme_sync()

    def clear(self) -> None:
        """Clear combo box."""
        self.dockwidget.PresetComboBox.clear()
        self._connected_layers.clear()
        self.set_buttons_enabled(False)

    def populate(self) -> None:
        """Repopulate the theme combo box."""
        if self._project_is_saving:
            return

        self.dockwidget.PresetComboBox.blockSignals(True)
        try:
            self.clear()
            themes: List[str] = self.dockwidget.getAvailableThemes()
            for theme in themes:
                self.dockwidget.PresetComboBox.addItem(theme)

            if self.dockwidget.PresetComboBox.count() > 0:
                active = self._detect_active_theme()
                index = self.dockwidget.PresetComboBox.findText(active, MATCH_FIXED_STRING) if active else -1
                self.dockwidget.PresetComboBox.setCurrentIndex(max(0, index))
        finally:
            self.dockwidget.PresetComboBox.blockSignals(False)

        self.update_button_state()

    # --- UI Navigation Helpers ---
    def set_combo_theme(self) -> None:
        theme = self.get_current_theme()
        if theme:
            self.dockwidget.PresetComboBox.setCurrentIndex(
                self.dockwidget.PresetComboBox.findText(theme, MATCH_FIXED_STRING)
            )

    def get_current_theme(self) -> str:
        return self.dockwidget.PresetComboBox.currentText()

    def theme_up(self) -> None:
        idx = self.dockwidget.PresetComboBox.currentIndex()
        if idx > 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(idx - 1)
            self.apply_selected_theme()

    def theme_down(self) -> None:
        idx = self.dockwidget.PresetComboBox.currentIndex()
        if idx < self.dockwidget.PresetComboBox.count() - 1:
            self.dockwidget.PresetComboBox.setCurrentIndex(idx + 1)
            self.apply_selected_theme()

    def apply_selected_theme(self) -> None:
        collection, root, model = self._get_map_context()
        if not collection or not root:
             return
        collection.applyTheme(self.get_current_theme(), root, model)
        self.check_theme_sync()

    def set_combo_text(self, name: str) -> None:
        index = self.dockwidget.PresetComboBox.findText(name, MATCH_FIXED_STRING)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def set_buttons_enabled(self, enabled: bool) -> None:
        btns = (
            self.dockwidget.pushButton_remove,
            self.dockwidget.pushButton_replace,
            self.dockwidget.pushButton_add,
            self.dockwidget.pushButton_rename,
            self.dockwidget.pushButton_duplicate,
        )
        for btn in btns:
            btn.setEnabled(enabled)
