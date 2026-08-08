#!/bin/sh
set -eu

# Build a one-folder application and prepare a Linux package tree.
pyinstaller --clean --noconfirm app.spec

rm -rf package
mkdir -p package/opt/ewageo
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/scalable/apps

cp -R dist/EwaGEO/. package/opt/ewageo/
cp liewa/liewa_gui/icon.svg package/usr/share/icons/hicolor/scalable/apps/ewageo.svg
cp ewageo.desktop package/usr/share/applications/

find package/opt/ewageo -type f -exec chmod 644 {} +
find package/opt/ewageo -type d -exec chmod 755 {} +
find package/usr/share -type f -exec chmod 644 {} +
chmod 755 package/opt/ewageo/EwaGEO

# Example Debian package command:
# fpm -C package -s dir -t deb -n ewageo -v 1.0.0 -p EwaGEO.deb
