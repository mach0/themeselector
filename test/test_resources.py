"""Resources test."""

import os
import unittest


class ResourcesTest(unittest.TestCase):
    """Test icon resources exist."""

    def test_icons_exist(self):
        img_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), os.pardir, 'themeselector', 'img'
            )
        )
        required_icons = [
            'selector.png',
            'selector.svg',
            'mActionArrowLeft.svg',
            'mActionArrowRight.svg',
        ]
        for icon in required_icons:
            icon_path = os.path.join(img_dir, icon)
            self.assertTrue(
                os.path.exists(icon_path),
                f"Missing icon {icon_path}"
            )


if __name__ == '__main__':
    unittest.main()
