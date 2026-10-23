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
from __future__ import annotations

import os

from qgis.core import QgsProject
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDockWidget, QWidget

from .compat import DOCK_WIDGET_FEATURES


class SelectorDockWidget(QDockWidget):
    """Dockable widget for theme selection and management.

    This widget provides a user interface for selecting and managing
    QGIS map themes directly from the QGIS desktop.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the dock widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        # Construct the path to the UI file dynamically
        base_dir = os.path.dirname(__file__)
        ui_path = os.path.join(base_dir, 'selector_dockwidget_base.ui')
        uic.loadUi(ui_path, self)

        # Set dock widget features
        self.setFeatures(DOCK_WIDGET_FEATURES)

    def getAvailableThemes(self) -> list[str]:
        """Retrieve and return available map themes from the QGIS project.

        Returns:
            List of available theme names
        """
        return QgsProject.instance().mapThemeCollection().mapThemes()
