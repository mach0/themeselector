# -*- coding: utf-8 -*-
"""
ThemeSelector

A QGIS plugin
This plugin brings the layer theme settings directly to the desktop
"""
# pylint: disable = no-name-in-module

import os
from typing import Optional, List, Tuple

from qgis.utils import iface
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, QFileInfo, Qt, QSize
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    QgsProject,
    QgsLayoutItemMap,
    QgsMapThemeCollection,
    QgsMessageLog,
    Qgis
)
from qgis.gui import QgsNewNameDialog

from .selector_dockwidget import SelectorDockWidget


class Selector:
    """QGIS Plugin Implementation for Theme Selection and Management.
    
    This plugin provides a dockable widget for managing QGIS map themes,
    allowing users to create, rename, duplicate, and switch between themes.
    """

    def __init__(self, iface) -> None:
        """Initialize the plugin.
        
        Args:
            iface: QGIS interface instance
        """
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        self._connected_layers = set()  # Track layers with connected signals

        # Locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', f'{locale}.qm')
        self.log(f"Detected locale: {locale}", Qgis.Info)
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dockwidget = SelectorDockWidget()
        self.action = self.dockwidget.toggleViewAction()

        settings = QSettings()
        self.dockwidget.resize(settings.value("ThemeSelector/size", QSize(300, 200)))

    def tr(self, message: str) -> str:
        """Translate a message using Qt translation system.
        
        Args:
            message: String to translate
            
        Returns:
            Translated string
        """
        return QCoreApplication.translate('Selector', message)
    
    def log(self, message: str, level: Qgis.MessageLevel = Qgis.Warning) -> None:
        """Log a message to QGIS message log.
        
        Args:
            message: Message to log
            level: Message level (Info, Warning, Critical)
        """
        QgsMessageLog.logMessage(message, 'ThemeSelector', level)

    # -------------------
    # GUI Setup
    # -------------------
    def initGui(self) -> None:
        """Initialize the plugin GUI."""
        self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.show()
        self.dockwidget.raise_()
        self.dockwidget.activateWindow()

        icon_path = QFileInfo(__file__).absolutePath() + '/img/selector.svg'
        self.action.setIcon(QIcon(icon_path))
        self.action.setText(self.tr('Theme&Selector'))
        self.iface.addToolBarIcon(self.action)

        self.populate()
        self.connect_signals()

    def unload(self) -> None:
        """Clean up plugin resources and save settings."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)

        # Save widget size
        settings = QSettings()
        settings.setValue("ThemeSelector/size", self.dockwidget.size())

    def connect_signals(self) -> None:
        """Connect all plugin signals and slots."""
        QgsProject.instance().cleared.connect(self.clear)
        QgsProject.instance().readProject.connect(self.populate)
        QgsProject.instance().mapThemeCollection().projectChanged.connect(self.populate)
        QgsProject.instance().layerWillBeRemoved.connect(self._on_layer_removed)
        self.iface.mapCanvas().layersChanged.connect(self.update_button_state)

        root = QgsProject.instance().layerTreeRoot()
        root.addedChildren.connect(self.on_layer_tree_changed)
        root.removedChildren.connect(self.on_layer_tree_changed)
        root.visibilityChanged.connect(self.check_theme_sync)

        self.dockwidget.PresetComboBox.currentIndexChanged.connect(self.apply_selected_theme)
        self.dockwidget.pushButton_replace.clicked.connect(self.replace_maptheme)
        self.dockwidget.pushButton_add.clicked.connect(self.add_maptheme)
        self.dockwidget.pushButton_remove.clicked.connect(self.remove_maptheme)
        self.dockwidget.pushButton_rename.clicked.connect(self.rename_maptheme)
        self.dockwidget.pushButton_duplicate.clicked.connect(self.duplicate_maptheme)

        self.dockwidget.pushButton_up.setIcon(QIcon(QFileInfo(__file__).absolutePath() + '/img/mActionArrowLeft.svg'))
        self.dockwidget.pushButton_down.setIcon(QIcon(QFileInfo(__file__).absolutePath() + '/img/mActionArrowRight.svg'))
        self.dockwidget.pushButton_up.clicked.connect(self.theme_up)
        self.dockwidget.pushButton_down.clicked.connect(self.theme_down)

        self.update_button_state()
    
    def _on_layer_removed(self, layer_id: str) -> None:
        """Handle layer removal to clean up signal connections.
        
        Args:
            layer_id: ID of the layer being removed
        """
        self._connected_layers.discard(layer_id)

    # -------------------
    # Layer / Theme Updates
    # -------------------
    def on_layer_tree_changed(self, parent, start, end) -> None:
        """Handle layer tree changes.
        
        Args:
            parent: Parent node
            start: Start index
            end: End index
        """
        self.update_button_state()

    def update_button_state(self) -> None:
        """Update button enabled/disabled state based on project state."""
        has_layers = bool(QgsProject.instance().mapLayers())
        has_themes = self.dockwidget.PresetComboBox.count() > 0

        self.dockwidget.pushButton_add.setEnabled(has_layers)
        enabled = has_layers and has_themes
        self.dockwidget.pushButton_remove.setEnabled(enabled)
        self.dockwidget.pushButton_replace.setEnabled(enabled)
        self.dockwidget.pushButton_rename.setEnabled(enabled)
        self.dockwidget.pushButton_duplicate.setEnabled(enabled)

        # Connect styleChanged signals only for new layers
        for layer_id, layer in QgsProject.instance().mapLayers().items():
            if layer_id not in self._connected_layers:
                try:
                    layer.styleChanged.connect(self.check_theme_sync)
                    self._connected_layers.add(layer_id)
                except (AttributeError, RuntimeError) as e:
                    self.log(f"Could not connect to layer {layer_id}: {e}", Qgis.Warning)

        self.check_theme_sync()

    # -------------------
    # Theme State Comparison
    # -------------------
    def theme_states_match(self, state1: QgsMapThemeCollection.MapThemeRecord, 
                          state2: QgsMapThemeCollection.MapThemeRecord) -> bool:
        """Compare two theme states for equality.
        
        Args:
            state1: First theme state
            state2: Second theme state
            
        Returns:
            True if states match, False otherwise
        """
        try:
            def get_layers(state):
                if not hasattr(state, 'layerRecords'):
                    return []
                # List of tuples (layer_id, visibility) in order
                result = []
                for r in state.layerRecords():
                    if r.layer() and r.layer().isValid():
                        # QGIS 4: isVisible is a property, QGIS 3: isVisible() is a method
                        visibility = r.isVisible if isinstance(r.isVisible, bool) else r.isVisible()
                        result.append((r.layer().id(), visibility))
                return result

            return get_layers(state1) == get_layers(state2)
        except (AttributeError, RuntimeError) as e:
            self.log(f"Error comparing theme states: {e}", Qgis.Warning)
            return True

    def check_theme_sync(self) -> None:
        """Check if current layer state matches any available theme.
        
        Updates the combo box styling to indicate sync status:
        - Normal style: current layer state matches at least one theme
        - Red background: current layer state doesn't match any theme
        """
        map_collection = QgsProject.instance().mapThemeCollection()
        available_themes = map_collection.mapThemes()
        
        if not available_themes or not QgsProject.instance().mapLayers():
            self.dockwidget.PresetComboBox.setStyleSheet("")
            return

        try:
            root = QgsProject.instance().layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            current_state = map_collection.createThemeFromCurrentState(root, model)

            # Check if current state matches ANY theme
            matches_any_theme = False
            for theme_name in available_themes:
                stored_state = map_collection.mapThemeState(theme_name)
                if self.theme_states_match(stored_state, current_state):
                    matches_any_theme = True
                    break
            
            if matches_any_theme:
                self.dockwidget.PresetComboBox.setStyleSheet("")  # normal
            else:
                # Current layer state doesn't match any saved theme
                self.dockwidget.PresetComboBox.setStyleSheet(
                    "QComboBox { background-color: #ffcccc; color: #cc0000; }"
                )
        except (AttributeError, RuntimeError) as e:
            self.log(f"Error checking theme sync: {e}", Qgis.Warning)
            self.dockwidget.PresetComboBox.setStyleSheet("")

    # -------------------
    # ComboBox / Populate
    # -------------------
    def clear(self) -> None:
        """Clear the theme combo box and disable buttons."""
        self.dockwidget.PresetComboBox.clear()
        self._connected_layers.clear()
        self.set_buttons_enabled(False)

    def populate(self) -> None:
        """Populate the theme combo box with available themes."""
        self.clear()
        themes = self.dockwidget.getAvailableThemes()
        for t in themes:
            self.dockwidget.PresetComboBox.addItem(t)
        # Select first theme if available
        if self.dockwidget.PresetComboBox.count() > 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(0)
        self.update_button_state()

    def set_combo_theme(self) -> None:
        """Set the combo box to display the current theme."""
        theme = self.get_current_theme()
        if theme:
            index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFlag.MatchFixedString)
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
    
    def get_current_theme(self) -> str:
        """Get the currently selected theme name.
        
        Returns:
            Name of the currently selected theme
        """
        return self.dockwidget.PresetComboBox.currentText()

    def theme_up(self) -> None:
        """Navigate to the previous theme in the list."""
        index = self.dockwidget.PresetComboBox.currentIndex()
        if index > 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index - 1)
            self.apply_selected_theme()

    def theme_down(self) -> None:
        """Navigate to the next theme in the list."""
        index = self.dockwidget.PresetComboBox.currentIndex()
        maximum = self.dockwidget.PresetComboBox.count()
        if index < maximum - 1:
            self.dockwidget.PresetComboBox.setCurrentIndex(index + 1)
            self.apply_selected_theme()

    def apply_selected_theme(self) -> None:
        """Apply the currently selected theme to the map canvas."""
        theme_name = self.get_current_theme()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        QgsProject.instance().mapThemeCollection().applyTheme(theme_name, root, model)
        self.check_theme_sync()

    def set_combo_text(self, name: str) -> None:
        """Set the combo box to a specific theme by name.
        
        Args:
            name: Theme name to select
        """
        index = self.dockwidget.PresetComboBox.findText(name, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    # -------------------
    # Theme Name Dialog Helper
    # -------------------
    def get_new_theme_name(self, title: str, initial: str, existing: List[str]) -> Optional[str]:
        """Show dialog to get a new theme name from user.
        
        Args:
            title: Dialog window title
            initial: Initial/default name to show
            existing: List of existing theme names to prevent duplicates
            
        Returns:
            New theme name if user confirmed, None if cancelled
        """
        dlg = QgsNewNameDialog('', initial, [], existing, Qt.CaseSensitive, self.iface.mainWindow())
        dlg.setWindowTitle(title)
        dlg.setAllowEmptyName(False)
        if dlg.exec():
            name = dlg.name().strip()
            return name if name else None
        return None

    # -------------------
    # Generic Theme Operations
    # -------------------
    def create_or_copy_theme(self, operation: str, source_theme: Optional[str] = None, 
                            initial_name: str = "") -> None:
        """Generic method for creating, renaming, or duplicating themes.
        
        Args:
            operation: Operation type ('add', 'rename', or 'duplicate')
            source_theme: Source theme name for rename/duplicate operations
            initial_name: Initial name to suggest in the dialog
        """
        map_collection = QgsProject.instance().mapThemeCollection()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        existing = map_collection.mapThemes()
        if operation == "rename" and source_theme:
            existing = [t for t in existing if t != source_theme]

        name = self.get_new_theme_name(
            title=self.tr(f"{operation.capitalize()} Theme"),
            initial=initial_name,
            existing=existing
        )
        if not name:
            return

        if operation == "add":
            state = map_collection.createThemeFromCurrentState(root, model)
            map_collection.insert(name, state)
            map_collection.applyTheme(name, root, model)

        elif operation == "rename" and source_theme:
            map_collection.renameMapTheme(source_theme, name)
            layout_manager = QgsProject.instance().layoutManager()
            for layout in layout_manager.layouts():
                for item in layout.items():
                    if isinstance(item, QgsLayoutItemMap):
                        item.refresh()

        elif operation == "duplicate" and source_theme:
            state = map_collection.mapThemeState(source_theme)
            map_collection.insert(name, state)

        self.populate()
        self.set_combo_text(name)

    # -------------------
    # Theme Methods Using Generic Helper
    # -------------------
    def add_maptheme(self) -> None:
        """Create a new theme from the current layer state."""
        self.create_or_copy_theme(operation="add", initial_name="")

    def rename_maptheme(self) -> None:
        """Rename the currently selected theme."""
        old_name = self.get_current_theme()
        self.create_or_copy_theme(operation="rename", source_theme=old_name, initial_name=old_name)

    def duplicate_maptheme(self) -> None:
        """Duplicate the currently selected theme."""
        theme = self.get_current_theme()
        self.create_or_copy_theme(operation="duplicate", source_theme=theme, initial_name=f"{theme}_copy")

    def remove_maptheme(self) -> None:
        """Remove the currently selected theme."""
        theme = self.get_current_theme()
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        self.populate()

    def replace_maptheme(self) -> None:
        """Replace the currently selected theme with the current layer state."""
        theme = self.get_current_theme()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
        QgsProject.instance().mapThemeCollection().update(theme, rec)
        self.check_theme_sync()

    # -------------------
    # Button Helpers
    # -------------------
    def set_buttons_enabled(self, enabled: bool) -> None:
        """Set the enabled state of all theme operation buttons.
        
        Args:
            enabled: True to enable buttons, False to disable
        """
        self.dockwidget.pushButton_remove.setEnabled(enabled)
        self.dockwidget.pushButton_replace.setEnabled(enabled)
        self.dockwidget.pushButton_add.setEnabled(enabled)
        self.dockwidget.pushButton_rename.setEnabled(enabled)
        self.dockwidget.pushButton_duplicate.setEnabled(enabled)
