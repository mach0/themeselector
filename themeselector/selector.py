# -*- coding: utf-8 -*-
"""
ThemeSelector

A QGIS plugin
This plugin brings the layer theme settings directly to the desktop

    begin                : 2017-07-13
    git sha              : $Format:%H$
    copyright            : (C) 2017 by Werner Macho
    email                : werner.macho@gmail.com

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
"""
# pylint: disable = no-name-in-module

import os
from qgis.utils import iface
from qgis.PyQt.QtCore import (
    QSettings,
    QTranslator,
    QCoreApplication,
    QFileInfo,
    Qt,
    QSize
)
from qgis.PyQt.QtWidgets import (
    QInputDialog,
    QLineEdit,
    QMessageBox
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject, QgsLayoutItemMap


# Import the code for the DockWidget
from .selector_dockwidget import SelectorDockWidget


class Selector:
    """QGIS Plugin Implementation.
    """

    def __init__(self, iface):
        """Constructor."""
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'{locale}.qm')

        print(f"Detected locale: {locale}")

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.dockwidget = SelectorDockWidget()
        self.action = self.dockwidget.toggleViewAction()

        # Remember size of the dockwidget
        settings = QSettings()
        self.dockwidget.resize(settings.value("ThemeSelector/size",
                                              QSize(300, 200)))

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('Selector', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # Add the dock widget to QGIS interface
        self.iface.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.dockwidget)
        
        # Ensure the dockwidget is always visible and activated
        self.dockwidget.show()
        self.dockwidget.raise_()
        self.dockwidget.activateWindow()

        # Set up the icon for the toolbar
        icon_path = QFileInfo(__file__).absolutePath() + '/img/selector.svg'
        self.action.setIcon(QIcon(icon_path))
        self.action.setText(self.tr('Theme&Selector'))

        # Add the toolbar icon to the QGIS toolbar
        self.iface.addToolBarIcon(self.action)

        # Initialize widget functionality
        self.populate()
        self.connect_signals()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)

        # Save the size of the dock widget
        settings = QSettings()
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        saved_size = settings.value("ThemeSelector/size", QSize(300, 200))
        if isinstance(saved_size, QSize):
            self.dockwidget.resize(saved_size)
        elif isinstance(saved_size, str):  # Handle improperly serialized values
            try:
                width, height = map(int, saved_size.strip("()").split(","))
                self.dockwidget.resize(QSize(width, height))
            except ValueError:
                self.dockwidget.resize(QSize(300, 200))  # Default size
        settings = QSettings()
        settings.setValue("ThemeSelector/size", self.dockwidget.size())

    def connect_signals(self):
        """Connect various signals and slots."""
        QgsProject.instance().cleared.connect(self.clear)
        QgsProject.instance().readProject.connect(self.populate)

        # Connect to map theme collection changes only
        QgsProject.instance().mapThemeCollection().projectChanged.connect(self.populate)
        
        # Connect to layer changes for button state updates and theme sync checking
        self.iface.mapCanvas().layersChanged.connect(self.update_button_state)
        
        # Connect to layer tree changes for more comprehensive monitoring
        QgsProject.instance().layerTreeRoot().addedChildren.connect(self.on_layer_tree_changed)
        QgsProject.instance().layerTreeRoot().removedChildren.connect(self.on_layer_tree_changed)
        QgsProject.instance().layerTreeRoot().visibilityChanged.connect(self.check_theme_sync)

        self.dockwidget.PresetComboBox.currentIndexChanged.connect(self.apply_selected_theme)
        self.dockwidget.pushButton_replace.clicked.connect(self.replace_maptheme)
        self.dockwidget.pushButton_add.clicked.connect(self.add_maptheme)
        self.dockwidget.pushButton_remove.clicked.connect(self.remove_maptheme)
        self.dockwidget.pushButton_rename.clicked.connect(self.rename_maptheme)
        self.dockwidget.pushButton_duplicate.clicked.connect(self.duplicate_maptheme)

        # Set button icons
        self.dockwidget.pushButton_up.setIcon(QIcon(QFileInfo(__file__).absolutePath() + '/img/mActionArrowLeft.svg'))
        self.dockwidget.pushButton_down.setIcon(QIcon(QFileInfo(__file__).absolutePath() + '/img/mActionArrowRight.svg'))
        self.dockwidget.pushButton_up.clicked.connect(self.theme_up)
        self.dockwidget.pushButton_down.clicked.connect(self.theme_down)

        # Initial button state
        self.update_button_state()

    def on_layer_tree_changed(self, parent, index_start, index_end):
        """Handle when layers are added or removed from the layer tree."""
        # Update button state and check theme sync when layer tree changes
        self.update_button_state()

    def update_button_state(self):
        """Update button enabled/disabled state based on themes and layers."""
        has_layers = bool(QgsProject.instance().mapLayers())
        has_themes = self.dockwidget.PresetComboBox.count() > 0
        
        # Always enable Add button when layers are present
        if has_layers:
            self.dockwidget.pushButton_add.setEnabled(True)
        else:
            self.dockwidget.pushButton_add.setEnabled(False)
        
        # Enable other buttons only when both layers and themes exist
        if has_layers and has_themes:
            self.dockwidget.pushButton_remove.setEnabled(True)
            self.dockwidget.pushButton_replace.setEnabled(True)
            self.dockwidget.pushButton_rename.setEnabled(True)
            self.dockwidget.pushButton_duplicate.setEnabled(True)
        else:
            self.dockwidget.pushButton_remove.setEnabled(False)
            self.dockwidget.pushButton_replace.setEnabled(False)
            self.dockwidget.pushButton_rename.setEnabled(False)
            self.dockwidget.pushButton_duplicate.setEnabled(False)
        
        # Check if current theme matches actual layer state and update styling
        self.check_theme_sync()

    def check_theme_sync(self):
        """Check if the current theme matches the actual layer state and update ComboBox styling."""
        current_theme = self.dockwidget.PresetComboBox.currentText()
        
        if not current_theme or not QgsProject.instance().mapLayers():
            # Reset styling if no theme or no layers
            self.dockwidget.PresetComboBox.setStyleSheet("")
            return
        
        map_collection = QgsProject.instance().mapThemeCollection()
        if current_theme not in map_collection.mapThemes():
            return
        
        try:
            # Get the stored theme state
            stored_theme_state = map_collection.mapThemeState(current_theme)
            
            # Get the current actual state
            root = QgsProject.instance().layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            current_state = map_collection.createThemeFromCurrentState(root, model)
            
            # Compare the states
            if self.theme_states_match(stored_theme_state, current_state):
                # Theme matches - normal styling
                self.dockwidget.PresetComboBox.setStyleSheet("")
            else:
                # Theme doesn't match - red background
                self.dockwidget.PresetComboBox.setStyleSheet(
                    "QComboBox { background-color: #ffcccc; color: #cc0000; }"
                )
        except Exception as e:
            # If there's any error, reset to normal styling
            print(f"Error checking theme sync: {e}")
            self.dockwidget.PresetComboBox.setStyleSheet("")

    def theme_states_match(self, state1, state2):
        """Compare two theme states to see if they match."""
        try:
            # Simple approach: compare the number of visible layers first
            current_layers = QgsProject.instance().mapLayers()
            if not current_layers:
                return True  # No layers, consider it matching
            
            # Get layer records from both states
            if hasattr(state1, 'layerRecords') and hasattr(state2, 'layerRecords'):
                records1 = state1.layerRecords()
                records2 = state2.layerRecords()
                
                # Quick check: different number of records means different states
                if len(records1) != len(records2):
                    return False
                
                # Create lookup dictionaries
                dict1 = {}
                dict2 = {}
                
                for record in records1:
                    try:
                        layer = record.layer()
                        if layer and layer.isValid():
                            dict1[layer.id()] = record
                    except:
                        continue
                        
                for record in records2:
                    try:
                        layer = record.layer()
                        if layer and layer.isValid():
                            dict2[layer.id()] = record
                    except:
                        continue
                
                # Check if same layers are present
                if set(dict1.keys()) != set(dict2.keys()):
                    return False
                
                # Compare visibility for each layer
                for layer_id in dict1.keys():
                    try:
                        record1 = dict1[layer_id]
                        record2 = dict2[layer_id]
                        
                        if record1.isVisible() != record2.isVisible():
                            return False
                    except:
                        continue
                
                return True
            
            # Fallback: assume they match if we can't properly compare
            return True
            
        except Exception as e:
            print(f"Error comparing theme states: {e}")
            return True  # Assume they match if we can't compare

    def clear(self):
        """Clear combobox and disable buttons."""
        self.dockwidget.PresetComboBox.clear()
        self.disable_buttons()

    def populate(self):
        """Populate combobox with available themes."""
        self.clear()
        themes = self.dockwidget.getAvailableThemes()

        for setting in themes:
            self.dockwidget.PresetComboBox.addItem(setting)

        self.set_combo_theme()
        # Update button state based on layers and themes
        self.update_button_state()

    def set_combo_theme(self):
        """Set combo box to the current theme."""
        theme = self.get_current_theme()
        if theme is not None:
            index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFlag.MatchFixedString)
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def get_current_theme(self):
        """Retrieve the currently selected theme by name."""
        return self.dockwidget.PresetComboBox.currentText()

    def theme_up(self):
        """Move to the previous theme based on the index in the combobox."""
        index = self.dockwidget.PresetComboBox.currentIndex()
        if index > 0:
            # Move to the previous theme by decreasing index
            self.dockwidget.PresetComboBox.setCurrentIndex(index - 1)
            self.apply_selected_theme()  

    def theme_down(self):
        """Move to the next theme based on the index in the combobox."""
        maximum = self.dockwidget.PresetComboBox.count()  # Total number of themes
        index = self.dockwidget.PresetComboBox.currentIndex()
        if index < maximum - 1:
            # Move to the next theme by increasing index
            self.dockwidget.PresetComboBox.setCurrentIndex(index + 1)
            self.apply_selected_theme()  

    def apply_selected_theme(self):
        """Apply the selected theme based on the current combobox selection."""
        theme_name = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        QgsProject.instance().mapThemeCollection().applyTheme(theme_name, root, model)
        # Check sync after applying theme
        self.check_theme_sync()

    def set_combo_text(self, name):
        """Set combobox to the newly created theme."""
        index = self.dockwidget.PresetComboBox.findText(name, Qt.MatchFlag.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def remove_maptheme(self):
        """Remove the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        self.populate()

    def replace_maptheme(self):
        """Replace the current theme with a new one."""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
        QgsProject.instance().mapThemeCollection().update(theme, rec)
        # Check sync after updating theme
        self.check_theme_sync()

    def add_maptheme(self):
        """Add a new theme."""
        map_collection = QgsProject.instance().mapThemeCollection()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()

        # Check if the current state already exists
        current_state = map_collection.createThemeFromCurrentState(root, model)
        for existing_theme in map_collection.mapThemes():
            if map_collection.mapThemeState(existing_theme) == current_state:
                msg = QMessageBox.warning(None, self.tr("Theme Exists"),
                                          self.tr("The theme '%1' already exists with this configuration. "
                                                  "Do you still want to create a new theme?").replace('%1', existing_theme), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg == QMessageBox.StandardButton.No:
                    return

        # Ask for new theme name
        name, ok = QInputDialog.getText(None, self.tr('Themename'), self.tr('Name of the new theme'))
        if ok and name != "":
            rec = map_collection.createThemeFromCurrentState(root, model)
            map_collection.insert(name, rec)
            self.populate()
            map_collection.applyTheme(name, root, model)
            self.set_combo_text(name)

    def rename_maptheme(self):
        """Rename the selected theme and update map layouts."""
        theme = self.dockwidget.PresetComboBox.currentText()
        name, ok = QInputDialog.getText(None,
                                        self.tr('Rename Theme'),
                                        self.tr('New Name:'),
                                        QLineEdit.EchoMode.Normal,
                                        theme)
        if ok and name != "":
            # Access the map theme collection via QgsProject instance
            map_collection = QgsProject.instance().mapThemeCollection()

            # Ensure the theme exists in the collection before renaming
            if theme in map_collection.mapThemes():
                # Rename the theme in the map theme collection
                map_collection.renameMapTheme(theme, name)

                # Apply the newly renamed theme to all layouts
                layout_manager = QgsProject.instance().layoutManager()
                for layout in layout_manager.layouts():
                    for item in layout.items():
                        if isinstance(item, QgsLayoutItemMap):
                            # Refresh the map item
                            item.refresh()
                            print(f"Refreshed map item in layout '{layout.name()}' for map item.")

                # Repopulate the combobox and set the selected theme
                self.populate()
                self.set_combo_text(name)
            else:
                QMessageBox.warning(None, self.tr("Theme Not Found"),
                                    self.tr("The theme '%1' was not found in the map theme collection.").replace('%1', theme))

    def duplicate_maptheme(self):
        """Duplicate the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        name, ok = QInputDialog.getText(None, self.tr('Duplicate Theme'),
                                        self.tr('Name of the new theme:'),
                                        QLineEdit.EchoMode.Normal,
                                        theme)
        if ok and name != "":
            map_collection = QgsProject.instance().mapThemeCollection()
            state = map_collection.mapThemeState(theme)
            map_collection.insert(name, state)
            self.populate()
            self.set_combo_text(name)

    def disable_buttons(self):
        """Disable theme buttons."""
        self.dockwidget.pushButton_remove.setEnabled(False)
        self.dockwidget.pushButton_replace.setEnabled(False)
        self.dockwidget.pushButton_add.setEnabled(False)
        self.dockwidget.pushButton_rename.setEnabled(False)
        self.dockwidget.pushButton_duplicate.setEnabled(False)

    def enable_buttons(self):
        """Enable theme buttons."""
        self.dockwidget.pushButton_remove.setEnabled(True)
        self.dockwidget.pushButton_replace.setEnabled(True)
        self.dockwidget.pushButton_add.setEnabled(True)
        self.dockwidget.pushButton_rename.setEnabled(True)
        self.dockwidget.pushButton_duplicate.setEnabled(True)
