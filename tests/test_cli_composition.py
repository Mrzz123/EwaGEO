import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from PIL import Image

from liewa.liewa_cli.image_parser import parse_image
from liewa.liewa_cli.utils import get_project_path


class CliCompositionTests(unittest.TestCase):
    def test_single_satellite_ui_config_composes_wallpaper(self):
        config = {
            "settings": {
                "width": 320,
                "height": 180,
                "bg-color": "#000000",
                "background-image": str(
                    Path(get_project_path())
                    / "recources"
                    / "cb6be5663982cdd0b307a7d17d3be5f9.jpg"
                ),
                "show-image-info": False,
            },
            "planets": {"fy4b": {"x": 160, "y": 90, "size": 120}},
        }
        satellite_image = Image.new("RGB", (200, 200), "white")
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.yml"
            config_path.write_text(
                yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
            )
            with mock.patch(
                "liewa.liewa_cli.image_parser.load_geostationary",
                return_value=satellite_image,
            ):
                wallpaper = parse_image(config_path)

        self.assertEqual((320, 180), wallpaper.size)
        self.assertNotEqual((0, 0, 0), wallpaper.getpixel((160, 90)))


if __name__ == "__main__":
    unittest.main()
