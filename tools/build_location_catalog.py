"""Build the compact offline location catalog bundled with EwaGEO."""

import argparse
import json
from pathlib import Path


CONTINENT_IDS = {
    "Africa": "africa",
    "Asia": "asia",
    "Europe": "europe",
    "Oceania": "oceania",
    "Polar": "antarctica",
}


def continent_id(country):
    region = country.get("region") or ""
    if region == "Americas":
        return (
            "south_america"
            if country.get("subregion") == "South America"
            else "north_america"
        )
    return CONTINENT_IDS.get(region, "other")


def translated_name(record):
    translations = record.get("translations") or {}
    return translations.get("zh-CN") or record.get("native") or record["name"]


def coordinate(record, name):
    value = record.get(name)
    if value in (None, ""):
        return None
    return round(float(value), 6)


def build_catalog(countries, states):
    states_by_country = {}
    for state in states:
        latitude = coordinate(state, "latitude")
        longitude = coordinate(state, "longitude")
        if latitude is None or longitude is None:
            continue
        states_by_country.setdefault(state["country_code"], []).append(
            {
                "id": str(state["id"]),
                "code": state.get("state_code") or "",
                "name": state["name"],
                "zh": translated_name(state),
                "latitude": latitude,
                "longitude": longitude,
            }
        )

    compact_countries = []
    for country in countries:
        latitude = coordinate(country, "latitude")
        longitude = coordinate(country, "longitude")
        if latitude is None or longitude is None:
            continue
        subdivisions = states_by_country.get(country["iso2"], [])
        subdivisions.sort(key=lambda item: item["name"].casefold())
        compact_countries.append(
            {
                "code": country["iso2"],
                "continent": continent_id(country),
                "name": country["name"],
                "zh": translated_name(country),
                "latitude": latitude,
                "longitude": longitude,
                "subdivisions": subdivisions,
            }
        )
    compact_countries.sort(key=lambda item: item["name"].casefold())
    return {
        "source": "Countries States Cities Database (ODbL-1.0)",
        "source_url": "https://github.com/dr5hn/countries-states-cities-database",
        "countries": compact_countries,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("countries")
    parser.add_argument("states")
    parser.add_argument("output")
    args = parser.parse_args()

    countries = json.loads(Path(args.countries).read_text(encoding="utf-8"))
    states = json.loads(Path(args.states).read_text(encoding="utf-8"))
    catalog = build_catalog(countries, states)
    Path(args.output).write_text(
        json.dumps(catalog, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
