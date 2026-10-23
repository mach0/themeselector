"""Tests for Selector orchestrator class."""

import unittest
from unittest.mock import MagicMock

from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class SelectorTest(unittest.TestCase):
    """Test plugin Selector functionality."""

    def setUp(self):
        if QGIS_APP is None:
            self.skipTest("QGIS environment not available")
        from themeselector.selector import Selector
        self.mock_iface = MagicMock()
        self.mock_iface.mainWindow.return_value = PARENT
        self.mock_iface.mapCanvas.return_value = CANVAS
        self.selector = Selector(self.mock_iface)

    def tearDown(self):
        if hasattr(self, 'selector'):
            self.selector.unload()

    def test_init_and_tr(self):
        """Test Selector initialization and translations."""
        self.assertIsNotNone(self.selector.dockwidget)
        self.assertIsNotNone(self.selector.action)
        translated = self.selector.tr('Theme&Selector')
        self.assertIsInstance(translated, str)

    def test_gui_init_and_unload(self):
        """Test initGui and clean unload."""
        self.selector.initGui()
        self.mock_iface.addDockWidget.assert_called_once()
        self.mock_iface.addToolBarIcon.assert_called_once()

        self.selector.unload()
        self.mock_iface.removeDockWidget.assert_called_once()
        self.mock_iface.removeToolBarIcon.assert_called_once()

    def test_button_states_empty_project(self):
        """Test button states when no layers or themes exist."""
        self.selector.update_button_state()
        btn_add = self.selector.dockwidget.pushButton_add
        btn_remove = self.selector.dockwidget.pushButton_remove
        self.assertFalse(btn_add.isEnabled())
        self.assertFalse(btn_remove.isEnabled())


if __name__ == '__main__':
    unittest.main()
