"""DockWidget test."""

import unittest

from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class SelectorDockWidgetTest(unittest.TestCase):

    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        if QGIS_APP is None:
            self.skipTest("QGIS environment not available")
        from themeselector.selector_dockwidget import SelectorDockWidget
        self.dockwidget = SelectorDockWidget(PARENT)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_creation(self):
        """Test dockwidget and child widgets exist."""
        self.assertIsNotNone(self.dockwidget)
        self.assertIsNotNone(self.dockwidget.PresetComboBox)
        self.assertIsNotNone(self.dockwidget.pushButton_add)
        self.assertIsNotNone(self.dockwidget.pushButton_remove)
        self.assertIsNotNone(self.dockwidget.pushButton_rename)
        self.assertIsNotNone(self.dockwidget.pushButton_duplicate)
        self.assertIsNotNone(self.dockwidget.pushButton_replace)
        self.assertIsNotNone(self.dockwidget.pushButton_up)
        self.assertIsNotNone(self.dockwidget.pushButton_down)


if __name__ == "__main__":
    unittest.main()
