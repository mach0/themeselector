"""Translations Test."""

import os
import unittest

from utilities import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class SafeTranslationsTest(unittest.TestCase):
    """Test translations work."""

    def setUp(self):
        """Runs before each test."""
        if QGIS_APP is None:
            self.skipTest("QGIS environment not available")

    def test_qm_files_exist(self):
        """Test compiled translation files exist."""
        i18n_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, 'themeselector', 'i18n'
            )
        )
        de_qm = os.path.join(i18n_dir, 'de.qm')
        self.assertTrue(os.path.exists(de_qm), f"Missing {de_qm}")


if __name__ == '__main__':
    unittest.main()
