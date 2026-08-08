import yaml
import datetime
import os
from pathlib import Path
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont, ImageOps
from liewa.liewa_cli.apod import load_apod
from liewa.liewa_cli.sentinel import load_sentinel
from liewa.liewa_cli.nasa_sdo import load_sdo
from liewa.liewa_cli.full_disks import load_geostationary
from liewa.liewa_cli.utils import get_user_data_path


CHINA_STANDARD_TIME = datetime.timezone(datetime.timedelta(hours=8))


def get_image_info_language():
    try:
        language = (
            Path(get_user_data_path()) / "ui_language.txt"
        ).read_text(encoding="utf-8").strip()
    except OSError:
        language = "zh_CN"
    return language if language in ("zh_CN", "en") else "zh_CN"


def load_overlay_font(size):
    windows_fonts = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    candidates = (
        windows_fonts / "msyh.ttc",
        windows_fonts / "msyhbd.ttc",
        windows_fonts / "simhei.ttf",
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/System/Library/Fonts/PingFang.ttc"),
    )
    for font_path in candidates:
        try:
            return ImageFont.truetype(str(font_path), size)
        except OSError:
            continue
    return ImageFont.load_default()


def format_capture_time(timestamp):
    try:
        captured = datetime.datetime.strptime(timestamp, "%Y%m%d%H%M%S")
    except (TypeError, ValueError):
        return None
    captured = captured.replace(tzinfo=datetime.timezone.utc)
    return captured.astimezone(CHINA_STANDARD_TIME)


