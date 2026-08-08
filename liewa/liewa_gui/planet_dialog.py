from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QLabel,
    QSpinBox,
)

from liewa.liewa_gui.designer_planet import Ui_Dialog


PLANET_TEXT = {
    "zh_CN": {
        "title": "添加或编辑卫星图层",
        "satellite": "卫星 / 图像源",
        "x": "中心位置 X",
        "y": "中心位置 Y",
        "width": "宽度",
        "height": "高度",
        "size": "地球直径",
        "scale": "缩放等级",
        "latitude": "纬度",
        "longitude": "经度",
        "color": "颜色模式",
        "bandwidth": "太阳波段",
        "fit": "填充方式",
        "apply": "确定",
        "cancel": "取消",
    },
    "en": {
        "title": "Add or edit satellite layer",
        "satellite": "Satellite / image source",
        "x": "Center X",
        "y": "Center Y",
        "width": "Width",
        "height": "Height",
        "size": "Earth diameter",
        "scale": "Scale",
        "latitude": "Latitude",
        "longitude": "Longitude",
        "color": "Color mode",
        "bandwidth": "Solar band",
        "fit": "Fit",
        "apply": "OK",
        "cancel": "Cancel",
    },
}

SATELLITE_NAMES = {
    "zh_CN": {
        "goes-19": "GOES-19（美洲东部）",
        "goes-18": "GOES-18（美洲西部）",
        "himawari": "Himawari（亚太）",
        "gk2a": "GK-2A（东亚）",
        "fy4b": "风云四号B星（中国 / 西太平洋）",
        "sdo": "SDO（太阳）",
        "apod": "NASA 每日天文图",
        "sentinel": "Sentinel 地表影像",
    },
    "en": {
        "fy4b": "FY-4B (China / Western Pacific)",
    },
}

OPTION_NAMES = {
    "zh_CN": {
        "natural_color": "自然色（建议日间使用）",
        "geocolor": "地理彩色（建议夜间使用）",
        "adaptive": "自动日间 / 夜间模式切换",
        "fill": "拉伸填充",
        "contain": "完整显示",
        "cover": "裁切铺满",
    },
    "en": {
        "natural_color": "Natural color (recommended for daytime)",
        "geocolor": "GeoColor (recommended for nighttime)",
        "adaptive": "Automatic day / night mode switching",
        "fill": "Stretch to fill",
        "contain": "Contain",
        "cover": "Crop to cover",
    },
}


class PlanetDialog(QDialog, Ui_Dialog):
    def __init__(self, planet, planet_config, view_config, language="zh_CN"):
        super(PlanetDialog, self).__init__()
        self.setupUi(self)

        self.language = language if language in PLANET_TEXT else "zh_CN"
        self.planet = planet
        self.settings = planet_config
        self.filter = {
            "geostationary": ["x", "y", "size", "color"],
            "fy4b": ["x", "y", "size"],
            "sdo": ["x", "y", "size", "bandwidth"],
            "apod": ["x", "y", "size", "fit"],
            "sentinel": [
                "x", "y", "width", "height", "scale", "latitude", "longitude"
            ],
        }

        if planet != "sentinel":
            self.size_input.setValue(int(view_config["width"] / 3))

        self._initialize_combo_data()
        self._set_combo_value(self.satellite_selector, self.planet)
        self._apply_language()

        self.dialog_buttons.clicked.connect(self.handle_dialog_btn_click)
        self.satellite_selector.currentIndexChanged.connect(self.filter_dialog)

        self.filter_dialog()
        self.parse_values_in_dialog()
        self.exec_()

    @staticmethod
    def _combo_value(combo):
        value = combo.currentData()
        return value if value is not None else combo.currentText()

    @staticmethod
    def _set_combo_value(combo, value):
        index = combo.findData(value)
        if index < 0:
            index = combo.findText(value)
        if index >= 0:
            combo.setCurrentIndex(index)

    def _initialize_combo_data(self):
        for combo in (
            self.satellite_selector,
            self.color_input,
            self.bandwidth_input,
            self.fit_input,
        ):
            for index in range(combo.count()):
                combo.setItemData(index, combo.itemText(index))

    def _apply_language(self):
        text = PLANET_TEXT[self.language]
        self.setWindowTitle(text["title"])
        self.satellite_label.setText(text["satellite"])
        self.x_label.setText(text["x"])
        self.y_label.setText(text["y"])
        self.width_label.setText(text["width"])
        self.height_label.setText(text["height"])
        self.size_label.setText(text["size"])
        self.scale_label.setText(text["scale"])
        self.latitude_label.setText(text["latitude"])
        self.longitude_label.setText(text["longitude"])
        self.color_label.setText(text["color"])
        self.bandwidth_label.setText(text["bandwidth"])
        self.fit_label.setText(text["fit"])
        self.dialog_buttons.button(QDialogButtonBox.Apply).setText(text["apply"])
        self.dialog_buttons.button(QDialogButtonBox.Cancel).setText(text["cancel"])

        satellite_names = SATELLITE_NAMES[self.language]
        for index in range(self.satellite_selector.count()):
            value = self.satellite_selector.itemData(index)
            self.satellite_selector.setItemText(index, satellite_names.get(value, value))

        option_names = OPTION_NAMES[self.language]
        for combo in (self.color_input, self.fit_input):
            for index in range(combo.count()):
                value = combo.itemData(index)
                combo.setItemText(index, option_names.get(value, value))

    def current_satellite(self):
        return self._combo_value(self.satellite_selector)

    def planet_group(self):
        satellite = self.current_satellite()
        if satellite in ["goes-19", "goes-18", "himawari", "gk2a"]:
            return "geostationary"
        return satellite

    def handle_dialog_btn_click(self, button):
        role = self.dialog_buttons.buttonRole(button)
        if role == QDialogButtonBox.ApplyRole:
            self.get_values()
            self.close()
        elif role == QDialogButtonBox.RejectRole:
            self.settings = None
            self.close()

    def get_values(self):
        all_values = {}
        for widget in self.children():
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                all_values[widget.objectName().split("_")[0]] = widget.value()
            elif isinstance(widget, QComboBox) and widget is not self.satellite_selector:
                all_values[widget.objectName().split("_")[0]] = self._combo_value(widget)

        group = self.planet_group()
        self.planet = self.current_satellite()
        self.settings = {parameter: all_values[parameter] for parameter in self.filter[group]}

    def filter_dialog(self):
        parameter_list = []
        for parameter in self.filter[self.planet_group()]:
            parameter_list.extend((parameter + "_label", parameter + "_input"))

        for widget in self.children():
            if isinstance(widget, (QSpinBox, QComboBox, QLabel, QDoubleSpinBox)):
                widget.setVisible(widget.objectName() in parameter_list)

        self.satellite_label.setVisible(True)
        self.satellite_selector.setVisible(True)
        self.adjustSize()

    def parse_values_in_dialog(self):
        self.planet = self.current_satellite()
        for widget in self.children():
            name = widget.objectName().split("_")[0]
            if name not in self.settings:
                continue
            value = self.settings[name]
            if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.setValue(value)
            elif isinstance(widget, QComboBox) and widget is not self.satellite_selector:
                self._set_combo_value(widget, value)
