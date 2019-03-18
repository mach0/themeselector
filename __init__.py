# -*- coding: utf-8 -*-
"""
/***************************************************************************
 LayerPreset
                                 A QGIS plugin
 This plugin brings the layer preset settings directly to the desktop
                             -------------------
        begin                : 2017-07-13
        copyright            : (C) 2017 by Werner Macho
        email                : werner.macho@gmail.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load LayerPreset class from file LayerPreset.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .selector import LayerPreset
    return LayerPreset(iface)
