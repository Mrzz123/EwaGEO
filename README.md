# EwaGEO

**Earth Wallpapers from Geosynchronous Satellites**

EwaGEO is a Windows desktop application that builds near-real-time Earth wallpapers from geostationary satellite imagery. It provides satellite and colour-mode selection, resolution-aware layout presets, custom backgrounds, automatic day/night switching, scheduled updates, a system-tray mode, and Chinese/English interfaces.

> EwaGEO is an independent community project. It is not affiliated with or endorsed by any satellite operator or imagery provider.

## Supported imagery

- FY-4B — China Meteorological Administration / National Satellite Meteorological Center
- GK-2A — Korea Meteorological Administration / National Meteorological Satellite Center
- Himawari — Japan Meteorological Agency
- GOES-18 and GOES-19 — NOAA imagery distributed through CIRA SLIDER

Imagery is downloaded from provider or research-institution endpoints when the wallpaper is updated. Availability, delay, resolution and usage conditions are controlled by those providers. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistributing the application or bundled preview images.

The bundled default background is a cropped widescreen adaptation of **The Hockey Stick Galaxy** (`GSFC_20171208_Archive_e000012`). Credit: **ESA/Hubble & NASA**. The source image is released by ESA/Hubble under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). See [ASSET_SOURCES.md](ASSET_SOURCES.md) for the exact source and preview-image mapping.

## Install on Windows

Download `EwaGEO-Setup.exe` from the [Releases page](https://github.com/Mrzz123/EwaGEO/releases). The installer includes the Python runtime and required libraries, so end users do not need to install Python.

The first update requires internet access. If a provider is temporarily unavailable, EwaGEO keeps the last successfully generated wallpaper; FY-4B can also reuse its most recently cached frame.

## Run from source

Python 3.10 or newer is recommended.

```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe app.py
```

Run the tests with:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Build the Windows release

```powershell
venv\Scripts\pyinstaller.exe --clean --noconfirm app.spec
& 'D:\Inno Setup 6\ISCC.exe' winCompiler.iss
```

The standalone application is written to `dist\EwaGEO`, and the installer to `Output\EwaGEO-Setup.exe`. Build outputs and local virtual environments are intentionally excluded by `.gitignore`; publish the installer as a GitHub Release asset rather than committing it to the source tree.

## Configuration and local data

Runtime configuration, cached imagery and the last generated wallpaper are stored under `%LOCALAPPDATA%\EwaGEO`. Existing `%LOCALAPPDATA%\Liewa` data is copied on first use so installations made before the rename keep their settings.

## Origin and licence

EwaGEO is a modified version of [Live-Earth-Wallpapers](https://github.com/lennart-rth/Live-Earth-Wallpapers), created by lennart-rth and contributors. The upstream project and this derivative are licensed under the **GNU General Public License v3.0**. The complete licence is in [LICENSE](LICENSE).

Source code for the distributed EwaGEO builds is published at [github.com/Mrzz123/EwaGEO](https://github.com/Mrzz123/EwaGEO). Changes made for EwaGEO are described in [NOTICE.md](NOTICE.md), and third-party components/data are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md).

Copyright notices from the upstream project and third parties must not be removed. There is no warranty; see sections 15–17 of the GPL for the full terms.

## Issues and contributions

- Bug reports and feature requests: [GitHub Issues](https://github.com/Mrzz123/EwaGEO/issues)
- Source repository: [Mrzz123/EwaGEO](https://github.com/Mrzz123/EwaGEO)

Contributions are accepted under GPL-3.0-only unless explicitly stated otherwise.
