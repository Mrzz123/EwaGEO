import platform
import subprocess
from PIL import Image
import os


def check_for_program(program):
    try:
        subprocess.check_output(["which", "--", program])
        return True
    except:
        return False


def set_background(file_name):
    system = platform.system()

    if system == "Windows":
        import ctypes
        from ctypes import wintypes

        source_path = os.path.abspath(file_name)
        bmp_path = os.path.splitext(source_path)[0] + ".bmp"
        try:
            with Image.open(source_path) as source:
                wallpaper = source.convert("RGB")
                wallpaper.save(bmp_path, "BMP")
        except OSError as exc:
            raise RuntimeError(f"Could not prepare wallpaper image: {source_path}") from exc

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        user32.SystemParametersInfoW.argtypes = [
            wintypes.UINT,
            wintypes.UINT,
            wintypes.LPWSTR,
            wintypes.UINT,
        ]
        user32.SystemParametersInfoW.restype = wintypes.BOOL
        changed = user32.SystemParametersInfoW(
            20,  # SPI_SETDESKWALLPAPER
            0,
            bmp_path,
            0x01 | 0x02,  # persist setting and broadcast WM_SETTINGCHANGE
        )
        if not changed:
            raise ctypes.WinError(ctypes.get_last_error())
        return bmp_path
    elif system == "Darwin":
        # subprocess.call(
        #     [
        #         "osascript",
        #         "-e",
        #         'tell application "System Events"\n',
        #         "-e",
        #         "set theDesktops to a reference to every desktop\n",
        #         "-e",
        #         "repeat with aDesktop in theDesktops\n",
        #         "-e",
        #         'set the picture of aDesktop to "' + file_name + '"\n',
        #         "-e",
        #         'end repeat\n',
        #         "-e",
        #         'end tell',
        #     ]
        # )
        subprocess.call(
            [
                'osascript',
                '-e',
                'tell application "System Events"\n',
                '-e',
                '\tset desktopCount to count of desktops\n',
                '-e',
                '\trepeat with desktopNumber from 1 to desktopCount\n',
                '-e',
                '\t\ttell desktop desktopNumber\n',
                '-e',
                '\t\t\tset picture to "' + file_name + '"\n',
                '-e',
                '\t\tend tell\n',
                '-e',
                '\tend repeat\n',
                '-e',
                'end tell'
            ]
            , timeout=10)
        os.system('killall Dock')
    elif system == "Linux":
        try:
            if check_for_program("feh"):
                subprocess.call(["feh", "--bg-fill", file_name], timeout=10)
            if check_for_program("nitrogen"):
                subprocess.call(["nitrogen", file_name], timeout=10)
            subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri", file_name], timeout=50)
            subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", file_name],
                            timeout=50)
            subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "picture-options", "scaled"],
                            timeout=50)
            subprocess.call(["gsettings", "set", "org.gnome.desktop.background", "primary-color", "#000000"],
                            timeout=50)
        except:
            try:
                subprocess.call(["feh", "--bg-fill", file_name], timeout=10)
            except:
                try:
                    subprocess.call(["nitrogen", file_name], timeout=10)
                except:
                    pass

    elif check_for_program("feh"):
        subprocess.call(["feh", "--bg-fill", file_name], timeout=10)
    elif check_for_program("nitrogen"):
        subprocess.call(["nitrogen", file_name], timeout=10)

    # # set the Ubuntu lock screen
    # # os.system(f"sudo ./ubuntu-gdm-set-background --image {filename}")
