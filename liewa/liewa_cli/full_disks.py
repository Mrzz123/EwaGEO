import datetime
import json
import math
import sys
import urllib.request
import urllib.error
from email.utils import parsedate_to_datetime
from multiprocessing.pool import ThreadPool as Pool
import time
import warnings
from pathlib import Path

import requests
from PIL import Image

from liewa.liewa_cli.utils import download, get_user_data_path


DEFAULT_LOCATION_NAME = "Liaoning"
DEFAULT_LATITUDE = 41.237411
DEFAULT_LONGITUDE = 122.995547
FY4B_IMAGE_URLS = {
    "thumbnail": "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/THUMBNAIL/FY4B_AGRI_DISK_GCLR.jpg",
    "full": "https://img.nsmc.org.cn/CLOUDIMAGE/FY4B/AGRI/GCLR/FY4B_DISK_GCLR.JPG",
}

OFFICIAL_IMAGE_SOURCES = {
    "goes-19": "NOAA · GOES-19",
    "goes-18": "NOAA · GOES-18",
    "himawari": "JMA · Himawari",
    "gk2a": "KMA/NMSC · GK-2A",
    "fy4b": "CMA/NSMC · FY-4B",
    "meteosat-9": "EUMETSAT · Meteosat-9",
    "meteosat-0deg": "EUMETSAT · Meteosat 0°",
}

sizes = {
    "goes-19": 678,
    # "goes-17": 678,
    "goes-18": 678,
    "himawari": 688,
    "gk2a": 688,
    "meteosat-9": 464,
    "meteosat-0deg": 464,
    # "meteosat-11": 464,
}

satellite_aliases = {
    # GOES-19 replaced GOES-16 as the operational GOES-East satellite.
    # Keep old saved GUI configurations working without manual edits.
    "goes-16": "goes-19",
}


def normalize_satellite(satellite):
    return satellite_aliases.get(satellite, satellite)


def _solar_event_utc(date, latitude, longitude, sunrise):
    """Calculate one solar event using NOAA's sunrise/sunset approximation."""
    day_of_year = date.timetuple().tm_yday
    longitude_hour = longitude / 15.0
    approximate_time = day_of_year + (
        ((6 if sunrise else 18) - longitude_hour) / 24.0
    )
    mean_anomaly = (0.9856 * approximate_time) - 3.289
    true_longitude = (
        mean_anomaly
        + 1.916 * math.sin(math.radians(mean_anomaly))
        + 0.020 * math.sin(math.radians(2 * mean_anomaly))
        + 282.634
    ) % 360

    right_ascension = math.degrees(
        math.atan(0.91764 * math.tan(math.radians(true_longitude)))
    ) % 360
    right_ascension += (
        math.floor(true_longitude / 90) * 90
        - math.floor(right_ascension / 90) * 90
    )
    right_ascension /= 15

    sin_declination = 0.39782 * math.sin(math.radians(true_longitude))
    cos_declination = math.cos(math.asin(sin_declination))
    latitude_radians = math.radians(latitude)
    cos_hour = (
        math.cos(math.radians(90.833))
        - sin_declination * math.sin(latitude_radians)
    ) / (cos_declination * math.cos(latitude_radians))
    if cos_hour > 1:
        return None, "polar_night"
    if cos_hour < -1:
        return None, "polar_day"

    hour_angle = math.degrees(math.acos(cos_hour))
    if sunrise:
        hour_angle = 360 - hour_angle
    hour_angle /= 15
    local_mean_time = (
        hour_angle + right_ascension - 0.06571 * approximate_time - 6.622
    )
    utc_hours = local_mean_time - longitude_hour
    midnight = datetime.datetime.combine(
        date, datetime.time.min, tzinfo=datetime.timezone.utc
    )
    return midnight + datetime.timedelta(hours=utc_hours), "normal"


