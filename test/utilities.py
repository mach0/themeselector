"""Common functionality used by regression tests."""

import logging
from unittest.mock import MagicMock

LOGGER = logging.getLogger('QGIS')
QGIS_APP = None
CANVAS = None
PARENT = None
IFACE = None


def get_qgis_app():
    """Start one QGIS application to test against.

    :returns: Handle to QGIS app, canvas, iface and parent.
    """
    global QGIS_APP, PARENT, CANVAS, IFACE

    if QGIS_APP is None:
        try:
            from qgis.testing import start_app
            QGIS_APP = start_app()
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Could not start QgsApplication: %s", exc)
            return None, None, None, None

    if PARENT is None:
        try:
            from qgis.PyQt.QtWidgets import QWidget
            PARENT = QWidget()
        except Exception:  # noqa: BLE001
            PARENT = None

    if CANVAS is None:
        try:
            from qgis.gui import QgsMapCanvas
            CANVAS = QgsMapCanvas(PARENT)
        except Exception:  # noqa: BLE001
            CANVAS = None

    if IFACE is None:

        IFACE = MagicMock()
        if CANVAS is not None:
            IFACE.mapCanvas.return_value = CANVAS

    return QGIS_APP, CANVAS, IFACE, PARENT
