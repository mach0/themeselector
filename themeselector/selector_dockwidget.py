# -*- coding: utf-8 -*-
"""
 SelectorDockWidget

 A QGIS plugin for managing layer theme settings from the desktop.

        begin                : 2017-07-13
        git sha              : $Format:%H$
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com

 This program is free software; you can redistribute it and/or modify
 t under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
"""
# pylint: disable = no-name-in-module

import os
from qgis.PyQt import uic
#from PyQt6.uic import loadUi
from qgis.PyQt.QtWidgets import QDockWidget
from qgis.core import QgsProject

# Load the UI file dynamically using uic
#FORM_CLASS, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__),
#                                            'selector_dockwidget_base.ui'))


class SelectorDockWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Construct the path to the UI file dynamically
        ui_path = os.path.join(os.path.dirname(__file__), 'selector_dockwidget_base.ui')
        uic.loadUi(ui_path, self)

        # Set dock widget features
        dock_features = getattr(
            QDockWidget,
            'AllDockWidgetFeatures',
            QDockWidget.DockWidgetFeature.DockWidgetClosable | 
            QDockWidget.DockWidgetFeature.DockWidgetMovable | 
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        #dock_features = getattr(QDockWidget, 'AllDockWidgetFeatures', QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setFeatures(dock_features)

        #self.setupUi(self)

    def getAvailableThemes(self):
        """
        Retrieve and return the available map themes from the current
        QGIS project.

        Returns:
            list: A list of available theme names.
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()