def get_sun_times(date, latitude=DEFAULT_LATITUDE, longitude=DEFAULT_LONGITUDE):
    """Return UTC sunrise, sunset and polar status for a representative point."""
    latitude = float(latitude)
    longitude = float(longitude)
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Invalid latitude or longitude")
    # Avoid the exact poles, where the hour-angle equation divides by zero.
    latitude = max(-89.9999, min(89.9999, latitude))
    sunrise, sunrise_status = _solar_event_utc(
        date, latitude, longitude, True
    )
    sunset, sunset_status = _solar_event_utc(
        date, latitude, longitude, False
    )
    status = (
        sunrise_status
        if sunrise_status != "normal"
        else sunset_status
    )
    if sunrise is not None and sunset is not None and sunset <= sunrise:
        sunset += datetime.timedelta(days=1)
    return sunrise, sunset, status


def resolve_color_mode(
    name,
    now=None,
    latitude=DEFAULT_LATITUDE,
    longitude=DEFAULT_LONGITUDE,
    location_name=DEFAULT_LOCATION_NAME,
):
    if name != "adaptive":
        return name

    now = now or datetime.datetime.now(datetime.timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=datetime.timezone.utc)
    else:
        now = now.astimezone(datetime.timezone.utc)
    try:
        latitude = float(latitude)
        longitude = float(longitude)
        if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
            raise ValueError
    except (TypeError, ValueError):
        latitude = DEFAULT_LATITUDE
        longitude = DEFAULT_LONGITUDE
        location_name = DEFAULT_LOCATION_NAME

    _, _, current_status = get_sun_times(now.date(), latitude, longitude)
    if current_status == "polar_day":
        selected = "natural_color"
        detail = "polar day"
    elif current_status == "polar_night":
        selected = "geocolor"
        detail = "polar night"
    else:
        selected = "geocolor"
        detail = "outside daylight window"
        for offset in range(-2, 3):
            solar_date = now.date() + datetime.timedelta(days=offset)
            sunrise, sunset, status = get_sun_times(
                solar_date, latitude, longitude
            )
            if status != "normal":
                continue
            natural_start = sunrise - datetime.timedelta(minutes=20)
            natural_end = sunset + datetime.timedelta(minutes=20)
            if natural_start <= now < natural_end:
                selected = "natural_color"
                detail = (
                    f"sunrise {sunrise:%Y-%m-%d %H:%M} UTC, "
                    f"sunset {sunset:%Y-%m-%d %H:%M} UTC"
                )
                break
    print(
        f"Automatic color for {location_name or 'selected location'} "
        f"({latitude:.4f}, {longitude:.4f}): {selected} ({detail})"
    )
    return selected


