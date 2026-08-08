# Third-party notices

This file records third-party software, data and network services used by EwaGEO. It is provided for attribution and does not replace the corresponding projects' complete licence texts. The versions actually included in a binary release are listed in `requirements.txt` and in the release's build materials.

## Upstream application

- **Live-Earth-Wallpapers**, lennart-rth and contributors — GNU General Public License v3.0 — https://github.com/lennart-rth/Live-Earth-Wallpapers

EwaGEO is a modified work. See `NOTICE.md` and `LICENSE`.

## Bundled Python and GUI components

- **Python** — Python Software Foundation License — https://docs.python.org/3/license.html
- **PyQt5** — GNU GPL v3 or commercial licence — https://www.riverbankcomputing.com/software/pyqt/
- **Qt** — licences offered by The Qt Company, including LGPL/GPL options for relevant modules — https://www.qt.io/licensing/
- **Pillow** — HPND License — https://github.com/python-pillow/Pillow
- **NumPy** — BSD 3-Clause License — https://github.com/numpy/numpy
- **OpenCV / opencv-python** — Apache License 2.0 and component notices — https://github.com/opencv/opencv-python
- **Requests** — Apache License 2.0 — https://github.com/psf/requests
- **Beautiful Soup** — MIT License — https://www.crummy.com/software/BeautifulSoup/
- **PyYAML** — MIT License — https://github.com/yaml/pyyaml
- **pywin32** — Python Software Foundation style licence — https://github.com/mhammond/pywin32
- **PyInstaller** — GNU GPL v2 with its bootloader exception — https://pyinstaller.org/en/stable/license.html

Transitive components may have additional notices. Binary distributors should retain the licence files shipped by the components and review the exact dependency set for each release.

## Location data

Location names and representative coordinates are derived from **Countries States Cities Database**:

- Source: https://github.com/dr5hn/countries-states-cities-database
- Licence: Open Database License (ODbL) v1.0
- Detailed bundled notice: `liewa/liewa_cli/recources/location-data-NOTICE.txt`

## Satellite imagery and online services

EwaGEO retrieves imagery at runtime from services operated by or associated with NOAA/CIRA, CMA/NSMC, KMA/NMSC and JMA. Satellite imagery, logos, timestamps, endpoint availability and provider metadata remain subject to each provider's own attribution and usage policies. EwaGEO is not affiliated with or endorsed by these organisations.

The layout-preview PNG files under `liewa/liewa_cli/recources/config` may contain reduced examples derived from satellite imagery and a bundled background. They are used only to preview the corresponding configuration. Before publishing a release, the distributor should confirm that every preview image and the default background may be redistributed, preserve required attribution, and replace any asset whose provenance or permission cannot be established.

Links to provider information:

- NOAA: https://www.noaa.gov/disclaimer
- CIRA SLIDER: https://slider.cira.colostate.edu/
- CMA/NSMC: https://www.nsmc.org.cn/
- KMA/NMSC: https://nmsc.kma.go.kr/
- JMA: https://www.jma.go.jp/jma/kishou/info/coment.html

See `ASSET_SOURCES.md` for the mapping between bundled preview files and their imagery sources. Source acknowledgement alone is not a substitute for permission when a provider has not granted reuse rights.

## Default background

The bundled file `liewa/liewa_cli/recources/cb6be5663982cdd0b307a7d17d3be5f9.jpg` is a cropped widescreen adaptation of:

- Title: **The Hockey Stick Galaxy**
- NASA asset ID: `GSFC_20171208_Archive_e000012`
- NASA library record: https://images.nasa.gov/details/GSFC_20171208_Archive_e000012
- ESA/Hubble image record: https://esahubble.org/images/potw1731a/
- Required credit: **ESA/Hubble & NASA**
- Licence: Creative Commons Attribution 4.0 International
- Licence terms: https://esahubble.org/copyright/
- Modification: cropped to a widescreen composition and resized/compressed for use as EwaGEO's default background

This is a jointly credited ESA/Hubble and NASA work, not a NASA-only public-domain claim. ESA/Hubble permits reproduction and modification, including commercial use, when the complete credit remains clear and visible, the work is not presented as endorsed by ESA/Hubble, and modifications are indicated.

## Application artwork

The application icon originated with the GPL-licensed upstream project unless replaced in a later EwaGEO release. It is redistributed as part of the GPL-covered work with the upstream attribution above.
