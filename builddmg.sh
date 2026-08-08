#!/bin/sh
set -eu

rm -rf dist/dmg
mkdir -p dist/dmg
cp -R dist/EwaGEO.app dist/dmg/
rm -f dist/EwaGEO.dmg

create-dmg \
  --volname "EwaGEO" \
  --volicon "icon.ico" \
  --window-pos 200 120 \
  --window-size 600 300 \
  --icon-size 100 \
  --hide-extension "EwaGEO.app" \
  --app-drop-link 425 120 \
  dist/EwaGEO.dmg \
  dist/dmg/