def add_image_info_overlay(image, metadata_entries, language=None):
    """Draw official source attribution and exact frame time at top-right."""
    if not metadata_entries:
        return image

    language = language or get_image_info_language()
    blocks = []
    for metadata in metadata_entries:
        source = metadata.get("source", metadata.get("satellite", "Unknown"))
        captured = format_capture_time(metadata.get("timestamp"))
        estimated = bool(metadata.get("timestamp_estimated", False))
        if language == "en":
            capture_text = (
                captured.strftime(
                    "%Y-%m-%d %H:%M (approx., China Standard Time)"
                    if estimated
                    else "%Y-%m-%d %H:%M (China Standard Time)"
                )
                if captured
                else "Not provided by source"
            )
            blocks.append(f"Image source: {source}\nCaptured: {capture_text}")
        else:
            capture_text = (
                captured.strftime(
                    "%Y-%m-%d %H:%M（约，北京时间）"
                    if estimated
                    else "%Y-%m-%d %H:%M（北京时间）"
                )
                if captured
                else "数据源未提供"
            )
            blocks.append(f"图像来源：{source}\n拍摄时间：{capture_text}")

    text = "\n\n".join(blocks)
    font_size = max(16, min(48, round(image.height * 0.018)))
    font = load_overlay_font(font_size)
    spacing = max(4, font_size // 3)
    padding = max(12, font_size // 2)
    margin = max(16, round(min(image.size) * 0.012))

    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    bounds = draw.multiline_textbbox((0, 0), text, font=font, spacing=spacing)
    text_width = bounds[2] - bounds[0]
    text_height = bounds[3] - bounds[1]
    right = image.width - margin
    left = max(margin, right - text_width - padding * 2)
    top = margin
    bottom = top + text_height + padding * 2
    draw.rounded_rectangle(
        (left, top, right, bottom),
        radius=max(8, padding // 2),
        fill=(0, 0, 0, 168),
    )
    draw.multiline_text(
        (left + padding, top + padding - bounds[1]),
        text,
        font=font,
        fill=(255, 255, 255, 240),
        spacing=spacing,
    )
    return Image.alpha_composite(image.convert("RGBA"), overlay).convert("RGB")


def load_yaml(filename):
    with open(filename, "r") as ymlfile:
        cfg = yaml.load(ymlfile, Loader=yaml.Loader)

    return cfg


def calc_load_region(satellite_size, canvas_size, satellite_center):
    # canvas origin relative to satellite image upper-left corner
    canvas_origin_x = -(satellite_center[0] - satellite_size[0] / 2)
    canvas_origin_y = -(satellite_center[1] - satellite_size[1] / 2)
    region_left = max(0, int(canvas_origin_x))
    region_top = max(0, int(canvas_origin_y))
    region_right = min(satellite_size[0], int(canvas_origin_x + canvas_size[0]))
    region_bottom = min(satellite_size[1], int(canvas_origin_y + canvas_size[1]))
    region_right = max(region_left, region_right)
    region_bottom = max(region_top, region_bottom)
    load_region = [region_top, region_left, region_bottom, region_right]
    print(f"load region: {load_region}")
    return load_region


def create_circular_mask(size):
    """Create an inset, feathered disk mask without the source image's black rim."""
    width, height = size
    short_side = min(width, height)
    # Full-disk satellite images contain a few pixels of black space at the limb.
    # Choke the mask slightly so those pixels cannot become a dark halo when the
    # image is composited over a user-selected background.
    inset = max(3, round(short_side * 0.006))
    feather = max(2, round(short_side * 0.002))
    opaque_edge = inset + feather
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse(
        (
            opaque_edge,
            opaque_edge,
            max(opaque_edge, width - opaque_edge - 1),
            max(opaque_edge, height - opaque_edge - 1),
        ),
        fill=255,
    )
    # The opaque disk starts inside the requested inset; the blur expands only
    # through that reserved band instead of reaching back into the black source rim.
    return mask.filter(ImageFilter.GaussianBlur(radius=feather / 2))


def parse_image(config_file_dir):
    config = load_yaml(config_file_dir)
    image_settings = config["settings"]

    bg_size = (image_settings["width"], image_settings["height"])
    background_path = image_settings.get("background-image")
    if background_path:
        background_path = Path(background_path).expanduser()
        if not background_path.is_absolute():
            background_path = Path(config_file_dir).resolve().parent / background_path
        try:
            with Image.open(background_path) as background:
                bg = ImageOps.fit(
                    background.convert("RGB"),
                    bg_size,
                    method=Image.Resampling.LANCZOS,
                )
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"Unable to load background image: {background_path}") from exc
    else:
        bg_color = image_settings["bg-color"]
        bg = Image.new("RGB", bg_size, ImageColor.getrgb(bg_color))

    metadata_entries = []
    for satellite, value in config["planets"].items():
        paste_mask = None
        if satellite == "sentinel":
            raw_img = load_sentinel(value)
            im_size = (value["width"], value["height"])
            resized_img = raw_img.resize(im_size)

        elif satellite == "sdo":
            raw_img = load_sdo(value)
            resized_img = raw_img.resize((value["size"], value["size"]))

        elif satellite == "apod":
            raw_img = load_apod()

            im_size = (value["width"], value["height"])
            if value['fit'] == "fill":
                resized_img = raw_img.resize(im_size)
            elif value['fit'] == "contain":
                resized_img = ImageOps.contain(raw_img, im_size)
            elif value['fit'] == "cover":
                resized_img = ImageOps.fit(raw_img, im_size)

        # load static image of planet into the bg
        elif satellite == "external_planet":
            # raw_img = load_external(value)
            pass

        # meteosat, goes or himawari
        else:
            load_region = calc_load_region((value["size"], value["size"]), bg_size, (value["x"], value["y"]))

            args = value
            raw_img = load_geostationary(satellite, region=load_region, **args)
            image_metadata = raw_img.info.get("liewa_metadata")
            if image_metadata:
                metadata_entries.append(image_metadata)

            scale_ratio = value["size"] / max(raw_img.size)
            new_width, new_height = (int(dim * scale_ratio) for dim in raw_img.size)
            resized_img = raw_img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS
            )   # keep aspect ratio of the raw image
            paste_mask = create_circular_mask(resized_img.size)

        pos = (int(value["x"] - (resized_img.width / 2)), int(value["y"] - (resized_img.height / 2)))
        bg.paste(resized_img, pos, paste_mask)

    if image_settings.get("show-image-info", False):
        bg = add_image_info_overlay(bg, metadata_entries)

    return bg

# im = parse_image("./recources")
# im.show()
