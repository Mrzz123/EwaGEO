import sys
import os
import subprocess
import pathlib
import platform
import shutil
import traceback
import copy
import json
import yaml
from PIL import Image
from PyQt5 import QtGui, QtCore, QtWidgets
from liewa.liewa_gui.designer_main import Ui_MainWindow
from PyQt5.QtWidgets import QColorDialog, QFileDialog, QDialogButtonBox, QStyle
from PyQt5.QtCore import Qt, QProcess

from liewa.liewa_gui.scheduler import Systemd, Launchd, Schtasks, get_cli_command
from liewa.liewa_cli.utils import get_gui_config_path, get_project_path, get_user_data_path


SUPPORTED_SATELLITES = (
    "fy4b",
    "gk2a",
    "himawari",
    "goes-18",
    "goes-19",
)
REFERENCE_CANVAS_SIZE = (2560, 1440)
DEFAULT_BACKGROUND_NAME = "cb6be5663982cdd0b307a7d17d3be5f9.jpg"
DEFAULT_LOCATION = {
    "continent": "asia",
    "country": "CN",
    "subdivision": "2268",
    "name": "Liaoning",
    "latitude": 41.237411,
    "longitude": 122.995547,
}
CONTINENT_ORDER = (
    "africa",
    "asia",
    "europe",
    "north_america",
    "south_america",
    "oceania",
    "antarctica",
    "other",
)
WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_RUN_VALUE = "EwaGEO"
LEGACY_WINDOWS_RUN_VALUE = "Liewa"
UI_TEXT = {
    "zh_CN": {
        "window_title": "EwaGEO 实时地球壁纸",
        "app_title": "EwaGEO · 实时地球壁纸",
        "language": "语言",
        "start_with_windows": "开机启动",
        "startup_error": "无法更改开机启动设置：{error}",
        "wallpaper_tab": "壁纸设置",
        "scheduler_tab": "自动更新",
        "canvas_group": "画布与分辨率",
        "canvas_size": "预设分辨率",
        "custom_size": "自定义分辨率",
        "width": "宽度",
        "height": "高度",
        "invalid_size": "请输入有效的宽度和高度。",
        "background_group": "背景",
        "background_color": "纯色背景",
        "choose_color": "选择颜色…",
        "background_image": "使用背景图片",
        "browse_image": "选择背景图片…",
        "planet_group": "卫星来源",
        "satellite": "卫星",
        "goes-19": "GOES-19（美洲东部）",
        "goes-18": "GOES-18（美洲西部）",
        "himawari": "Himawari（亚太）",
        "gk2a": "GK-2A（韩国）",
        "fy4b": "风云四号B星（中国）",
        "color_mode": "色彩显示",
        "adaptive": "自动日间 / 夜间模式切换",
        "natural_color": "自然色（建议日间使用）",
        "geocolor": "地理彩色（建议夜间使用）",
        "fy4b_true_color": "真彩色（昼夜融合）",
        "location_hint": "根据所选省/州的平均坐标计算日出日落时间",
        "continent": "大陆",
        "country": "国家",
        "subdivision": "省 / 州",
        "whole_country": "整个国家 / 地区",
        "continent_africa": "非洲",
        "continent_asia": "亚洲",
        "continent_europe": "欧洲",
        "continent_north_america": "北美洲",
        "continent_south_america": "南美洲",
        "continent_oceania": "大洋洲",
        "continent_antarctica": "南极洲",
        "continent_other": "其他",
        "preset_group": "布局预设",
        "preset_earth": "地球",
        "preset_china": "中国区域",
        "preset_custom": "自定义",
        "position_x": "位置 X",
        "position_y": "位置 Y",
        "planet_size": "大小",
        "show_image_info": "显示图像来源及时间",
        "import_yaml": "导入配置文件…",
        "export_yaml": "导出配置文件…",
        "export_wallpaper": "导出当前壁纸…",
        "export_wallpaper_dialog": "导出当前壁纸",
        "save": "保存设置",
        "restore": "恢复默认",
        "saved": "设置已保存",
        "imported": "配置已导入",
        "exported": "配置已导出",
        "wallpaper_exported": "当前壁纸已导出",
        "wallpaper_not_found": "尚未找到已生成的壁纸，请先执行“保存设置并立即更新壁纸”。",
        "wallpaper_invalid": "当前壁纸文件无法读取：{error}",
        "wallpaper_export_failed": "无法导出当前壁纸：{error}",
        "restore_title": "恢复默认设置",
        "restore_question": "确定恢复为 1920×1080、风云四号B星地球预设吗？",
        "hide_to_tray": "隐藏到托盘",
        "scheduler_description": "先设置好壁纸并立即测试；确认效果后选择更新间隔，再启用自动任务。修改间隔后需要再次点击“启用 / 更新”。",
        "manage_group": "更新操作",
        "apply_now": "保存设置并立即更新壁纸",
        "enable_schedule": "启用 / 更新自动任务",
        "interval": "更新间隔",
        "minutes": "分钟（5–720）",
        "disable_schedule": "停用自动更新",
        "status_group": "计划任务状态",
        "running": "自动更新已启用",
        "not_running": "自动更新未启用",
        "success": "成功",
        "error": "错误",
        "downloading": "正在下载卫星图像…",
        "already_running": "已有一个下载任务正在运行。",
        "finished": "任务已结束",
        "processing": "正在更新…",
        "wallpaper_changed": "图像下载成功，桌面壁纸已更新。",
        "download_failed": "下载程序失败，退出代码：{code}",
        "open_file": "选择配置文件",
        "save_file": "导出配置文件",
        "open_image": "选择背景图片",
        "tray_open": "打开 EwaGEO",
        "tray_exit": "彻底退出",
        "tray_notice": "EwaGEO 仍在系统托盘中运行。",
        "missing_settings": "配置文件缺少 settings 部分。",
        "missing_planets": "配置文件缺少 planets 部分。",
        "missing_field": "配置文件缺少 settings.{name}。",
        "unsupported_satellite": "配置中没有可用的全圆盘地球卫星。",
        "extra_layers_ignored": "已采用第一个可用卫星“{name}”，其余图层已忽略。",
        "preset_error": "无法读取布局预设资源：{error}",
        "scheduler_read_error": "无法读取计划任务状态：{error}",
        "scheduler_done": "计划任务操作已完成。",
        "scheduler_failed": "计划任务操作失败：{error}",
        "save_config_failed": "无法保存当前设置：{error}",
        "downloader_start_failed": "无法启动下载程序：{error}",
    },
    "en": {
        "window_title": "EwaGEO Live Earth Wallpaper",
        "app_title": "EwaGEO · Live Earth Wallpaper",
        "language": "Language",
        "start_with_windows": "Start with Windows",
        "startup_error": "Unable to change the startup setting: {error}",
        "wallpaper_tab": "Wallpaper",
        "scheduler_tab": "Automatic updates",
        "canvas_group": "Canvas and resolution",
        "canvas_size": "Resolution preset",
        "custom_size": "Custom resolution",
        "width": "Width",
        "height": "Height",
        "invalid_size": "Enter a valid width and height.",
        "background_group": "Background",
        "background_color": "Solid color",
        "choose_color": "Choose color…",
        "background_image": "Use a background image",
        "browse_image": "Choose background image…",
        "planet_group": "Satellite source",
        "satellite": "Satellite",
        "goes-19": "GOES-19 (Americas East)",
        "goes-18": "GOES-18 (Americas West)",
        "himawari": "Himawari (Asia-Pacific)",
        "gk2a": "GK-2A (South Korea)",
        "fy4b": "FY-4B (China)",
        "color_mode": "Color mode",
        "adaptive": "Automatic day / night mode switching",
        "natural_color": "Natural color (recommended for daytime)",
        "geocolor": "GeoColor (recommended for nighttime)",
        "fy4b_true_color": "True color (day/night blend)",
        "location_hint": "Sunrise and sunset are calculated from the selected state/province's representative coordinates",
        "continent": "Continent",
        "country": "Country",
        "subdivision": "State / Province",
        "whole_country": "Whole country / region",
        "continent_africa": "Africa",
        "continent_asia": "Asia",
        "continent_europe": "Europe",
        "continent_north_america": "North America",
        "continent_south_america": "South America",
        "continent_oceania": "Oceania",
        "continent_antarctica": "Antarctica",
        "continent_other": "Other",
        "preset_group": "Layout preset",
        "preset_earth": "Earth",
        "preset_china": "China region",
        "preset_custom": "Custom",
        "position_x": "Position X",
        "position_y": "Position Y",
        "planet_size": "Size",
        "show_image_info": "Show image source and time",
        "import_yaml": "Import configuration…",
        "export_yaml": "Export configuration…",
        "export_wallpaper": "Export current wallpaper…",
        "export_wallpaper_dialog": "Export current wallpaper",
        "save": "Save settings",
        "restore": "Restore defaults",
        "saved": "Settings saved",
        "imported": "Configuration imported",
        "exported": "Configuration exported",
        "wallpaper_exported": "Current wallpaper exported",
        "wallpaper_not_found": "No generated wallpaper was found. Run Save settings and update wallpaper now first.",
        "wallpaper_invalid": "The current wallpaper file cannot be read: {error}",
        "wallpaper_export_failed": "Unable to export the current wallpaper: {error}",
        "restore_title": "Restore defaults",
        "restore_question": "Restore the 1920×1080 FY-4B Earth preset defaults?",
        "hide_to_tray": "Hide to tray",
        "scheduler_description": "Configure and test the wallpaper, choose an interval, then enable automatic updates. Click Enable / update again after changing the interval.",
        "manage_group": "Update actions",
        "apply_now": "Save settings and update wallpaper now",
        "enable_schedule": "Enable / update automatic task",
        "interval": "Update interval",
        "minutes": "minutes (5–720)",
        "disable_schedule": "Disable automatic updates",
        "status_group": "Scheduled task status",
        "running": "Automatic updates enabled",
        "not_running": "Automatic updates disabled",
        "success": "Success",
        "error": "Error",
        "downloading": "Downloading satellite images…",
        "already_running": "An image download is already running.",
        "finished": "Task finished",
        "processing": "Updating…",
        "wallpaper_changed": "Images downloaded and the desktop wallpaper was updated.",
        "download_failed": "Downloader failed with exit code {code}.",
        "open_file": "Choose configuration file",
        "save_file": "Export configuration",
        "open_image": "Choose background image",
        "tray_open": "Open EwaGEO",
        "tray_exit": "Exit",
        "tray_notice": "EwaGEO is still running in the system tray.",
        "missing_settings": "The configuration is missing a settings section.",
        "missing_planets": "The configuration is missing a planets section.",
        "missing_field": "The configuration is missing settings.{name}.",
        "unsupported_satellite": "The configuration has no supported full-disk Earth satellite.",
        "extra_layers_ignored": "The first supported satellite, “{name}”, was loaded; other layers were ignored.",
        "preset_error": "Unable to read layout preset resources: {error}",
        "scheduler_read_error": "Unable to read scheduler status: {error}",
        "scheduler_done": "Scheduler command completed.",
        "scheduler_failed": "Scheduler command failed: {error}",
        "save_config_failed": "Unable to save the current configuration: {error}",
        "downloader_start_failed": "Unable to start downloader: {error}",
    },
}


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self._force_quit = False
        self._tray_notice_shown = False
        self.tray_icon = None
        self.tray_open_action = None
        self.tray_quit_action = None
        self._updating_configuration_controls = False
        self._current_satellite = "fy4b"
        self._current_preset = "earth"
        self._last_geostationary_color = "adaptive"
        self._preset_cache = {}
        self._default_background_cache = None
        self.preset_assets = self._discover_preset_assets()
        self.location_catalog = self._load_location_catalog()
        self._current_location = copy.deepcopy(DEFAULT_LOCATION)
        self.satellite_radios = {
            "fy4b": self.fy4b_radio,
            "gk2a": self.gk2a_radio,
            "himawari": self.himawari_radio,
            "goes-18": self.goes18_radio,
            "goes-19": self.goes19_radio,
        }
        self._setup_language()
        self._setup_startup_option()
        self._setup_scheduler_interval()
        self._setup_system_tray()
        #########################Image Cmposition#########################

        self.process = None

        self.parsed_config = self._unvalidated_default_config()

        self.satellite_button_group = QtWidgets.QButtonGroup(self)
        for satellite_button in self.satellite_radios.values():
            self.satellite_button_group.addButton(satellite_button)
        self.color_button_group = QtWidgets.QButtonGroup(self)
        for color_button in (
            self.adaptive_color_radio,
            self.natural_color_radio,
            self.geocolor_radio,
            self.fy4b_color_radio,
        ):
            self.color_button_group.addButton(color_button)
        self.preset_button_group = QtWidgets.QButtonGroup(self)
        for preset_button in (
            self.earth_preset_radio,
            self.china_preset_radio,
            self.custom_preset_radio,
        ):
            self.preset_button_group.addButton(preset_button)

        self.dialog_buttons.clicked.connect(self.handle_dialog_btn_click)
        self.close_btn.clicked.connect(self.handle_close_btn_click)
        self.save_yml_btn.clicked.connect(self.save_yml)
        self.export_wallpaper_btn.clicked.connect(self.export_current_wallpaper)
        self.choose_color_btn.clicked.connect(self.open_colorpicker)
        self.browse_bg_file_btn.clicked.connect(self.get_bg_img_file)
        self.browse_config_btn.clicked.connect(self.get_config_file)
        for satellite, satellite_button in self.satellite_radios.items():
            satellite_button.toggled.connect(
                lambda checked, name=satellite: checked
                and self.select_satellite(name)
            )
        self.adaptive_color_radio.toggled.connect(
            lambda checked: checked and self.select_color_mode("adaptive")
        )
        self.natural_color_radio.toggled.connect(
            lambda checked: checked and self.select_color_mode("natural_color")
        )
        self.geocolor_radio.toggled.connect(
            lambda checked: checked and self.select_color_mode("geocolor")
        )
        self.continent_combo.currentIndexChanged.connect(
            self.location_continent_changed
        )
        self.country_combo.currentIndexChanged.connect(self.location_country_changed)
        self.subdivision_combo.currentIndexChanged.connect(
            self.location_subdivision_changed
        )
        self.earth_preset_radio.toggled.connect(
            lambda checked: checked and self.select_preset("earth")
        )
        self.china_preset_radio.toggled.connect(
            lambda checked: checked and self.select_preset("china")
        )
        self.custom_preset_radio.toggled.connect(
            lambda checked: checked and self.select_preset("custom")
        )
        self.custom_x_input.valueChanged.connect(self.update_custom_layout)
        self.custom_y_input.valueChanged.connect(self.update_custom_layout)
        self.custom_planet_size_input.valueChanged.connect(self.update_custom_layout)
        self.size_dropdown.currentIndexChanged.connect(self.canvas_size_change)
        self.x_value_input.textChanged.connect(self.canvas_size_change)
        self.y_value_input.textChanged.connect(self.canvas_size_change)
        self.custom_config_checkbox.toggled.connect(self.toggel_custom_config_mode)
        self.custom_size_checkbox.toggled.connect(self.size_dropdown.setDisabled)
        self.custom_size_checkbox.toggled.connect(self.x_label.setEnabled)
        self.custom_size_checkbox.toggled.connect(self.y_label.setEnabled)
        self.custom_size_checkbox.toggled.connect(self.x_value_input.setEnabled)
        self.custom_size_checkbox.toggled.connect(self.y_value_input.setEnabled)
        self.background_img_checkbox.toggled.connect(self.toggle_background_image)
        self.background_img_checkbox.toggled.connect(
            self.browse_bg_file_btn.setEnabled
        )
        self.background_img_checkbox.toggled.connect(self.choose_color_btn.setDisabled)
        self.show_image_info_checkbox.toggled.connect(self.toggle_image_info)

        pixmapi = QStyle.SP_DialogSaveButton
        icon = self.style().standardIcon(pixmapi)
        self.save_yml_btn.setIcon(icon)
        image_save_icon = QtGui.QIcon.fromTheme("image-x-generic", icon)
        self.export_wallpaper_btn.setIcon(image_save_icon)

        self.drop_down_options = {
            "320x320": (320,320),
            "640x480": (640,480),
            "800x600": (800,600),
            "900x600": (900,600),
            "1024x768": (1024,768),
            "1440x900": (1440,900),
            "1920x1080": (1920,1080),
            "2560x1440": (2560,1440),
            "3840x2160": (3840,2160),
            "7680x4320": (7680,4320),}

        self.selected_size = (1920, 1080)
        self.selected_bg_color = QtGui.QColor(QtCore.Qt.black)

        self.size_error_label.setVisible(False)
        self.choosen_color_label.setStyleSheet(f"background-color: {self.selected_bg_color.name()};\n"f"color: {self.selected_bg_color.name()};")

        self.add_drop_down_options()
        self.size_dropdown.setCurrentIndex(6)

        self._open_yml_file()
        self.update_preview()
        #########################Scheduler###########################
        system = platform.system()
        if system == "Windows":
            self.scheduler = Schtasks()
        elif system == "Darwin":
            self.scheduler = Launchd()
        elif system == "Linux":
            self.scheduler = Systemd()
        else:
            raise Exception("Unsupported operating system!")

        self.status = False

        pixmapi = QStyle.SP_BrowserReload
        icon = self.style().standardIcon(pixmapi)
        self.reload_status_btn.setIcon(icon)

        self.reload_status_btn.clicked.connect(self.update_status)
        self.create_schedueler_btn.clicked.connect(self.create_new_scheduler)
        self.delete_scheduler_btn.clicked.connect(self.delete_scheduler)
        self.test_now_btn.clicked.connect(self.test_now)

        self.update_status()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.setInterval(5000)
        self.timer.start()

        self.tabWidget.setCurrentIndex(0)
        self.show()

    def _t(self, key):
        return UI_TEXT[self.language][key]

    def _setup_language(self):
        self.language_preference_path = pathlib.Path(get_user_data_path()) / "ui_language.txt"
        if self.language_combo.count() >= 2:
            self.language_combo.setItemData(0, "zh_CN")
            self.language_combo.setItemData(1, "en")
        try:
            saved_language = self.language_preference_path.read_text(
                encoding="utf-8"
            ).strip()
        except OSError:
            saved_language = "zh_CN"
        self.language = saved_language if saved_language in UI_TEXT else "zh_CN"
        index = self.language_combo.findData(self.language)
        self.language_combo.blockSignals(True)
        self.language_combo.setCurrentIndex(max(0, index))
        self.language_combo.blockSignals(False)
        self.language_combo.currentIndexChanged.connect(self.change_language)
        self._apply_language()

    def change_language(self, index):
        language = self.language_combo.itemData(index)
        if language not in UI_TEXT:
            return
        self.language = language
        try:
            self.language_preference_path.write_text(language, encoding="utf-8")
        except OSError:
            pass
        self._apply_language()

    def _setup_scheduler_interval(self):
        self.scheduler_interval_path = (
            pathlib.Path(get_user_data_path()) / "scheduler_interval.txt"
        )
        try:
            interval = int(
                self.scheduler_interval_path.read_text(encoding="utf-8").strip()
            )
        except (OSError, ValueError):
            interval = 10
        self.interval_input.setValue(max(5, min(720, interval)))
        self.interval_input.valueChanged.connect(self._save_scheduler_interval)

    @staticmethod
    def _startup_command():
        if getattr(sys, "frozen", False):
            arguments = [sys.executable]
        else:
            app_path = pathlib.Path(__file__).resolve().parents[2] / "app.py"
            arguments = [sys.executable, str(app_path)]
        return subprocess.list2cmdline(arguments)

    def _is_startup_enabled(self):
        if platform.system() != "Windows":
            return False
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                WINDOWS_RUN_KEY,
                0,
                winreg.KEY_QUERY_VALUE,
            ) as registry_key:
                for value_name in (WINDOWS_RUN_VALUE, LEGACY_WINDOWS_RUN_VALUE):
                    try:
                        value, _ = winreg.QueryValueEx(registry_key, value_name)
                        if value:
                            return True
                    except FileNotFoundError:
                        continue
            return False
        except (OSError, ImportError):
            return False

    def _setup_startup_option(self):
        is_windows = platform.system() == "Windows"
        self.startup_checkbox.setVisible(is_windows)
        self.startup_checkbox.blockSignals(True)
        self.startup_checkbox.setChecked(
            is_windows and self._is_startup_enabled()
        )
        self.startup_checkbox.blockSignals(False)
        self.startup_checkbox.toggled.connect(self.toggle_startup)

    def toggle_startup(self, enabled):
        if platform.system() != "Windows":
            return
        try:
            import winreg

            with winreg.CreateKey(
                winreg.HKEY_CURRENT_USER, WINDOWS_RUN_KEY
            ) as registry_key:
                if enabled:
                    winreg.SetValueEx(
                        registry_key,
                        WINDOWS_RUN_VALUE,
                        0,
                        winreg.REG_SZ,
                        self._startup_command(),
                    )
                for value_name in (LEGACY_WINDOWS_RUN_VALUE,) if enabled else (
                    WINDOWS_RUN_VALUE,
                    LEGACY_WINDOWS_RUN_VALUE,
                ):
                    try:
                        winreg.DeleteValue(registry_key, value_name)
                    except FileNotFoundError:
                        pass
        except (OSError, ImportError) as exc:
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(not enabled)
            self.startup_checkbox.blockSignals(False)
            QtWidgets.QMessageBox.warning(
                self,
                self._t("error"),
                self._t("startup_error").format(error=exc),
            )

    def _save_scheduler_interval(self, interval):
        try:
            self.scheduler_interval_path.write_text(str(interval), encoding="utf-8")
        except OSError:
            pass

    def _apply_language(self):
        self.setWindowTitle(self._t("window_title"))
        self.app_title_label.setText(self._t("app_title"))
        self.startup_checkbox.setText(self._t("start_with_windows"))
        self.language_label.setText(self._t("language"))
        self.tabWidget.setTabText(0, self._t("wallpaper_tab"))
        self.tabWidget.setTabText(1, self._t("scheduler_tab"))
        self.canvas_group.setTitle(self._t("canvas_group"))
        self.canvas_size.setText(self._t("canvas_size"))
        self.custom_size_checkbox.setText(self._t("custom_size"))
        self.x_label.setText(self._t("width"))
        self.y_label.setText(self._t("height"))
        self.size_error_label.setText(self._t("invalid_size"))
        self.background_group.setTitle(self._t("background_group"))
        self.background_color.setText(self._t("background_color"))
        self.choose_color_btn.setText(self._t("choose_color"))
        self.background_img_checkbox.setText(self._t("background_image"))
        self.browse_bg_file_btn.setText(self._t("browse_image"))
        self.planet_group.setTitle(self._t("planet_group"))
        self.satellite_label.setText(self._t("satellite"))
        for satellite, satellite_button in self.satellite_radios.items():
            satellite_button.setText(self._t(satellite))
        self.color_label.setText(self._t("color_mode"))
        self.adaptive_color_radio.setText(self._t("adaptive"))
        self.natural_color_radio.setText(self._t("natural_color"))
        self.geocolor_radio.setText(self._t("geocolor"))
        self.fy4b_color_radio.setText(self._t("fy4b_true_color"))
        self.location_hint_label.setText(self._t("location_hint"))
        self.continent_label.setText(self._t("continent"))
        self.country_label.setText(self._t("country"))
        self.subdivision_label.setText(self._t("subdivision"))
        self._sync_location_selectors()
        self.preset_group.setTitle(self._t("preset_group"))
        self.earth_preset_radio.setText(self._t("preset_earth"))
        self.china_preset_radio.setText(self._t("preset_china"))
        self.custom_preset_radio.setText(self._t("preset_custom"))
        self.custom_x_label.setText(self._t("position_x"))
        self.custom_y_label.setText(self._t("position_y"))
        self.custom_planet_size_label.setText(self._t("planet_size"))
        self.show_image_info_checkbox.setText(self._t("show_image_info"))
        self.browse_config_btn.setText(self._t("import_yaml"))
        self.save_yml_btn.setText(self._t("export_yaml"))
        self.export_wallpaper_btn.setText(self._t("export_wallpaper"))
        self.dialog_buttons.button(QDialogButtonBox.Apply).setText(self._t("save"))
        self.dialog_buttons.button(QDialogButtonBox.Cancel).setText(self._t("restore"))
        self.close_btn.button(QDialogButtonBox.Close).setText(self._t("hide_to_tray"))
        self.scheduler_description.setText(self._t("scheduler_description"))
        self.manage_group.setTitle(self._t("manage_group"))
        self.test_now_btn.setText(self._t("apply_now"))
        self.create_schedueler_btn.setText(self._t("enable_schedule"))
        self.interval_label.setText(self._t("interval"))
        self.interval_unit_label.setText(self._t("minutes"))
        self.delete_scheduler_btn.setText(self._t("disable_schedule"))
        self.status_group.setTitle(self._t("status_group"))
        if hasattr(self, "status"):
            self.status_label_text.setText(
                self._t("running") if self.status else self._t("not_running")
            )
        if self.tray_open_action is not None:
            self.tray_open_action.setText(self._t("tray_open"))
        if self.tray_quit_action is not None:
            self.tray_quit_action.setText(self._t("tray_exit"))
        if hasattr(self, "preset_thumbnail_label"):
            self.update_preview()

    #########################Image Cmposition#########################
    def _resource_path(self, *parts):
        return pathlib.Path(get_project_path(), "recources", *parts)

    def _load_location_catalog(self):
        """Load the bundled offline country and first-level subdivision list."""
        fallback_country = {
            "code": "CN",
            "continent": "asia",
            "name": "China",
            "zh": "中国",
            "latitude": 35.86166,
            "longitude": 104.195397,
            "subdivisions": [
                {
                    "id": "2268",
                    "code": "LN",
                    "name": "Liaoning",
                    "zh": "辽宁省",
                    "latitude": DEFAULT_LOCATION["latitude"],
                    "longitude": DEFAULT_LOCATION["longitude"],
                }
            ],
        }
        try:
            catalog_path = pathlib.Path(
                get_project_path(), "recources", "location_catalog.json"
            )
            with catalog_path.open("r", encoding="utf-8") as catalog_file:
                catalog = json.load(catalog_file)
            if not isinstance(catalog, dict) or not isinstance(
                catalog.get("countries"), list
            ):
                raise ValueError("location_catalog.json")
            return catalog
        except (OSError, ValueError, TypeError):
            # Keep the GUI usable even if a damaged installation loses the catalog.
            return {"countries": [fallback_country]}

    def _location_display_name(self, record):
        if self.language == "zh_CN":
            return record.get("zh") or record.get("name") or ""
        return record.get("name") or record.get("zh") or ""

    def _country_record(self, country_code):
        return next(
            (
                country
                for country in self.location_catalog.get("countries", [])
                if country.get("code") == country_code
            ),
            None,
        )

    def _canonical_location(self, country, subdivision="country"):
        selected = None
        if subdivision != "country":
            selected = next(
                (
                    item
                    for item in country.get("subdivisions", [])
                    if str(item.get("id")) == str(subdivision)
                ),
                None,
            )
        source = selected or country
        return {
            "continent": country.get("continent", "other"),
            "country": country.get("code", ""),
            "subdivision": str(selected.get("id")) if selected else "country",
            "name": source.get("name") or country.get("name") or "",
            "latitude": float(source["latitude"]),
            "longitude": float(source["longitude"]),
        }

    def _normalize_location(self, location):
        if not isinstance(location, dict):
            location = DEFAULT_LOCATION
        country = self._country_record(str(location.get("country", "")).upper())
        if country is None:
            country = self._country_record(DEFAULT_LOCATION["country"])
        if country is None:
            country = self.location_catalog["countries"][0]
        subdivision = str(location.get("subdivision", "country"))
        canonical = self._canonical_location(country, subdivision)
        try:
            latitude = float(location.get("latitude", canonical["latitude"]))
            longitude = float(location.get("longitude", canonical["longitude"]))
        except (TypeError, ValueError):
            return canonical
        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return canonical
        # Known catalog selections always use their bundled representative point.
        return canonical

    def _sync_location_selectors(self):
        if not hasattr(self, "continent_combo") or not self.location_catalog:
            return
        location = self._normalize_location(self._current_location)
        country = self._country_record(location["country"])
        if country is None:
            return

        controls = (
            self.continent_combo,
            self.country_combo,
            self.subdivision_combo,
        )
        for control in controls:
            control.blockSignals(True)
        try:
            available_continents = {
                item.get("continent", "other")
                for item in self.location_catalog.get("countries", [])
            }
            self.continent_combo.clear()
            for continent in CONTINENT_ORDER:
                if continent in available_continents:
                    self.continent_combo.addItem(
                        self._t(f"continent_{continent}"), continent
                    )
            continent_index = self.continent_combo.findData(location["continent"])
            self.continent_combo.setCurrentIndex(max(0, continent_index))

            self.country_combo.clear()
            countries = [
                item
                for item in self.location_catalog.get("countries", [])
                if item.get("continent") == location["continent"]
            ]
            countries.sort(key=lambda item: self._location_display_name(item).casefold())
            for item in countries:
                self.country_combo.addItem(
                    self._location_display_name(item), item.get("code")
                )
            country_index = self.country_combo.findData(location["country"])
            self.country_combo.setCurrentIndex(max(0, country_index))

            self.subdivision_combo.clear()
            self.subdivision_combo.addItem(self._t("whole_country"), "country")
            subdivisions = list(country.get("subdivisions", []))
            subdivisions.sort(
                key=lambda item: self._location_display_name(item).casefold()
            )
            for item in subdivisions:
                self.subdivision_combo.addItem(
                    self._location_display_name(item), str(item.get("id"))
                )
            subdivision_index = self.subdivision_combo.findData(
                location["subdivision"]
            )
            self.subdivision_combo.setCurrentIndex(max(0, subdivision_index))
        finally:
            for control in controls:
                control.blockSignals(False)

    def _persist_current_location(self):
        if (
            hasattr(self, "parsed_config")
            and self._current_satellite != "fy4b"
            and self._current_satellite in self.parsed_config.get("planets", {})
        ):
            self.parsed_config["planets"][self._current_satellite][
                "location"
            ] = copy.deepcopy(self._current_location)

    def location_continent_changed(self, index):
        if self._updating_configuration_controls or index < 0:
            return
        continent = self.continent_combo.itemData(index)
        country = next(
            (
                item
                for item in self.location_catalog.get("countries", [])
                if item.get("continent") == continent
            ),
            None,
        )
        if country is None:
            return
        self._current_location = self._canonical_location(country)
        self._sync_location_selectors()
        self._persist_current_location()

    def location_country_changed(self, index):
        if self._updating_configuration_controls or index < 0:
            return
        country = self._country_record(self.country_combo.itemData(index))
        if country is None:
            return
        self._current_location = self._canonical_location(country)
        self._sync_location_selectors()
        self._persist_current_location()

    def location_subdivision_changed(self, index):
        if self._updating_configuration_controls or index < 0:
            return
        country = self._country_record(self.country_combo.currentData())
        if country is None:
            return
        self._current_location = self._canonical_location(
            country, self.subdivision_combo.itemData(index)
        )
        self._persist_current_location()

    @staticmethod
    def _preset_name_from_stem(stem):
        normalized = stem.casefold().replace("_", "-")
        if "中国区域" in stem or "china" in normalized:
            return "china"
        if "地球" in stem or "earth" in normalized:
            return "earth"
        return None

    @staticmethod
    def _preset_color_from_stem(stem, declared_color):
        normalized = stem.casefold().replace("_", "-")
        if "地理彩色" in stem or "geocolor" in normalized or "geo-color" in normalized:
            return "geocolor"
        if "自然色" in stem or "natural-color" in normalized or "naturalcolor" in normalized:
            return "natural_color"
        if "自动" in stem or "adaptive" in normalized:
            return "adaptive"
        return declared_color

    def _discover_preset_assets(self):
        """Discover valid YAML/PNG preset pairs and their declared color mode."""
        assets = {}
        config_dir = self._resource_path("config")
        if not config_dir.is_dir():
            return assets
        for yaml_path in sorted(config_dir.glob("*.yml")):
            image_path = yaml_path.with_suffix(".png")
            preset = self._preset_name_from_stem(yaml_path.stem)
            if preset is None or not image_path.is_file():
                continue
            try:
                if QtGui.QImage(str(image_path)).isNull():
                    continue
                with yaml_path.open("r", encoding="utf-8") as preset_file:
                    preset_config = yaml.safe_load(preset_file)
                planets = preset_config.get("planets", {})
                satellite = next(
                    (name for name in planets if name in SUPPORTED_SATELLITES),
                    None,
                )
                geometry = planets.get(satellite) if satellite else None
                if not isinstance(geometry, dict) or not all(
                    isinstance(geometry.get(name), (int, float))
                    for name in ("x", "y", "size")
                ):
                    continue
                color = (
                    None
                    if satellite == "fy4b"
                    else self._preset_color_from_stem(
                        yaml_path.stem, geometry.get("color")
                    )
                )
                if satellite != "fy4b" and color not in (
                    "adaptive",
                    "natural_color",
                    "geocolor",
                ):
                    continue
                assets[(satellite, color, preset)] = (
                    yaml_path.name,
                    image_path.name,
                )
            except (OSError, ValueError, TypeError, yaml.YAMLError):
                continue
        return assets

    def _preset_asset(self, satellite, preset, color=None):
        if satellite == "fy4b":
            color = None
        elif color is None:
            color = self._last_geostationary_color
        asset = self.preset_assets.get((satellite, color, preset))
        if asset is None and color == "adaptive":
            asset = self.preset_assets.get((satellite, "geocolor", preset))
        return asset

    def _read_preset_geometry(self, satellite, preset, color=None):
        effective_color = (
            None
            if satellite == "fy4b"
            else color or self._last_geostationary_color
        )
        asset = self._preset_asset(satellite, preset, effective_color)
        if asset is None:
            raise KeyError((satellite, effective_color, preset))
        cache_key = (satellite, effective_color, preset)
        if cache_key in self._preset_cache:
            return copy.deepcopy(self._preset_cache[cache_key])
        yaml_name, image_name = asset
        yaml_path = self._resource_path("config", yaml_name)
        image_path = self._resource_path("config", image_name)
        if not yaml_path.is_file() or not image_path.is_file():
            raise FileNotFoundError(f"{yaml_path.name} / {image_path.name}")
        with open(yaml_path, "r", encoding="utf-8") as preset_file:
            preset_config = yaml.safe_load(preset_file)
        geometry = preset_config.get("planets", {}).get(satellite)
        if not isinstance(geometry, dict):
            raise ValueError(f"{yaml_path.name}: planets.{satellite}")
        values = {}
        for name in ("x", "y", "size"):
            value = geometry.get(name)
            if not isinstance(value, (int, float)):
                raise ValueError(f"{yaml_path.name}: planets.{satellite}.{name}")
            values[name] = value
        thumbnail = QtGui.QImage(str(image_path))
        if thumbnail.isNull():
            raise ValueError(image_path.name)
        self._preset_cache[cache_key] = values
        return copy.deepcopy(values)

    def _preset_geometry(self, satellite, preset, canvas_size, color=None):
        source = self._read_preset_geometry(satellite, preset, color)
        width_scale = canvas_size[0] / REFERENCE_CANVAS_SIZE[0]
        height_scale = canvas_size[1] / REFERENCE_CANVAS_SIZE[1]
        size_scale = min(width_scale, height_scale)
        return {
            "x": int(round(source["x"] * width_scale)),
            "y": int(round(source["y"] * height_scale)),
            "size": max(1, int(round(source["size"] * size_scale))),
        }

    def _default_background_path(self):
        if self._default_background_cache is not None:
            return self._default_background_cache
        path = self._resource_path(DEFAULT_BACKGROUND_NAME)
        if not path.is_file():
            raise FileNotFoundError(path.name)
        image = QtGui.QImage(str(path))
        if image.isNull():
            raise ValueError(path.name)
        self._default_background_cache = str(path.resolve())
        return self._default_background_cache

    def _base_default_config(self):
        canvas_size = (1920, 1080)
        return {
            "settings": {
                "width": canvas_size[0],
                "height": canvas_size[1],
                "bg-color": "#000000",
                "background-image": self._default_background_path(),
                "show-image-info": False,
            },
            "planets": {
                "fy4b": self._preset_geometry("fy4b", "earth", canvas_size)
            },
        }

    def _unvalidated_default_config(self):
        return {
            "settings": {
                "width": 1920,
                "height": 1080,
                "bg-color": "#000000",
                "background-image": str(
                    self._resource_path(DEFAULT_BACKGROUND_NAME).resolve()
                ),
                "show-image-info": False,
            },
            "planets": {"fy4b": {"x": 975, "y": 540, "size": 1050}},
        }

    def _open_yml_file(self):
        try:
            config_path = get_gui_config_path()
            with open(config_path, "r", encoding="utf-8") as ymlfile:
                cfg = yaml.safe_load(ymlfile)
            self._apply_loaded_config(cfg, config_path)
        except (OSError, ValueError, KeyError, yaml.YAMLError):
            try:
                self._apply_loaded_config(self._base_default_config())
            except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
                self._apply_loaded_config(
                    self._unvalidated_default_config(),
                    allow_missing_presets=True,
                )
                QtCore.QTimer.singleShot(
                    0,
                    lambda error=str(exc): QtWidgets.QMessageBox.warning(
                        self,
                        self._t("error"),
                        self._t("preset_error").format(error=error),
                    ),
                )

    def _apply_loaded_config(
        self, config, source_path=None, allow_missing_presets=False
    ):
        if not isinstance(config, dict) or not isinstance(config.get("settings"), dict):
            raise ValueError(self._t("missing_settings"))
        if not isinstance(config.get("planets"), dict):
            raise ValueError(self._t("missing_planets"))

        normalized = copy.deepcopy(config)
        settings = normalized["settings"]
        for name in ("width", "height", "bg-color"):
            if name not in settings:
                raise ValueError(self._t("missing_field").format(name=name))

        try:
            canvas_size = (int(settings["width"]), int(settings["height"]))
        except (TypeError, ValueError) as exc:
            raise ValueError(self._t("invalid_size")) from exc
        if canvas_size[0] <= 0 or canvas_size[1] <= 0:
            raise ValueError(self._t("invalid_size"))

        background_path = settings.get("background-image")
        if background_path and source_path:
            background_path = pathlib.Path(background_path).expanduser()
            if not background_path.is_absolute():
                background_path = pathlib.Path(source_path).resolve().parent / background_path
            settings["background-image"] = str(background_path.resolve())

        planets = normalized["planets"]
        selected_satellite = next(
            (name for name in planets if name in SUPPORTED_SATELLITES), None
        )
        if selected_satellite is None:
            raise ValueError(self._t("unsupported_satellite"))
        planet_settings = planets[selected_satellite]
        if not isinstance(planet_settings, dict):
            raise ValueError(self._t("missing_planets"))
        for name in ("x", "y", "size"):
            if not isinstance(planet_settings.get(name), (int, float)):
                raise ValueError(f"planets.{selected_satellite}.{name}")

        planet_settings = copy.deepcopy(planet_settings)
        planet_settings["x"] = max(
            -9999, min(9999, int(round(planet_settings["x"])))
        )
        planet_settings["y"] = max(
            -9999, min(9999, int(round(planet_settings["y"])))
        )
        planet_settings["size"] = max(
            1, min(9999, int(round(planet_settings["size"])))
        )
        if selected_satellite != "fy4b":
            color = planet_settings.get("color", "adaptive")
            if color not in ("adaptive", "natural_color", "geocolor"):
                color = "adaptive"
            planet_settings["color"] = color
            selected_location = self._normalize_location(
                planet_settings.get("location")
            )
            planet_settings["location"] = selected_location
            self._last_geostationary_color = color
        else:
            planet_settings.pop("color", None)
            planet_settings.pop("location", None)
        normalized["planets"] = {selected_satellite: planet_settings}

        selected_preset = "custom"
        geometry = {name: planet_settings[name] for name in ("x", "y", "size")}
        preset_color = planet_settings.get("color")
        try:
            for preset in ("earth", "china"):
                if self._preset_asset(
                    selected_satellite, preset, preset_color
                ) is None:
                    continue
                if geometry == self._preset_geometry(
                    selected_satellite, preset, canvas_size, preset_color
                ):
                    selected_preset = preset
                    break
        except (OSError, ValueError, KeyError, yaml.YAMLError):
            if not allow_missing_presets:
                raise

        self.parsed_config = normalized
        self.selected_size = canvas_size
        self._current_satellite = selected_satellite
        self._current_preset = selected_preset
        if selected_satellite != "fy4b":
            self._current_location = copy.deepcopy(selected_location)
        self.selected_bg_color = QtGui.QColor(settings["bg-color"])
        if not self.selected_bg_color.isValid():
            self.selected_bg_color = QtGui.QColor(QtCore.Qt.black)
            settings["bg-color"] = self.selected_bg_color.name()
        self.choosen_color_label.setStyleSheet(
            f"background-color: {self.selected_bg_color.name()};\n"
            f"color: {self.selected_bg_color.name()};"
        )
        resolution_name = f"{self.selected_size[0]}x{self.selected_size[1]}"
        is_custom = resolution_name not in self.drop_down_options
        controls = (
            self.size_dropdown,
            self.custom_size_checkbox,
            self.x_value_input,
            self.y_value_input,
            self.background_img_checkbox,
            self.show_image_info_checkbox,
        )
        for control in controls:
            control.blockSignals(True)
        if is_custom:
            self.custom_size_checkbox.setChecked(True)
            self.x_value_input.setValue(self.selected_size[0])
            self.y_value_input.setValue(self.selected_size[1])
        else:
            self.custom_size_checkbox.setChecked(False)
            self.size_dropdown.setCurrentText(resolution_name)
            self.x_value_input.setValue(self.selected_size[0])
            self.y_value_input.setValue(self.selected_size[1])
        self.size_dropdown.setEnabled(not is_custom)
        self.x_label.setEnabled(is_custom)
        self.y_label.setEnabled(is_custom)
        self.x_value_input.setEnabled(is_custom)
        self.y_value_input.setEnabled(is_custom)

        has_background = bool(settings.get("background-image"))
        self.background_img_checkbox.setChecked(has_background)
        self.browse_bg_file_btn.setEnabled(has_background)
        self.choose_color_btn.setEnabled(not has_background)
        self.show_image_info_checkbox.setChecked(
            bool(settings.get("show-image-info", False))
        )
        for control in controls:
            control.blockSignals(False)
        self._sync_satellite_controls()
        self.update_preview()
        return len(planets) > 1 or next(iter(planets), None) != selected_satellite

    def _sync_satellite_controls(self):
        self._updating_configuration_controls = True
        try:
            for satellite, satellite_button in self.satellite_radios.items():
                satellite_button.setChecked(satellite == self._current_satellite)
            has_cira_color = self._current_satellite != "fy4b"
            for button in (
                self.adaptive_color_radio,
                self.natural_color_radio,
                self.geocolor_radio,
            ):
                button.setVisible(has_cira_color)
            self.fy4b_color_radio.setVisible(not has_cira_color)
            color = self._last_geostationary_color
            self.adaptive_color_radio.setChecked(has_cira_color and color == "adaptive")
            self.natural_color_radio.setChecked(
                has_cira_color and color == "natural_color"
            )
            self.geocolor_radio.setChecked(has_cira_color and color == "geocolor")
            self.fy4b_color_radio.setChecked(not has_cira_color)
            self.location_widget.setVisible(has_cira_color and color == "adaptive")
            self._sync_location_selectors()

            self.earth_preset_radio.setEnabled(
                self._preset_asset(self._current_satellite, "earth") is not None
            )
            self.china_preset_radio.setEnabled(
                self._preset_asset(self._current_satellite, "china") is not None
            )
            self.earth_preset_radio.setChecked(self._current_preset == "earth")
            self.china_preset_radio.setChecked(self._current_preset == "china")
            self.custom_preset_radio.setChecked(self._current_preset == "custom")
            is_custom = self._current_preset == "custom"
            self.custom_controls_widget.setVisible(True)
            geometry = self.parsed_config["planets"][self._current_satellite]
            for control, name in (
                (self.custom_x_input, "x"),
                (self.custom_y_input, "y"),
                (self.custom_planet_size_input, "size"),
            ):
                control.blockSignals(True)
                control.setValue(int(round(geometry[name])))
                control.setReadOnly(not is_custom)
                control.setButtonSymbols(
                    QtWidgets.QAbstractSpinBox.UpDownArrows
                    if is_custom
                    else QtWidgets.QAbstractSpinBox.NoButtons
                )
                control.setFocusPolicy(Qt.StrongFocus if is_custom else Qt.NoFocus)
                control.blockSignals(False)
        finally:
            self._updating_configuration_controls = False
        self.update_preset_thumbnail()

    def _apply_named_preset(self, satellite, preset):
        geometry = self._preset_geometry(satellite, preset, self.selected_size)
        if satellite != "fy4b":
            geometry["color"] = self._last_geostationary_color
            geometry["location"] = copy.deepcopy(self._current_location)
        background_path = self._default_background_path()
        self.parsed_config["settings"]["background-image"] = background_path
        self.background_img_checkbox.blockSignals(True)
        self.background_img_checkbox.setChecked(True)
        self.background_img_checkbox.blockSignals(False)
        self.browse_bg_file_btn.setEnabled(True)
        self.choose_color_btn.setEnabled(False)
        self.parsed_config["planets"] = {satellite: geometry}

    def select_satellite(self, satellite):
        if self._updating_configuration_controls or satellite == self._current_satellite:
            return
        geometry = copy.deepcopy(
            self.parsed_config["planets"][self._current_satellite]
        )
        geometry.pop("color", None)
        geometry.pop("location", None)
        has_named_preset = (
            self._preset_asset(
                satellite, self._current_preset, self._last_geostationary_color
            )
            is not None
        )
        if self._current_preset in ("earth", "china") and has_named_preset:
            try:
                self._apply_named_preset(satellite, self._current_preset)
            except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
                QtWidgets.QMessageBox.warning(
                    self,
                    self._t("error"),
                    self._t("preset_error").format(error=exc),
                )
                self._sync_satellite_controls()
                return
        else:
            if satellite != "fy4b":
                geometry["color"] = self._last_geostationary_color
                geometry["location"] = copy.deepcopy(self._current_location)
            self.parsed_config["planets"] = {satellite: geometry}
            if self._current_preset in ("earth", "china"):
                self._current_preset = "custom"
        self._current_satellite = satellite
        self._sync_satellite_controls()
        self.update_preview()

    def select_color_mode(self, color):
        if self._updating_configuration_controls or self._current_satellite == "fy4b":
            return
        self._last_geostationary_color = color
        self.parsed_config["planets"][self._current_satellite]["color"] = color
        if color == "adaptive":
            self._persist_current_location()
        if self._current_preset in ("earth", "china"):
            if self._preset_asset(
                self._current_satellite, self._current_preset, color
            ) is None:
                self._current_preset = "custom"
            else:
                try:
                    self._apply_named_preset(
                        self._current_satellite, self._current_preset
                    )
                except (OSError, ValueError, KeyError, yaml.YAMLError):
                    self._current_preset = "custom"
        else:
            geometry = self.parsed_config["planets"][self._current_satellite]
            current_geometry = {
                name: geometry[name] for name in ("x", "y", "size")
            }
            for preset in ("earth", "china"):
                if self._preset_asset(
                    self._current_satellite, preset, color
                ) is None:
                    continue
                try:
                    expected = self._preset_geometry(
                        self._current_satellite,
                        preset,
                        self.selected_size,
                        color,
                    )
                except (OSError, ValueError, KeyError, yaml.YAMLError):
                    continue
                if current_geometry == expected:
                    self._current_preset = preset
                    break
        self._sync_satellite_controls()

    def select_preset(self, preset):
        if self._updating_configuration_controls or preset == self._current_preset:
            return
        if preset in ("earth", "china"):
            if self._preset_asset(self._current_satellite, preset) is None:
                self._current_preset = "custom"
                self._sync_satellite_controls()
                return
            try:
                self._apply_named_preset(self._current_satellite, preset)
            except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
                QtWidgets.QMessageBox.warning(
                    self,
                    self._t("error"),
                    self._t("preset_error").format(error=exc),
                )
                self._sync_satellite_controls()
                return
        else:
            geometry = self.parsed_config["planets"][self._current_satellite]
            geometry["x"] = max(-9999, min(9999, int(round(geometry["x"]))))
            geometry["y"] = max(-9999, min(9999, int(round(geometry["y"]))))
            geometry["size"] = max(1, min(9999, int(round(geometry["size"]))))
        self._current_preset = preset
        self._sync_satellite_controls()
        self.update_preview()

    def update_custom_layout(self):
        if self._updating_configuration_controls or self._current_preset != "custom":
            return
        geometry = self.parsed_config["planets"][self._current_satellite]
        geometry.update(
            {
                "x": self.custom_x_input.value(),
                "y": self.custom_y_input.value(),
                "size": self.custom_planet_size_input.value(),
            }
        )
        self.update_preview()

    def _save_runtime_config(self):
        config_path = pathlib.Path(get_user_data_path()) / "gui_config.yml"
        with open(config_path, "w", encoding="utf-8") as config_file:
            yaml.safe_dump(self.parsed_config, config_file, sort_keys=False)
        return str(config_path)

    def open_colorpicker(self):
            color = QColorDialog.getColor()
            if color.isValid():
                self.selected_bg_color = color
                self.choosen_color_label.setStyleSheet(f"background-color: {self.selected_bg_color.name()};\n"f"color: {self.selected_bg_color.name()};")
                self.parsed_config['settings']['bg-color'] = self.selected_bg_color.name()
                self.update_preview()

    def handle_dialog_btn_click(self, button):
        role = self.dialog_buttons.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self._save_runtime_config()
            self.save_feedback_label.setText(self._t("saved"))

        elif role == QDialogButtonBox.RejectRole:
            answer = QtWidgets.QMessageBox.question(
                self,
                self._t("restore_title"),
                self._t("restore_question"),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if answer != QtWidgets.QMessageBox.Yes:
                return
            try:
                self._last_geostationary_color = "adaptive"
                self._current_location = copy.deepcopy(DEFAULT_LOCATION)
                self._apply_loaded_config(self._base_default_config())
            except (OSError, ValueError, KeyError, yaml.YAMLError) as exc:
                QtWidgets.QMessageBox.warning(
                    self,
                    self._t("error"),
                    self._t("preset_error").format(error=exc),
                )

    def handle_close_btn_click(self,button):
        self.close()

    def _setup_system_tray(self):
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = QtWidgets.QApplication.windowIcon()
        if icon.isNull():
            icon = self.style().standardIcon(QStyle.SP_ComputerIcon)

        self.tray_icon = QtWidgets.QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("EwaGEO")

        tray_menu = QtWidgets.QMenu(self)
        self.tray_open_action = tray_menu.addAction(self._t("tray_open"))
        self.tray_open_action.triggered.connect(self.restore_from_tray)
        tray_menu.addSeparator()
        self.tray_quit_action = tray_menu.addAction(self._t("tray_exit"))
        self.tray_quit_action.triggered.connect(self.quit_from_tray)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.handle_tray_activation)
        self.tray_icon.show()

    def handle_tray_activation(self, reason):
        if reason in (
            QtWidgets.QSystemTrayIcon.Trigger,
            QtWidgets.QSystemTrayIcon.DoubleClick,
        ):
            self.restore_from_tray()

    def restore_from_tray(self):
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def quit_from_tray(self):
        self._force_quit = True
        if self.tray_icon is not None:
            self.tray_icon.hide()
        self.close()
        QtWidgets.QApplication.quit()

    def get_config_file(self):
        try:
            fname = QFileDialog.getOpenFileName(self, self._t("open_file"),"", "YAML files (*.yml *.yaml)")[0]
            if not fname:
                return
            with open(fname, "r", encoding="utf-8") as ymlfile:
                cfg = yaml.safe_load(ymlfile)
            ignored_layers = self._apply_loaded_config(cfg, fname)
            self.save_feedback_label.setText(self._t("imported"))
            if ignored_layers:
                QtWidgets.QMessageBox.information(
                    self,
                    self._t("imported"),
                    self._t("extra_layers_ignored").format(
                        name=self._t(self._current_satellite)
                    ),
                )
        except (OSError, ValueError, yaml.YAMLError) as exc:
            QtWidgets.QMessageBox.warning(self, self._t("error"), str(exc))

    def toggel_custom_config_mode(self,state):
        # Kept for compatibility with older generated UI files. Importing YAML is
        # now an explicit button and no longer clears the current configuration.
        return

    def get_bg_img_file(self):
        fname = QFileDialog.getOpenFileName(
            self,
            self._t("open_image"),
            "",
            "Background files (*.png *.jpg *.jpeg *.bmp)",
        )[0]
        if not fname:
            return

        source = pathlib.Path(fname).resolve()
        destination = pathlib.Path(get_user_data_path()) / f"background_source{source.suffix.lower()}"
        if source != destination.resolve():
            shutil.copy2(source, destination)
        self.parsed_config["settings"]["background-image"] = str(destination)
        self.background_img_checkbox.setChecked(True)
        self.update_preview()

    def toggle_background_image(self, enabled):
        if not enabled:
            self.parsed_config["settings"].pop("background-image", None)
        self.update_preview()

    def toggle_image_info(self, enabled):
        self.parsed_config["settings"]["show-image-info"] = bool(enabled)
        self.update_preview()

    def save_yml(self):
        fname = QFileDialog.getSaveFileName(
            self, self._t("save_file"), "ewageo_config.yml", "YAML files (*.yml)"
        )[0]
        if not fname:
            return
        try:
            with open(fname, "w", encoding="utf-8") as file:
                yaml.safe_dump(self.parsed_config, file, sort_keys=False)
            self.save_feedback_label.setText(self._t("exported"))
        except (OSError, yaml.YAMLError) as exc:
            QtWidgets.QMessageBox.warning(self, self._t("error"), str(exc))

    def export_current_wallpaper(self):
        source = pathlib.Path(get_user_data_path()) / "backgroundImage.png"
        if not source.is_file():
            QtWidgets.QMessageBox.warning(
                self, self._t("error"), self._t("wallpaper_not_found")
            )
            return

        try:
            with Image.open(source) as wallpaper:
                wallpaper.verify()
        except (OSError, ValueError) as exc:
            QtWidgets.QMessageBox.warning(
                self,
                self._t("error"),
                self._t("wallpaper_invalid").format(error=exc),
            )
            return

        timestamp = QtCore.QDateTime.currentDateTime().toString("yyyyMMdd-HHmm")
        default_name = f"ewageo-wallpaper-{timestamp}.png"
        destination = QFileDialog.getSaveFileName(
            self,
            self._t("export_wallpaper_dialog"),
            default_name,
            "PNG images (*.png)",
        )[0]
        if not destination:
            return

        destination = pathlib.Path(destination)
        if not destination.suffix:
            destination = destination.with_suffix(".png")

        try:
            if source.resolve() != destination.resolve():
                shutil.copy2(source, destination)
            self.save_feedback_label.setText(self._t("wallpaper_exported"))
        except (OSError, shutil.Error) as exc:
            QtWidgets.QMessageBox.warning(
                self,
                self._t("error"),
                self._t("wallpaper_export_failed").format(error=exc),
            )

    def add_drop_down_options(self):
        for i,el in enumerate(self.drop_down_options):
            self.size_dropdown.addItem(el)
            self.size_dropdown.setItemText(i,el)

    def canvas_size_change(self):
        if self.x_value_input.isEnabled():
            self.selected_size = (int(self.x_value_input.text()),int(self.y_value_input.text()))
        else:
            self.selected_size = self.drop_down_options[self.size_dropdown.currentText()]
        try:
            self.parsed_config["settings"]["width"] = self.selected_size[0]
            self.parsed_config["settings"]["height"] = self.selected_size[1]
            if (
                self._current_preset in ("earth", "china")
                and self._preset_asset(
                    self._current_satellite, self._current_preset
                )
                is not None
            ):
                geometry = self._preset_geometry(
                    self._current_satellite,
                    self._current_preset,
                    self.selected_size,
                )
                if self._current_satellite != "fy4b":
                    geometry["color"] = self._last_geostationary_color
                    geometry["location"] = copy.deepcopy(self._current_location)
                self.parsed_config["planets"] = {
                    self._current_satellite: geometry
                }
            self.size_error_label.setVisible(False)
            self.update_preview()
        except (ZeroDivisionError, OSError, ValueError, KeyError, yaml.YAMLError):
            self.size_error_label.setVisible(True)

    def update_preview(self):
        self.update_preset_thumbnail()

    def update_preset_thumbnail(self):
        target_size = self.preset_thumbnail_label.size()
        if (
            self._current_preset in ("earth", "china")
            and self._preset_asset(
                self._current_satellite, self._current_preset
            )
            is not None
        ):
            _, image_name = self._preset_asset(
                self._current_satellite, self._current_preset
            )
            pixmap = QtGui.QPixmap(
                str(self._resource_path("config", image_name))
            )
            if pixmap.isNull():
                self.preset_thumbnail_label.clear()
                return
            self.preset_thumbnail_label.setPixmap(
                pixmap.scaled(
                    target_size,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
            return

        pixmap = QtGui.QPixmap(target_size)
        pixmap.fill(self.selected_bg_color)
        painter = QtGui.QPainter(pixmap)
        background_path = self.parsed_config["settings"].get("background-image")
        background = QtGui.QPixmap(background_path) if background_path else QtGui.QPixmap()
        if not background.isNull():
            painter.drawPixmap(
                pixmap.rect(),
                background.scaled(
                    target_size,
                    Qt.IgnoreAspectRatio,
                    Qt.SmoothTransformation,
                ),
            )
        geometry = self.parsed_config["planets"][self._current_satellite]
        scale_x = target_size.width() / self.selected_size[0]
        scale_y = target_size.height() / self.selected_size[1]
        earth_size = geometry["size"] * min(scale_x, scale_y)
        earth_rect = QtCore.QRectF(
            geometry["x"] * scale_x - earth_size / 2,
            geometry["y"] * scale_y - earth_size / 2,
            earth_size,
            earth_size,
        )
        painter.setPen(QtGui.QPen(QtGui.QColor(80, 155, 255), 2))
        painter.setBrush(QtGui.QColor(30, 105, 210, 180))
        painter.drawEllipse(earth_rect)
        if self.parsed_config["settings"].get("show-image-info", False):
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QColor(0, 0, 0, 170))
            painter.drawRect(
                target_size.width() - 138,
                6,
                132,
                38,
            )
        painter.end()
        self.preset_thumbnail_label.setPixmap(pixmap)

    ##############################Scheduler###########################################

    def update_status(self, preserve_output=False):
        try:
            output, self.status = self.scheduler.update()
        except Exception as exc:
            output = self._t("scheduler_read_error").format(error=exc)
            self.status = False

        if self.status:
            icon = self.style().standardIcon(QStyle.SP_DialogYesButton).pixmap(20,20)
            self.status_label_text.setText(self._t("running"))
        else:
            icon = self.style().standardIcon(QStyle.SP_DialogNoButton).pixmap(20,20)
            self.status_label_text.setText(self._t("not_running"))
        self.status_label_color.setPixmap(icon)
        if not preserve_output and len(output) >= 5:
            self.status_output.clear()
            self.status_output.setPlainText(output)

    def create_new_scheduler(self):
        if not self._save_config_for_run():
            return
        interval = self.interval_input.value()
        self._save_scheduler_interval(interval)
        self._run_scheduler_action(
            lambda: self.scheduler.create_scheduler(interval_minutes=interval)
        )

    def delete_scheduler(self):
        self._run_scheduler_action(self.scheduler.delete_scheduler)

    def reload_scheduler(self):
        if not self._save_config_for_run():
            return
        self._run_scheduler_action(self.scheduler.reload_scheduler)

    def _run_scheduler_action(self, action):
        try:
            result = action()
            if isinstance(result, tuple):
                output, succeeded = result
            else:
                output, succeeded = self._t("scheduler_done"), True
        except Exception as exc:
            output, succeeded = self._t("scheduler_failed").format(error=exc), False

        self.update_status(preserve_output=True)
        prefix = self._t("success") if succeeded else self._t("error")
        self.status_output.setPlainText(f"{prefix}: {output}")

    def _save_config_for_run(self):
        try:
            self._save_runtime_config()
            return True
        except (OSError, ValueError, yaml.YAMLError) as exc:
            self.status_output.setPlainText(
                self._t("save_config_failed").format(error=exc)
            )
            return False

    def test_now(self):
        if not self._save_config_for_run():
            return
        system = platform.system()
        if system == "Windows":
            if self.process is not None:
                self.status_output.append(self._t("already_running"))
                return

            self.status_output.clear()
            self.status_output.setPlainText(self._t("downloading"))
            command = get_cli_command()
            self.process = QProcess(self)
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.stateChanged.connect(self.handle_state)
            self.process.errorOccurred.connect(self.process_error)
            self.process.finished.connect(self.process_finished)
            self.process.start(command[0], command[1:])


        elif system == "Linux":
            self.status_output.clear()
            cwd = pathlib.Path(__file__).parent.resolve()
            liewa_gui = os.path.dirname(cwd)
            liewa_gui = os.path.dirname(liewa_gui)
            liewa_cli = os.path.join(liewa_gui,"cli.py")
            if self.process is None:
                self.process = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
                self.process.readyReadStandardOutput.connect(self.handle_stdout)
                self.process.readyReadStandardError.connect(self.handle_stderr)
                self.process.stateChanged.connect(self.handle_state)
                self.process.finished.connect(self.process_finished)  # Clean up once complete.
                self.process.start(os.popen('which python3').read().strip()+" "+liewa_cli)
            # output = subprocess.check_output(liewa_cli)
            # self.status_output.append(output.decode('utf-8'))
        elif system == "Darwin":
            self.status_output.clear()
            cwd = pathlib.Path(__file__).parent.resolve()
            liewa_gui = os.path.dirname(cwd)
            liewa_gui = os.path.dirname(liewa_gui)
            liewa_cli = os.path.join(liewa_gui,"cli.py")
            if self.process is None:
                self.process = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
                self.process.readyReadStandardOutput.connect(self.handle_stdout)
                self.process.readyReadStandardError.connect(self.handle_stderr)
                self.process.stateChanged.connect(self.handle_state)
                self.process.finished.connect(self.process_finished)  # Clean up once complete.
                self.process.start(os.popen('which python3').read().strip()+" "+liewa_cli)
            # output = subprocess.check_output(liewa_cli)
            # self.status_output.append(output.decode('utf-8'))

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8", errors="replace")
        self.status_output.append(stderr)

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8", errors="replace")
        self.status_output.append(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: self._t("finished"),
            QProcess.Starting: self._t("downloading"),
            QProcess.Running: self._t("processing"),
        }
        state_name = states[state]
        self.status_output.append(state_name)

    def process_error(self, error):
        if self.process is not None:
            process = self.process
            self.status_output.append(
                self._t("downloader_start_failed").format(error=process.errorString())
            )
            if error == QProcess.FailedToStart:
                process.deleteLater()
                self.process = None

    def process_finished(self, exit_code, exit_status):
        if exit_status == QProcess.NormalExit and exit_code == 0:
            self.status_output.append(self._t("wallpaper_changed"))
        else:
            self.status_output.append(self._t("download_failed").format(code=exit_code))
        self.process = None

    def closeEvent(self, event):
        if self.tray_icon is not None and not self._force_quit:
            event.ignore()
            self.hide()
            if not self._tray_notice_shown:
                self.tray_icon.showMessage(
                    "EwaGEO",
                    self._t("tray_notice"),
                    QtWidgets.QSystemTrayIcon.Information,
                    3000,
                )
                self._tray_notice_shown = True
            return

        self.timer.stop()
        if self.process is not None and self.process.state() != QProcess.NotRunning:
            self.process.terminate()
            if not self.process.waitForFinished(1500):
                self.process.kill()
                self.process.waitForFinished(1000)
        super().closeEvent(event)


def _handle_unhandled_exception(exc_type, exc_value, exc_traceback):
    """Keep exceptions in Qt callbacks visible instead of terminating silently."""
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    try:
        log_dir = pathlib.Path(os.getenv("LOCALAPPDATA", pathlib.Path.home())) / "EwaGEO"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "ewageo-error.log").write_text(details, encoding="utf-8")
    except Exception:
        pass

    try:
        QtWidgets.QMessageBox.critical(
            None,
            "EwaGEO error",
            f"An unexpected error occurred. The application will stay open.\n\n{exc_value}",
        )
    except Exception:
        pass

def startup():
    sys.excepthook = _handle_unhandled_exception
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(str(pathlib.Path(__file__).with_name("icon.png"))))
    window = MainWindow()
    if window.tray_icon is not None:
        app.setQuitOnLastWindowClosed(False)
    app.exec()


# if __name__ == '__main__':
#     startup()
