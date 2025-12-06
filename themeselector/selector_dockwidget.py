# -*- coding: utf-8 -*-
"""
 SelectorDockWidget

 A QGIS plugin for managing layer theme settings from the desktop.

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
from typing import Optional, List

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QWidget
from qgis.core import QgsProject


class SelectorDockWidget(QDockWidget):
    """Dockable widget for theme selection and management.
    
    This widget provides a user interface for selecting and managing
    QGIS map themes directly from the QGIS desktop.
    """
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize the dock widget.
        
        Args:
            parent: Optional parent widget
        """
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
        self.setFeatures(dock_features)

    def getAvailableThemes(self) -> List[str]:
        """Retrieve and return the available map themes from the current QGIS project.

        Returns:
            List of available theme names
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()