def _estimate_fy4b_capture_time(last_modified):
    """Estimate the AGRI scan start from NSMC's image publication time.

    The public latest-image endpoint does not expose the embedded scan timestamp
    as machine-readable metadata. Its GeoColor image is normally published about
    25-26 minutes after the 15-minute scan start, so round that offset back to the
    nearest official 15-minute observation slot and mark it as estimated.
    """
    if not last_modified:
        return None
    try:
        published = parsedate_to_datetime(last_modified)
        if published.tzinfo is None:
            published = published.replace(tzinfo=datetime.timezone.utc)
        candidate = published.astimezone(datetime.timezone.utc) - datetime.timedelta(
            minutes=26
        )
        rounded_seconds = int((candidate.timestamp() + 450) // 900 * 900)
        return datetime.datetime.fromtimestamp(
            rounded_seconds, tz=datetime.timezone.utc
        ).strftime("%Y%m%d%H%M%S")
    except (TypeError, ValueError, OverflowError):
        return None


def _load_fy4b_cached_image(quality, target_size):
    """Download NSMC's latest FY-4B image with conditional and offline caching."""
    url = FY4B_IMAGE_URLS[quality]
    cache_dir = Path(get_user_data_path()) / "satellite-cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    image_path = cache_dir / f"fy4b_gclr_{quality}.jpg"
    metadata_path = cache_dir / f"fy4b_gclr_{quality}.json"
    metadata = {}
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        pass

    headers = {"User-Agent": "EwaGEO/1.0 (+https://github.com/Mrzz123/EwaGEO)"}
    if image_path.exists():
        if metadata.get("etag"):
            headers["If-None-Match"] = metadata["etag"]
        if metadata.get("last_modified"):
            headers["If-Modified-Since"] = metadata["last_modified"]

    try:
        with requests.get(url, headers=headers, timeout=(10, 75)) as response:
            if response.status_code == 304 and image_path.exists():
                print(f"FY-4B {quality} image is unchanged; using cached frame.")
            else:
                response.raise_for_status()
                temporary_path = image_path.with_suffix(".tmp")
                temporary_path.write_bytes(response.content)
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore", Image.DecompressionBombWarning)
                        with Image.open(temporary_path) as downloaded:
                            downloaded.verify()
                    temporary_path.replace(image_path)
                except Exception:
                    temporary_path.unlink(missing_ok=True)
                    raise

                last_modified = response.headers.get("Last-Modified")
                metadata = {
                    "url": url,
                    "etag": response.headers.get("ETag"),
                    "last_modified": last_modified,
                    "timestamp": _estimate_fy4b_capture_time(last_modified),
                }
                metadata_path.write_text(
                    json.dumps(metadata, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
    except (OSError, requests.RequestException, ValueError) as exc:
        if not image_path.exists():
            raise RuntimeError(
                f"Unable to download FY-4B imagery and no cached frame is available: {url}"
            ) from exc
        print(f"Unable to refresh FY-4B imagery; using cached frame: {exc}")

    try:
        with warnings.catch_warnings():
            # This is a trusted, fixed NSMC endpoint whose current image is about
            # 131 megapixels, slightly above Pillow's generic warning threshold.
            warnings.simplefilter("ignore", Image.DecompressionBombWarning)
            with Image.open(image_path) as cached:
                # Let the JPEG decoder choose an efficient native downsampling
                # ratio before allocating the requested output pixels.
                cached.draft("RGB", (target_size, target_size))
                image = cached.convert("RGB")
    except OSError as exc:
        raise RuntimeError(f"Unable to open cached FY-4B image: {image_path}") from exc
    return image, metadata


def load_fy4b(**kwargs):
    """Load and clean NSMC's latest FY-4B AGRI full-disk GeoColor image."""
    target_size = int(kwargs.get("size", 1024))
    quality = "full"
    image, source_metadata = _load_fy4b_cached_image(quality, target_size)

    # NSMC's fixed image contains a square full disk followed by a logo strip.
    # Cropping to the square removes the strip; the circular compositor removes
    # the timestamp text in the black top-left corner without touching Earth.
    disk_side = min(image.width, image.height)
    image = image.crop((0, 0, disk_side, disk_side))
    if image.width > target_size:
        image = image.resize(
            (target_size, target_size), Image.Resampling.LANCZOS
        )
    image.info["liewa_metadata"] = {
        "satellite": "fy4b",
        "source": OFFICIAL_IMAGE_SOURCES["fy4b"],
        "timestamp": source_metadata.get("timestamp"),
        "color": "geocolor",
    }
    return image


def get_time_code(satellite, name):
    satellite = normalize_satellite(satellite)
    url = f"https://slider.cira.colostate.edu/data/json/{satellite}/full_disk/{name}/latest_times.json"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "EwaGEO/1.0 (+https://github.com/Mrzz123/EwaGEO)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.load(response)
        latest = data["timestamps_int"][0]
    except (urllib.error.URLError, KeyError, IndexError, ValueError) as exc:
        raise RuntimeError(
            f"No current {name} imagery is available for {satellite}. "
            f"Data source: {url}"
        ) from exc
    date = datetime.datetime.strptime(str(latest), "%Y%m%d%H%M%S").strftime("%Y/%m/%d")

    return latest, date


def calc_tile_coordinates(scale):
    # Zoom level 0-3 or 0-4 (depending on the satellite)
    tiles_n = 2 ** scale
    row = range(0, tiles_n)
    col = range(0, tiles_n)
    return list(row), list(col)


def calc_scale(satellite, **kwargs):
    satellite = normalize_satellite(satellite)
    size = sizes[satellite]
    minimum_side = kwargs.get("size", 1024)
    scale = int(minimum_side / size / 1.2)  # up scale < 120%

    scale = max(min(scale.bit_length(), 4), 0)   # log_2 scale between 0-4
    if satellite.lower().startswith("meteosat") and scale == 4:
        scale = 3  # Meteosat 9 and 0deg only support up to 8x zoom

    return scale


def build_url(satellite, scale, include_metadata=False, **kwargs):
    satellite = normalize_satellite(satellite)
    if scale > 4:
        sys.exit("Does not support Zoom Levels greater than 4.")

    location = kwargs.get("location") or {}
    name = resolve_color_mode(
        kwargs.get("color", "natural_color"),
        latitude=location.get("latitude", DEFAULT_LATITUDE),
        longitude=location.get("longitude", DEFAULT_LONGITUDE),
        location_name=location.get("name", DEFAULT_LOCATION_NAME),
    )

    supported_args = ["geocolor", "natural_color"]
    if name not in supported_args:
        raise ValueError(
            "Wrong parameter for colorMode: Meteorsat and Goes only support 'natural_color' or 'geocolor' as colorMode!"
        )

    time_code, date = get_time_code(satellite, name)
    base_url = f"https://slider.cira.colostate.edu/data/imagery/{date}/{satellite}---full_disk/{name}/{time_code}/0{scale}"
    if include_metadata:
        return base_url, {
            "satellite": satellite,
            "source": OFFICIAL_IMAGE_SOURCES.get(satellite, satellite),
            "timestamp": str(time_code),
            "color": name,
        }
    return base_url


def load_geostationary(satellite, region=None, **kwargs):
    # load region_ can be [top, left, bottom, right] in pixels
    # or a list [[row1,col1], [row2,col2]] in indexes
    satellite = normalize_satellite(satellite)
    if satellite == "fy4b":
        return load_fy4b(**kwargs)

    scale = calc_scale(satellite, **kwargs)
    base_url, image_metadata = build_url(
        satellite, scale, include_metadata=True, **kwargs
    )
    row, col = calc_tile_coordinates(scale)

    tilesize = sizes[satellite]
    fullsize = tilesize * (2 ** scale)
    tgt_size = kwargs.get("size", 1024)

    if region is None:
        region = [0, 0, fullsize, fullsize]

    if len(region) == 4 and all(isinstance(item, (int, float)) for item in region):
        # Scale the load region_ to the full size of the image
        load_region = [item * fullsize / tgt_size for item in region]

        top, left, bottom, right = [item / tilesize for item in load_region]
        print(top, left, bottom, right)
        row_col_pairs = [[r, c]
                         for r in row if top-1 < r < bottom
                         for c in col if left-1 < c < right
                         ]

    elif all(len(i) == 2 and isinstance(i, list) and all(isinstance(j, int) for j in i) for i in region):
        row_col_pairs = region
    else:
        raise ValueError("Invalid region parameter.")

    img_map = {}
    print(f"Downloading {len(row_col_pairs)} images...")

    def download_func(row_col):
        r = row_col[0]
        c = row_col[1]
        url = base_url + f"/{str(r).zfill(3)}_{str(c).zfill(3)}.png"
        print(f"Downloading Image ({r},{c}).{url}")
        img = download(url)
        # store the images in a dict so we don't have to care about the order they're downloaded in
        img_map[str(r) + ":" + str(c)] = img
        return img

    start = time.time()

    with Pool(len(row_col_pairs)) as pool:
        pool.map(download_func, row_col_pairs)

    print("Stiching images...")
    # stich the images together based on the position in the grid.
    bg = Image.new("RGB", (tilesize * (max(col) + 1), tilesize * (max(row) + 1)))
    for r, c in row_col_pairs:
        img = img_map[str(r) + ":" + str(c)]
        bg.paste(img, (img.width * c, img.height * r))

    end = time.time()
    print("Downloads took: ", end - start)

    bg.info["liewa_metadata"] = image_metadata

    return bg
