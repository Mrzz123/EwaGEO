# Bundled asset sources and reuse status

This inventory covers raster images committed to the EwaGEO source repository. It records provenance; it does not itself grant rights that the original provider has not granted.

## Application icon

| Bundled files | Source | Credit and terms |
| --- | --- | --- |
| `icon.ico`, `liewa/liewa_gui/icon.png` | EwaGEO project artwork supplied by Mrzz123 | Used as the Windows executable, installer, window and system-tray icon. Mrzz123 is responsible for confirming the artwork's reuse and redistribution rights. |

## Default background

| Bundled file | Source | Credit and terms |
| --- | --- | --- |
| `liewa/liewa_cli/recources/cb6be5663982cdd0b307a7d17d3be5f9.jpg` | [The Hockey Stick Galaxy](https://esahubble.org/images/potw1731a/), also catalogued by NASA as [`GSFC_20171208_Archive_e000012`](https://images.nasa.gov/details/GSFC_20171208_Archive_e000012) | **ESA/Hubble & NASA**, [CC BY 4.0](https://esahubble.org/copyright/). Cropped to widescreen and resized/compressed for EwaGEO. |

## Layout previews

All PNG files below are EwaGEO wallpaper composites made with the default background above. Each therefore retains the **ESA/Hubble & NASA** background credit and also contains processed satellite imagery.

| File pattern | Satellite imagery obtained by EwaGEO from | Published terms found during the source audit |
| --- | --- | --- |
| `config/FY-4B*.png` | CMA/NSMC FY-4B public latest-image endpoint | NSMC provides public/shared data services, but no explicit redistribution licence for this image endpoint has been identified. Obtain written confirmation or remove these previews before public distribution. |
| `config/GOES-18*.png`, `config/GOES-19*.png` | CIRA SLIDER tiles derived from NOAA GOES data | NOAA-originated US Government data is generally public domain unless marked otherwise; the separate reuse status of CIRA's processed GeoColor/natural-colour tile product should still be confirmed. |
| `config/himawari*.png` | CIRA SLIDER tiles derived from JMA Himawari data | JMA MSC content may be copied, modified and commercially used with source citation and an editing statement; the terms are CC BY 4.0 compatible. Confirm any additional CIRA processing rights. |
| `config/gk2a*.png` | CIRA SLIDER tiles derived from KMA/NMSC GK-2A data | KMA/NMSC permits free reuse for works carrying the applicable KOGL mark; unmarked material requires prior coordination. Confirm the exact source product and any additional CIRA processing rights. |

Relevant official policies:

- NASA Images and Media Usage Guidelines: https://www.nasa.gov/nasa-brand-center/images-and-media/
- ESA/Hubble image copyright terms: https://esahubble.org/copyright/
- NOAA/PSL data and product disclaimer: https://www.psl.noaa.gov/disclaimer/
- JMA Meteorological Satellite Center legal notice: https://www.data.jma.go.jp/mscweb/en/general/note.html
- KMA/NMSC copyright protection policy: https://nmsc.kma.go.kr/homepage/html/base/cmm/selectPage.do?page=static.etc.copyrightProtectionPolicy
- CMA/NSMC data-service help and contact: https://satellite.nsmc.org.cn/DataPortal/cn/support/faq.html

## Upstream example images

Files under `examples/` came from the GPL-licensed upstream Live-Earth-Wallpapers repository. GPL licensing of the repository does not automatically settle rights in third-party imagery depicted in those screenshots. They are not used by the EwaGEO Windows application and should be reviewed or removed before the first public release.
