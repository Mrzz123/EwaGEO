import os
import time
from io import BytesIO
import datetime
import shutil
from pathlib import Path

import requests
from PIL import Image


# downloads a image from a url and return a pil Image
def download(url):
    last_error = None
    for attempt in range(1, 4):
        try:
            with requests.get(url, timeout=30) as response:
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
                image.load()
                return image
        except Exception as e:
            last_error = e
            print(f"{attempt}/3 Could not download image '{url}': {e}")
            time.sleep(1)
    raise RuntimeError(f"Unable to download image after 3 attempts: {url}") from last_error


def get_project_path():
    return os.path.dirname(os.path.realpath(__file__))


def get_user_data_path():
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
        path = base / "EwaGEO"
        legacy_path = base / "Liewa"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        path = base / "ewageo"
        legacy_path = base / "liewa"
    if not path.exists() and legacy_path.is_dir():
        try:
            shutil.copytree(legacy_path, path)
        except OSError:
            # An older installation must remain usable even when migration is
            # blocked by permissions or another process starting concurrently.
            path = legacy_path
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def get_gui_config_path():
    user_config = Path(get_user_data_path()) / "gui_config.yml"
    if user_config.exists():
        return str(user_config)
    return os.path.join(get_project_path(), "recources", "gui_config.yml")


def save_image(img, filename, file):
    if file is None:
        img.save(os.path.join(filename))
    else:
        img.save(os.path.join(filename, file))


def get_current_time():
    return datetime.datetime.today().strftime('%Y-%m-%d_%H-%M')
