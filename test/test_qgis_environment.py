"""Tests for QGIS functionality."""

import unittest

from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class QGISTest(unittest.TestCase):
    """Test the QGIS Environment."""

    def test_qgis_environment(self):
        if QGIS_APP is None:
            self.skipTest("QGIS environment not available")
        from qgis.core import QgsProject
        self.assertIsNotNone(QgsProject.instance())


if __name__ == '__main__':
    unittest.main()
