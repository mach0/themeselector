# -*- coding: utf-8 -*-
"""Qt5/Qt6 compatibility constants for the ThemeSelector plugin."""
# pylint: disable=no-name-in-module

from qgis.PyQt.QtCore import Qt

if hasattr(Qt, 'CaseSensitivity'):
    # Qt6
    CASE_SENSITIVE = Qt.CaseSensitivity.CaseSensitive
    MATCH_FIXED_STRING = Qt.MatchFlag.MatchFixedString
    LEFT_DOCK_WIDGET_AREA = Qt.DockWidgetArea.LeftDockWidgetArea
else:
    # Qt5
    CASE_SENSITIVE = Qt.CaseSensitive
    MATCH_FIXED_STRING = Qt.MatchFixedString
    LEFT_DOCK_WIDGET_AREA = Qt.LeftDockWidgetArea
