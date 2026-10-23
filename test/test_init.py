"""Tests QGIS plugin init."""

import configparser
import logging
import os
import unittest

LOGGER = logging.getLogger('QGIS')


class TestInit(unittest.TestCase):
    """Test that the plugin init is usable for QGIS."""

    def test_read_init(self):
        """Test that the plugin metadata will validate on plugins.qgis.org."""
        required_metadata = [
            'name',
            'description',
            'version',
            'qgisMinimumVersion',
            'email',
            'author',
        ]

        test_dir = os.path.dirname(__file__)
        file_path = os.path.abspath(
            os.path.join(test_dir, os.pardir, 'themeselector', 'metadata.txt')
        )
        if not os.path.exists(file_path):
            file_path = os.path.abspath(
                os.path.join(test_dir, os.pardir, 'metadata.txt')
            )

        self.assertTrue(
            os.path.exists(file_path),
            f"Cannot find metadata.txt at {file_path}"
        )
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read(file_path, encoding='utf-8')
        self.assertTrue(
            parser.has_section('general'),
            f'Cannot find section "general" in {file_path}'
        )
        metadata = dict(parser.items('general'))

        for expectation in required_metadata:
            self.assertIn(
                expectation,
                metadata,
                f'Cannot find metadata "{expectation}" in {file_path}'
            )


if __name__ == '__main__':
    unittest.main()
