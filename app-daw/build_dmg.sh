#!/usr/bin/env bash
set -euo pipefail

APP_NAME="Melodic Microchop"
APP_BUNDLE="dist/${APP_NAME}.app"
DMG_NAME="Melodic-Microchop-macOS.dmg"
DMG_PATH="dist/${DMG_NAME}"
STAGING_ROOT="/private/tmp/melodic-microchop-dmg"
STAGING_DIR="${STAGING_ROOT}/${APP_NAME}"
VOLUME_NAME="${APP_NAME}"

if [[ ! -d "${APP_BUNDLE}" ]]; then
  echo "Missing ${APP_BUNDLE}. Build the app first with:"
  echo "PYINSTALLER_CONFIG_DIR=/private/tmp/microchop-pyinstaller-config ./microchop_venv/bin/pyinstaller --noconfirm --clean app-daw/microchop_desktop.spec"
  exit 1
fi

rm -rf "${STAGING_ROOT}"
mkdir -p "${STAGING_DIR}"
cp -R "${APP_BUNDLE}" "${STAGING_DIR}/"
ln -s /Applications "${STAGING_DIR}/Applications"

rm -f "${DMG_PATH}"
hdiutil create \
  -volname "${VOLUME_NAME}" \
  -srcfolder "${STAGING_DIR}" \
  -ov \
  -format UDZO \
  "${DMG_PATH}"

MOUNT_OUTPUT="$(hdiutil attach "${DMG_PATH}" -nobrowse)"
MOUNT_POINT="$(printf '%s\n' "${MOUNT_OUTPUT}" | awk '/\/Volumes\// {print substr($0, index($0, "/Volumes/")); exit}')"

if [[ -z "${MOUNT_POINT}" || ! -d "${MOUNT_POINT}/${APP_NAME}.app" || ! -L "${MOUNT_POINT}/Applications" ]]; then
  [[ -n "${MOUNT_POINT}" ]] && hdiutil detach "${MOUNT_POINT}" >/dev/null || true
  echo "DMG verification failed."
  exit 1
fi

hdiutil detach "${MOUNT_POINT}" >/dev/null
echo "Created and verified ${DMG_PATH}"
