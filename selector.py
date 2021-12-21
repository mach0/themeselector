# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThemeSelector
                                 A QGIS plugin
 This plugin brings the layer theme settings directly to the desktop
                              -------------------
        begin                : 2017-07-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
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
from qgis.utils import iface

# Import the code for the DockWidget
from .selector_dockwidget import SelectorDockWidget
import os.path


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
            '{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'Theme&Selector')

        self.toolbar = self.iface.addToolBar(self.tr(u'Themeselector'))
        self.toolbar.setObjectName(self.tr(u'Themeselector'))

        self.pluginIsActive = False
        self.dockwidget = None

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
            text=self.tr(u'Theme&Selector'),
            callback=self.run,
            parent=self.iface.mainWindow()
        )

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)
        # TODO: toggle button in toolbar when dockwidget closed
        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'Theme&Selector'),
                action)
            self.iface.removeToolBarIcon(action)
        del self.toolbar

    def run(self):
        """Run method that loads and starts the plugin"""
        # TODO: Check if there is a loaded project - if not deactivate buttons

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

            # show the dockwidget
            # TODO: fix to allow choice of dock location
            self.iface.addDockWidget(Qt.LeftDockWidgetArea, self.dockwidget)
            self.dockwidget.show()

            self.populate()
            # TODO load and display correct theme on opening
            QgsProject.instance().cleared.connect(self.clear)
            QgsProject.instance().readProject.connect(self.populate)

            #QgsProject.instance().mapThemeCollection.projectChanged(self.populate)
            self.dockwidget.PresetComboBox.currentIndexChanged.connect(self.theme_changed)
            self.dockwidget.pushButton_replace.clicked.connect(self.replace_maptheme)
            self.dockwidget.pushButton_add.clicked.connect(self.add_maptheme)
            self.dockwidget.pushButton_remove.clicked.connect(self.remove_maptheme)
            self.dockwidget.pushButton_rename.clicked.connect(self.rename_maptheme)
            self.dockwidget.pushButton_duplicate.clicked.connect(self.duplicate_maptheme)
            icon_up_path = QFileInfo(__file__).absolutePath() + '/img/mActionArrowUp.svg'
            icon_up = QIcon(icon_up_path)
            self.dockwidget.pushButton_up.setIcon(icon_up)
            icon_down_path = QFileInfo(__file__).absolutePath() + '/img/mActionArrowDown.svg'
            icon_down = QIcon(icon_down_path)
            self.dockwidget.pushButton_down.setIcon(icon_down)
            self.dockwidget.pushButton_up.clicked.connect(self.theme_up)
            self.dockwidget.pushButton_down.clicked.connect(self.theme_down)

        else:
            self.pluginIsActive = False
            self.dockwidget.close()

    def clear(self):
        self.dockwidget.PresetComboBox.clear()
        self.dockwidget.pushButton_add.setEnabled(False)
        self.dockwidget.pushButton_remove.setEnabled(False)

    def populate(self):
        self.clear()
        themes = self.dockwidget.getAvailableThemes()
        for setting in themes:
            self.dockwidget.PresetComboBox.addItem(setting)
        theme = self.get_current_theme()
        index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFixedString)
        self.dockwidget.PresetComboBox.setCurrentIndex(index)
        self.dockwidget.pushButton_add.setEnabled(True)
        self.dockwidget.pushButton_remove.setEnabled(True)
    
    def get_current_theme(self):
        ProjectInstance = QgsProject.instance()
        mTC = ProjectInstance.mapThemeCollection()
        themes = self.dockwidget.getAvailableThemes()
        root = ProjectInstance.layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        currentTheme = mTC.createThemeFromCurrentState( root, model )
        for theme in themes:
            if mTC.mapThemeState(theme) == currentTheme:
                return theme


    def theme_down(self):
        max = len(self.dockwidget.getAvailableThemes())
        theme = self.dockwidget.PresetComboBox.currentText()
        index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFixedString)
        if index < max-1:
            index = index + 1
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
            self.theme_changed()

    def theme_up(self):
        theme = self.dockwidget.PresetComboBox.currentText()
        index = self.dockwidget.PresetComboBox.findText(theme, Qt.MatchFixedString)
        if index > 0:
            index = index - 1
            self.dockwidget.PresetComboBox.setCurrentIndex(index)
            self.theme_changed()

    def set_combo_text(self, name):
        # set Combobox to newly created Theme
        index = self.dockwidget.PresetComboBox.findText(name, Qt.MatchFixedString)
        if index >= 0:
            self.dockwidget.PresetComboBox.setCurrentIndex(index)

    def theme_changed(self):
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        
        QgsProject.instance().mapThemeCollection().applyTheme(
            theme, root, model
        )

    def remove_maptheme(self):
        theme = self.dockwidget.PresetComboBox.currentText()
        QgsProject.instance().mapThemeCollection().removeMapTheme(theme)
        self.populate()
        self.theme_changed()

    def replace_maptheme(self):
        theme = self.dockwidget.PresetComboBox.currentText()
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
        QgsProject.instance().mapThemeCollection().update(theme, rec)

    def add_maptheme(self):
        quest = QInputDialog.getText(None,
                                     self.tr(u'Themename'),
                                     self.tr(u'Name of the new theme')
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
        theme = self.dockwidget.PresetComboBox.currentText()
        quest = QInputDialog.getText(None,
                                     self.tr(u'Rename Theme'),
                                     self.tr(u'New Name:'),
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
            QgsProject.instance().mapThemeCollection().applyTheme(
                name, root, model
            )

            QgsProject.instance().mapThemeCollection().removeMapTheme(theme)

            self.populate()
            self.theme_changed()
            self.set_combo_text(name)
            return


    def duplicate_maptheme(self):
        theme = self.dockwidget.PresetComboBox.currentText()
        quest = QInputDialog.getText(None,
                                     self.tr(u'Duplicate theme'),
                                     self.tr(u'Copy theme ')+theme+self.tr(u' to theme '),
                                     0,
                                     theme
                                     )
        root = QgsProject.instance().layerTreeRoot()
        model = iface.layerTreeView().layerTreeModel()
        name, ok = quest
        if ok and name != "":
            rec = QgsProject.instance().mapThemeCollection().createThemeFromCurrentState(root, model)
            QgsProject.instance().mapThemeCollection().insert(name, rec)
            self.set_combo_text(name)
            self.populate()
            self.theme_changed()
            return
