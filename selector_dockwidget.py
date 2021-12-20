# -*- coding: utf-8 -*-
"""
/***************************************************************************
 SelectorDockwidget
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

import os

from qgis.PyQt import (
    uic
)
from qgis.PyQt.QtCore import (
    pyqtSignal
)
from qgis.PyQt.QtWidgets import (
    QDockWidget
)
from qgis.core import (
    QgsProject
)

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'selector_dockwidget_base.ui'))


class SelectorDockWidget(QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, parent=None):
        """Constructor."""
        super(SelectorDockWidget, self).__init__(parent)
        #self.getAvailableThemes()

        self.setupUi(self)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def getAvailableThemes(self):
        prj = QgsProject.instance()
        themes = prj.mapThemeCollection().mapThemes()
        return themes
