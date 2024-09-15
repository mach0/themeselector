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
    QMessageBox
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject


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

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

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
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.show()

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
        settings.setValue("ThemeSelector/size", self.dockwidget.size())

    def connect_signals(self):
        """Connect various signals and slots."""
        QgsProject.instance().cleared.connect(self.clear)
        QgsProject.instance().readProject.connect(self.populate)
        self.iface.mapCanvas().layersChanged.connect(self.set_combo_theme)

        self.dockwidget.PresetComboBox.currentIndexChanged.connect(self.theme_changed)
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

        # Disable buttons if no layers present
        if len(QgsProject.instance().mapLayers()) == 0:
            self.disable_buttons()

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
        self.enable_buttons()

    def set_combo_theme(self):
        """Set combo box to the current theme."""
        theme = self.get_current_theme()
        if theme is not None:
            index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFixedString)
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def get_current_theme(self):
        """Retrieve the current theme."""
        project_instance = QgsProject.instance()
        map_theme_collection = project_instance.mapThemeCollection()
        themes = self.dockwidget.getAvailableThemes()
        root = project_instance.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        current_theme = map_theme_collection.createThemeFromCurrentState(root, model)

        for theme in themes:
            if map_theme_collection.mapThemeState(theme) == current_theme:
                return theme

    def theme_down(self):
        """Switch to the next theme."""
        maximum = len(self.dockwidget.getAvailableThemes())
        index = self.dockwidget.PresetComboBox.currentIndex()

        if index < maximum - 1:
            self.dockwidget.PresetComboBox.setCurrentIndex(index + 1)
            self.theme_changed()

    def theme_up(self):
        """Switch to the previous theme."""
        index = self.dockwidget.PresetComboBox.currentIndex()

        if index > 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index - 1)
            self.theme_changed()

    def set_combo_text(self, name):
        """Set combobox to the newly created theme."""
        index = self.dockwidget.PresetComboBox.findText(name, Qt.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def theme_changed(self):
        """Apply the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        QgsProject.instance().mapThemeCollection().applyTheme(theme, root, model)

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
                                          self.tr(f"The theme '{existing_theme}' already exists with this configuration. "
                                                  "Do you still want to create a new theme?"), QMessageBox.Yes | QMessageBox.No)
                if msg == QMessageBox.No:
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
        """Rename the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        name, ok = QInputDialog.getText(None, self.tr('Rename Theme'),
                                        self.tr('New Name:'),
                                        0,
                                        theme)
        if ok and name != "":
            map_collection = QgsProject.instance().mapThemeCollection()
            root = QgsProject.instance().layerTreeRoot()
            model = iface.layerTreeView().layerTreeModel()
            rec = map_collection.createThemeFromCurrentState(root, model)
            map_collection.insert(name, rec)
            map_collection.removeMapTheme(theme)
            self.populate()
            self.set_combo_text(name)

    def duplicate_maptheme(self):
        """Duplicate the selected theme."""
        theme = self.dockwidget.PresetComboBox.currentText()
        name, ok = QInputDialog.getText(None, self.tr('Duplicate Theme'),
                                        self.tr('Name of the new theme:'),
                                        0,
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
