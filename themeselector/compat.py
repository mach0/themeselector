"""Qt5/Qt6 compatibility constants for the ThemeSelector plugin."""
# pylint: disable=no-name-in-module

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QDockWidget

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

if hasattr(QDockWidget, 'DockWidgetFeature'):
    # Qt6
    DOCK_WIDGET_FEATURES = (
        QDockWidget.DockWidgetFeature.DockWidgetClosable
        | QDockWidget.DockWidgetFeature.DockWidgetMovable
        | QDockWidget.DockWidgetFeature.DockWidgetFloatable
    )
else:
    # Qt5
    _fallback_features = (
        QDockWidget.DockWidgetClosable
        | QDockWidget.DockWidgetMovable
        | QDockWidget.DockWidgetFloatable
    )
    DOCK_WIDGET_FEATURES = getattr(
        QDockWidget,
        'AllDockWidgetFeatures',
        _fallback_features
    )
