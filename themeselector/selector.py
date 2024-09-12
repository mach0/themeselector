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

import os.path
from qgis.utils import iface
from qgis.PyQt.QtCore import (
    QSettings,
    QTranslator,
    QCoreApplication,
    QFileInfo,
    Qt
)
from qgis.PyQt.QtWidgets import (
    QInputDialog
)
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProject


# Import the code for the DockWidget
from .selector_dockwidget import SelectorDockWidget


class Selector:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
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

        self.dockwidget = None
        self.dockwidget = SelectorDockWidget()
        self.action = self.dockwidget.toggleViewAction()

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Selector', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # Create the dockwidget (after translation) and keep reference
   
        self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
        self.dockwidget.show()


        icon_path = QFileInfo(__file__).absolutePath() + '/img/selector.svg'
        self.action.setIcon(QIcon(icon_path))
        self.action.setText(self.tr('Theme&Selector'))
        self.iface.addToolBarIcon(self.action)
        self.run_init()

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeDockWidget(self.dockwidget)

    def run_init(self):
        """Run method that loads and starts the plugin"""
        self.populate()
        QgsProject.instance().cleared.connect(self.clear)
        QgsProject.instance().readProject.connect(self.populate)
        # connect QGIS layertool to themeselector
        self.iface.mapCanvas().layersChanged.connect(
            self.set_combo_theme)

        self.dockwidget.PresetComboBox.currentIndexChanged.connect(
            self.theme_changed)
        self.dockwidget.pushButton_replace.clicked.connect(
            self.replace_maptheme)
        self.dockwidget.pushButton_add.clicked.connect(
            self.add_maptheme)
        self.dockwidget.pushButton_remove.clicked.connect(
            self.remove_maptheme)
        self.dockwidget.pushButton_rename.clicked.connect(
            self.rename_maptheme)
        self.dockwidget.pushButton_duplicate.clicked.connect(
            self.duplicate_maptheme)
        icon_up_path = QFileInfo(__file__).absolutePath() + \
            '/img/mActionArrowLeft.svg'
        icon_up = QIcon(icon_up_path)
        self.dockwidget.pushButton_up.setIcon(icon_up)
        icon_down_path = QFileInfo(__file__).absolutePath() + \
            '/img/mActionArrowRight.svg'
        icon_down = QIcon(icon_down_path)
        self.dockwidget.pushButton_down.setIcon(icon_down)
        self.dockwidget.pushButton_up.clicked.connect(self.theme_up)
        self.dockwidget.pushButton_down.clicked.connect(self.theme_down)

        if len(QgsProject.instance().mapLayers()) == 0:
            self.dockwidget.pushButton_add.setEnabled(False)
            self.dockwidget.pushButton_remove.setEnabled(False)
            self.dockwidget.pushButton_rename.setEnabled(False)
            self.dockwidget.pushButton_replace.setEnabled(False)
            self.dockwidget.pushButton_duplicate.setEnabled(False)

    def clear(self):
        """set combobox to zero"""
        self.dockwidget.PresetComboBox.clear()
        self.dockwidget.pushButton_add.setEnabled(False)
        self.dockwidget.pushButton_remove.setEnabled(False)
        self.dockwidget.pushButton_rename.setEnabled(False)
        self.dockwidget.pushButton_replace.setEnabled(False)
        self.dockwidget.pushButton_duplicate.setEnabled(False)

    def populate(self):
        """populate combobox with existing themes"""
        self.clear()
        themes = self.dockwidget.getAvailableThemes()
        for setting in themes:
            self.dockwidget.PresetComboBox.addItem(setting)
        self.set_combo_theme()
        self.dockwidget.pushButton_add.setEnabled(True)
        self.dockwidget.pushButton_remove.setEnabled(True)
        self.dockwidget.pushButton_rename.setEnabled(True)
        self.dockwidget.pushButton_replace.setEnabled(True)
        self.dockwidget.pushButton_duplicate.setEnabled(True)

    def set_combo_theme(self):
        """set combo to current theme"""
        theme = self.get_current_theme()
        if theme is not None:
            index = self.dockwidget.PresetComboBox.findText(
                theme,
                Qt.MatchFixedString)
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def get_current_theme(self):
        """get current theme"""
        ProjectInstance = QgsProject.instance()
        mTC = ProjectInstance.mapThemeCollection()
        themes = self.dockwidget.getAvailableThemes()
        root = ProjectInstance.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        currentTheme = mTC.createThemeFromCurrentState(root, model)
        for theme in themes:
            if mTC.mapThemeState(theme) == currentTheme:
                return theme

    def theme_down(self):
        """change one theme down"""
        maximum = len(self.dockwidget.getAvailableThemes())
        theme = self.dockwidget.PresetComboBox.currentText()
        index = self.dockwidget.PresetComboBox.findText(theme,
                                                        Qt.MatchFixedString)
        if index < maximum-1:
            index = index + 1
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
            self.theme_changed()

    def theme_up(self):
        """change one theme up"""
        theme = self.dockwidget.PresetComboBox.currentText()
        index = self.dockwidget.PresetComboBox.findText(theme,
                                                        Qt.MatchFixedString)
        if index > 0:
            index = index - 1
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
            self.theme_changed()

    def set_combo_text(self, name):
        """set Combobox to newly created Theme"""
        index = self.dockwidget.PresetComboBox.findText(name,
                                                        Qt.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def theme_changed(self):
        """check if theme has changed"""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        QgsProject.instance().mapThemeCollection().applyTheme(
            theme, root, model
        )

    def remove_maptheme(self):
        """remove theme"""
        theme = self.dockwidget.PresetComboBox.currentText()
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        self.populate()
        self.theme_changed()

    def replace_maptheme(self):
        """replace current theme with new one"""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
        QgsProject.instance().mapThemeCollection().update(theme, rec)

    def add_maptheme(self):
        """add theme"""
        self.map_collection = QgsProject.instance().mapThemeCollection()
        quest = QInputDialog.getText(None,
                                     self.tr('Themename'),
                                     self.tr('Name of the new theme')
                                     )
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        name, ok = quest
        if ok and name != "":
            rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
            QgsProject.instance().mapThemeCollection().insert(name, rec)
            self.populate()
            QgsProject.instance().mapThemeCollection().applyTheme(
                name, root, model
            )
            self.set_combo_text(name)
            return

    def rename_maptheme(self):
        """rename theme"""
        theme = self.dockwidget.PresetComboBox.currentText()
        quest = QInputDialog.getText(None,
                                     self.tr('Rename Theme'),
                                     self.tr('New Name:'),
                                     0,
                                     theme
                                     )
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        name, ok = quest
        if ok and name != "":
            rec= QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
            QgsProject.instance().mapThemeCollection().insert(name, rec)
            self.populate()
            QgsProject.instance().mapThemeCollection().applyTheme(
                name, root, model
            )
            QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
            self.populate()
            self.theme_changed()
            self.set_combo_text(name)
            return

    def duplicate_maptheme(self):
        """duplicate current theme"""
        theme = self.dockwidget.PresetComboBox.currentText()
        quest = QInputDialog.getText(None,
                                     self.tr('Duplicate theme'),
                                     self.tr('Copy theme ') +
                                     theme+self.tr(' to theme '),
                                     0,
                                     theme
                                     )
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        name, ok = quest
        if ok and name != "":
            rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
            QgsProject.instance().mapThemeCollection().insert(name, rec)
            self.populate()
            self.set_combo_text(name)
            self.theme_changed()
            return
