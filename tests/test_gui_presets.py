import copy
import os
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt5 import QtWidgets

from liewa.liewa_gui.main import MainWindow


class PresetUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.local_data = tempfile.TemporaryDirectory()
        self.env_patch = mock.patch.dict(
            os.environ, {"LOCALAPPDATA": self.local_data.name}
        )
        self.env_patch.start()
        with mock.patch.object(MainWindow, "_setup_system_tray", lambda window: None), mock.patch.object(
            MainWindow, "update_status", lambda window, preserve_output=False: None
        ), mock.patch.object(
            MainWindow, "_is_startup_enabled", lambda window: False
        ):
            self.window = MainWindow()
        self.window._apply_loaded_config(self.window._base_default_config())

    def tearDown(self):
        self.window._force_quit = True
        self.window.close()
        self.env_patch.stop()
        self.local_data.cleanup()

    def test_default_and_resolution_scaling(self):
        self.assertEqual("fy4b", self.window._current_satellite)
        self.assertEqual("earth", self.window._current_preset)
        self.assertEqual(
            {"x": 975, "y": 540, "size": 1050},
            self.window.parsed_config["planets"]["fy4b"],
        )
        self.assertEqual(
            {"x": 1950, "y": 1080, "size": 2100},
            self.window._preset_geometry("fy4b", "earth", (3840, 2160)),
        )

    def test_satellite_color_and_custom_state(self):
        self.window.select_satellite("gk2a")
        self.window.select_color_mode("geocolor")
        self.window.select_preset("custom")
        self.window.custom_x_input.setValue(123)
        self.window.custom_y_input.setValue(-45)
        self.window.custom_planet_size_input.setValue(1600)

        self.window.select_satellite("fy4b")
        self.assertEqual(
            {"x": 123, "y": -45, "size": 1600},
            self.window.parsed_config["planets"]["fy4b"],
        )
        self.window.select_satellite("gk2a")
        self.assertEqual(
            "geocolor", self.window.parsed_config["planets"]["gk2a"]["color"]
        )
        self.assertEqual(123, self.window.parsed_config["planets"]["gk2a"]["x"])

    def test_all_full_disk_satellites_are_selectable(self):
        expected = {
            "goes-19",
            "goes-18",
            "himawari",
            "gk2a",
            "fy4b",
        }
        self.assertEqual(expected, set(self.window.satellite_radios))
        self.assertEqual(
            ["fy4b", "gk2a", "himawari", "goes-18", "goes-19"],
            list(self.window.satellite_radios),
        )
        expected_positions = {
            "fy4b": (0, 1),
            "gk2a": (0, 2),
            "himawari": (0, 3),
            "goes-18": (1, 1),
            "goes-19": (1, 2),
        }
        for satellite, button in self.window.satellite_radios.items():
            index = self.window.satellite_grid.indexOf(button)
            row, column, _, _ = self.window.satellite_grid.getItemPosition(index)
            self.assertEqual(expected_positions[satellite], (row, column))
        self.assertFalse(hasattr(self.window, "meteosat9_radio"))
        self.assertFalse(hasattr(self.window, "meteosat0_radio"))

        original_geometry = copy.deepcopy(
            self.window.parsed_config["planets"]["fy4b"]
        )
        self.window.select_satellite("goes-19")
        self.assertEqual("goes-19", self.window._current_satellite)
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.earth_preset_radio.isEnabled())
        self.assertFalse(self.window.china_preset_radio.isEnabled())
        self.assertEqual(
            original_geometry,
            {
                name: self.window.parsed_config["planets"]["goes-19"][name]
                for name in ("x", "y", "size")
            },
        )
        self.assertEqual(
            "adaptive",
            self.window.parsed_config["planets"]["goes-19"]["color"],
        )
        self.assertTrue(self.window.adaptive_color_radio.isVisible())
        self.assertFalse(self.window.fy4b_color_radio.isVisible())

    def test_legacy_goes_config_imports_as_custom(self):
        config = {
            "settings": {"width": 1920, "height": 1080, "bg-color": "#000000"},
            "planets": {
                "goes-18": {
                    "x": 960,
                    "y": 540,
                    "size": 1000,
                    "color": "geocolor",
                }
            },
        }
        ignored = self.window._apply_loaded_config(config)
        self.assertFalse(ignored)
        self.assertEqual("goes-18", self.window._current_satellite)
        self.assertEqual("custom", self.window._current_preset)
        self.assertEqual(
            "geocolor",
            self.window.parsed_config["planets"]["goes-18"]["color"],
        )

    def test_named_preset_applies_default_background_and_preserves_settings(self):
        settings = self.window.parsed_config["settings"]
        settings["show-image-info"] = True
        settings["width"] = 2560
        settings["height"] = 1440
        self.window.selected_size = (2560, 1440)
        self.window.select_satellite("gk2a")
        self.window.select_color_mode("geocolor")
        self.window.select_preset("china")

        self.assertTrue(settings["show-image-info"])
        self.assertEqual((2560, 1440), self.window.selected_size)
        self.assertTrue(settings["background-image"].endswith("cb6be5663982cdd0b307a7d17d3be5f9.jpg"))
        self.assertEqual(
            {
                "x": 1800,
                "y": 2000,
                "size": 4267,
                "color": "geocolor",
                "location": {
                    "continent": "asia",
                    "country": "CN",
                    "subdivision": "2268",
                    "name": "Liaoning",
                    "latitude": 41.237411,
                    "longitude": 122.995547,
                },
            },
            self.window.parsed_config["planets"]["gk2a"],
        )

    def test_thumbnail_mapping_follows_satellite_color_and_layout(self):
        expected_keys = {
            ("fy4b", None, "earth"),
            ("fy4b", None, "china"),
            ("gk2a", "geocolor", "earth"),
            ("gk2a", "geocolor", "china"),
            ("gk2a", "natural_color", "earth"),
            ("gk2a", "natural_color", "china"),
            ("goes-18", "natural_color", "earth"),
            ("goes-18", "geocolor", "earth"),
            ("goes-19", "natural_color", "earth"),
            ("goes-19", "geocolor", "earth"),
            ("himawari", "natural_color", "earth"),
            ("himawari", "natural_color", "china"),
            ("himawari", "geocolor", "earth"),
            ("himawari", "geocolor", "china"),
        }
        self.assertEqual(expected_keys, set(self.window.preset_assets))
        self.assertEqual(
            self.window._preset_asset("goes-19", "earth", "geocolor"),
            self.window._preset_asset("goes-19", "earth", "adaptive"),
        )
        self.assertEqual(
            self.window._preset_asset("gk2a", "china", "geocolor"),
            self.window._preset_asset("gk2a", "china", "adaptive"),
        )

        self.window.select_satellite("goes-19")
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.earth_preset_radio.isEnabled())
        self.assertEqual(
            "adaptive",
            self.window.parsed_config["planets"]["goes-19"]["color"],
        )

        self.window.select_color_mode("natural_color")
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.earth_preset_radio.isEnabled())
        self.assertFalse(self.window.china_preset_radio.isEnabled())
        natural_thumbnail = self.window.preset_thumbnail_label.pixmap().cacheKey()

        self.window.select_color_mode("geocolor")
        self.assertEqual("earth", self.window._current_preset)
        geocolor_thumbnail = self.window.preset_thumbnail_label.pixmap().cacheKey()
        self.assertNotEqual(natural_thumbnail, geocolor_thumbnail)

        self.window.select_color_mode("adaptive")
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.earth_preset_radio.isEnabled())
        self.assertTrue(self.window.custom_controls_widget.isVisible())
        self.assertTrue(self.window.custom_x_input.isReadOnly())

        self.window.select_satellite("himawari")
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.earth_preset_radio.isEnabled())
        self.assertTrue(self.window.china_preset_radio.isEnabled())
        self.window.select_color_mode("natural_color")
        self.window.select_preset("china")
        self.assertEqual("china", self.window._current_preset)
        self.assertEqual(
            (
                "himawari中国区域自然色.yml",
                "himawari中国区域自然色.png",
            ),
            self.window._preset_asset("himawari", "china", "natural_color"),
        )

    def test_startup_checkbox_is_left_of_language_and_updates_registry(self):
        self.assertEqual("开机启动", self.window.startup_checkbox.text())
        startup_index = self.window.header_layout.indexOf(
            self.window.startup_checkbox
        )
        language_index = self.window.header_layout.indexOf(self.window.language_label)
        self.assertLess(startup_index, language_index)

        import winreg

        registry_context = mock.MagicMock()
        registry_key = object()
        registry_context.__enter__.return_value = registry_key
        with mock.patch("winreg.CreateKey", return_value=registry_context), mock.patch(
            "winreg.SetValueEx"
        ) as set_value, mock.patch("winreg.DeleteValue") as delete_legacy_value:
            self.window.startup_checkbox.setChecked(True)
        set_value.assert_called_once_with(
            registry_key,
            "EwaGEO",
            0,
            winreg.REG_SZ,
            self.window._startup_command(),
        )
        delete_legacy_value.assert_called_once_with(registry_key, "Liewa")
        self.assertIn("app.py", self.window._startup_command())

        registry_context = mock.MagicMock()
        registry_key = object()
        registry_context.__enter__.return_value = registry_key
        with mock.patch("winreg.CreateKey", return_value=registry_context), mock.patch(
            "winreg.DeleteValue"
        ) as delete_value:
            self.window.startup_checkbox.setChecked(False)
        self.assertEqual(
            [mock.call(registry_key, "EwaGEO"), mock.call(registry_key, "Liewa")],
            delete_value.call_args_list,
        )

        self.window.change_language(self.window.language_combo.findData("en"))
        self.assertEqual("Start with Windows", self.window.startup_checkbox.text())

    def test_layout_parameters_stay_visible_and_lock_for_named_presets(self):
        self.assertEqual("earth", self.window._current_preset)
        self.assertTrue(self.window.custom_controls_widget.isVisible())
        self.assertTrue(self.window.custom_x_input.isReadOnly())
        self.assertTrue(self.window.custom_y_input.isReadOnly())
        self.assertTrue(self.window.custom_planet_size_input.isReadOnly())
        self.assertEqual(975, self.window.custom_x_input.value())
        self.assertEqual(540, self.window.custom_y_input.value())
        self.assertEqual(1050, self.window.custom_planet_size_input.value())

        controls_height = self.window.custom_controls_widget.sizeHint().height()
        self.window.select_preset("custom")
        self.assertTrue(self.window.custom_controls_widget.isVisible())
        self.assertFalse(self.window.custom_x_input.isReadOnly())
        self.assertEqual(
            QtWidgets.QAbstractSpinBox.UpDownArrows,
            self.window.custom_x_input.buttonSymbols(),
        )
        self.assertEqual(
            controls_height, self.window.custom_controls_widget.sizeHint().height()
        )

        self.window.custom_x_input.setValue(1000)
        self.assertEqual(
            1000, self.window.parsed_config["planets"]["fy4b"]["x"]
        )
        self.window.select_preset("earth")
        self.assertTrue(self.window.custom_controls_widget.isVisible())
        self.assertTrue(self.window.custom_x_input.isReadOnly())
        self.assertEqual(
            QtWidgets.QAbstractSpinBox.NoButtons,
            self.window.custom_x_input.buttonSymbols(),
        )
        self.assertEqual(975, self.window.custom_x_input.value())

    def test_removed_meteosat_config_is_no_longer_supported(self):
        config = {
            "settings": {"width": 1920, "height": 1080, "bg-color": "#000000"},
            "planets": {
                "meteosat-9": {
                    "x": 960,
                    "y": 540,
                    "size": 1000,
                    "color": "geocolor",
                }
            },
        }
        with self.assertRaises(ValueError):
            self.window._apply_loaded_config(config)

    def test_adaptive_mode_uses_cascading_location_selection(self):
        self.window.select_satellite("gk2a")
        planet = self.window.parsed_config["planets"]["gk2a"]
        self.assertEqual("adaptive", planet["color"])
        self.assertEqual("CN", planet["location"]["country"])
        self.assertEqual("2268", planet["location"]["subdivision"])
        self.assertTrue(self.window.location_widget.isVisible())

        color_widgets = [
            self.window.color_row.itemAt(index).widget()
            for index in range(self.window.color_row.count())
            if self.window.color_row.itemAt(index).widget() is not None
        ]
        self.assertLess(
            color_widgets.index(self.window.geocolor_radio),
            color_widgets.index(self.window.adaptive_color_radio),
        )

        north_america = self.window.continent_combo.findData("north_america")
        self.window.continent_combo.setCurrentIndex(north_america)
        united_states = self.window.country_combo.findData("US")
        self.window.country_combo.setCurrentIndex(united_states)
        california = next(
            item
            for item in self.window._country_record("US")["subdivisions"]
            if item["name"] == "California"
        )
        self.window.subdivision_combo.setCurrentIndex(
            self.window.subdivision_combo.findData(str(california["id"]))
        )
        location = planet["location"]
        self.assertEqual("north_america", location["continent"])
        self.assertEqual("US", location["country"])
        self.assertEqual("California", location["name"])
        self.assertEqual(california["latitude"], location["latitude"])

        self.window.select_color_mode("natural_color")
        self.assertFalse(self.window.location_widget.isVisible())
        self.window.select_color_mode("adaptive")
        self.assertTrue(self.window.location_widget.isVisible())
        self.assertEqual("California", planet["location"]["name"])

    def test_legacy_import_selects_first_supported_satellite(self):
        config = {
            "settings": {"width": 2560, "height": 1440, "bg-color": "#112233"},
            "planets": {
                "goes-19": {"x": 1, "y": 2, "size": 3},
                "gk2a": {
                    "x": 1300,
                    "y": 720,
                    "size": 1400,
                    "color": "natural_color",
                },
                "fy4b": {"x": 5, "y": 6, "size": 7},
            },
        }
        ignored = self.window._apply_loaded_config(config)
        self.assertTrue(ignored)
        self.assertEqual(["goes-19"], list(self.window.parsed_config["planets"]))
        self.assertEqual("custom", self.window._current_preset)

    def test_unsupported_import_keeps_current_configuration(self):
        before = copy.deepcopy(self.window.parsed_config)
        config = {
            "settings": {"width": 1920, "height": 1080, "bg-color": "#000000"},
            "planets": {"sdo": {"x": 1, "y": 2, "size": 3}},
        }
        with self.assertRaises(ValueError):
            self.window._apply_loaded_config(config)
        self.assertEqual(before, self.window.parsed_config)

    def test_missing_preset_resource_keeps_current_configuration(self):
        self.window.select_preset("custom")
        before = copy.deepcopy(self.window.parsed_config)
        with mock.patch.object(
            self.window, "_preset_geometry", side_effect=FileNotFoundError("missing")
        ), mock.patch.object(QtWidgets.QMessageBox, "warning") as warning:
            self.window.select_preset("china")
        self.assertEqual(before, self.window.parsed_config)
        self.assertEqual("custom", self.window._current_preset)
        warning.assert_called_once()

    def test_language_and_thumbnail_controls(self):
        self.assertEqual("风云四号B星（中国）", self.window.fy4b_radio.text())
        self.assertEqual("GK-2A（韩国）", self.window.gk2a_radio.text())
        self.window.change_language(self.window.language_combo.findData("en"))
        self.assertEqual("FY-4B (China)", self.window.fy4b_radio.text())
        self.assertEqual("GK-2A (South Korea)", self.window.gk2a_radio.text())
        self.assertEqual("Layout preset", self.window.preset_group.title())
        self.assertEqual(
            "Natural color (recommended for daytime)",
            self.window.natural_color_radio.text(),
        )
        self.assertEqual(
            "GeoColor (recommended for nighttime)",
            self.window.geocolor_radio.text(),
        )
        self.assertEqual(
            "Show image source and time",
            self.window.show_image_info_checkbox.text(),
        )
        self.assertFalse(self.window.preset_thumbnail_label.pixmap().isNull())
        self.assertFalse(hasattr(self.window, "preview_group"))
        self.assertIs(
            self.window.preset_group,
            self.window.show_image_info_checkbox.parent(),
        )
        self.assertIs(
            self.window.show_image_info_checkbox,
            self.window.preset_preview_layout.itemAt(1).widget(),
        )
        self.assertIsNotNone(
            self.window.location_selector_layout.itemAt(
                self.window.location_selector_layout.count() - 1
            ).spacerItem()
        )
        self.assertEqual(150, self.window.continent_combo.maximumWidth())
        self.assertEqual(180, self.window.country_combo.maximumWidth())
        self.assertEqual(220, self.window.subdivision_combo.maximumWidth())

    def test_update_actions_are_at_bottom_of_wallpaper_tab(self):
        self.assertIs(
            self.window.image_compostion,
            self.window.wallpaper_scroll_area.widget(),
        )
        self.assertIs(
            self.window.manage_group,
            self.window.image_layout.itemAt(
                self.window.image_layout.count() - 1
            ).widget(),
        )
        self.assertIs(self.window.image_compostion, self.window.manage_group.parent())
        self.assertEqual(1, self.window.scheduler_layout.count())
        self.assertIs(
            self.window.status_group,
            self.window.scheduler_layout.itemAt(0).widget(),
        )


if __name__ == "__main__":
    unittest.main()
