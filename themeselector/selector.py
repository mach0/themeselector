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
    qVersion,
    QCoreApplication,
    QFileInfo,
    Qt
)
from qgis.PyQt.QtGui import (
    QIcon
)
from qgis.PyQt.QtWidgets import (
    QAction,
    QInputDialog
)
from qgis.core import (
    QgsProject
)

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

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('Theme&Selector')

        self.toolbar = self.iface.addToolBar(self.tr('Themeselector'))
        self.toolbar.setObjectName(self.tr('Themeselector'))

        self.pluginIsActive = False
        self.dockwidget = None
        self.map_collection = QgsProject.instance().mapThemeCollection()

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

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):

        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.setCheckable(True)
        action.toggled.connect(callback)
        action.setEnabled(enabled_flag)
        action.setChecked(False)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = QFileInfo(__file__).absolutePath() + '/img/selector.svg'
        self.add_action(
            icon_path,
            text=self.tr('Theme&Selector'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('Theme&Selector'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that loads and starts the plugin"""
        if not self.pluginIsActive:
            self.pluginIsActive = True
            # dockwidget may not exist if:
            #    first run of plugin
            #    removed on close (see self.onClosePlugin method)
            if self.dockwidget is None:
                # Create the dockwidget (after translation) and keep reference
                self.dockwidget = SelectorDockWidget()
            # connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)
            # add widget to widgetarea
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

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
        else:
            self.pluginIsActive = False
            self.clear()
            self.dockwidget.close()
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
        self.map_collection.applyTheme(
            theme, root, model
        )

    def remove_maptheme(self):
        """remove theme"""
        theme = self.dockwidget.PresetComboBox.currentText()
        self.map_collection.removeMapTheme(theme)
        self.populate()
        self.theme_changed()

    def replace_maptheme(self):
        """replace current theme with new one"""
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = self.map_collection.createThemeFromCurrentState(root, model)
        self.map_collection.update(theme, rec)

    def add_maptheme(self):
        """add theme"""
        quest = QInputDialog.getText(None,
                                     self.tr('Themename'),
                                     self.tr('Name of the new theme')
                                     )
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        name, ok = quest
        if ok and name != "":
            rec = self.map_collection.createThemeFromCurrentState(root, model)
            self.map_collection.insert(name, rec)
            self.populate()
            self.map_collection.applyTheme(
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
            rec = self.map_collection.createThemeFromCurrentState(root, model)
            self.map_collection.insert(name, rec)
            self.populate()
            self.map_collection.applyTheme(
                name, root, model
            )
            self.map_collection.removeMapTheme(theme)
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
            rec = self.map_collection.createThemeFromCurrentState(root, model)
            self.map_collection.insert(name, rec)
            self.populate()
            self.set_combo_text(name)
            self.theme_changed()
            return
