#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ANDROID_DIR="$APP_DIR/android"
SDK_DIR="${ANDROID_SDK_ROOT:-${ANDROID_HOME:-$HOME/Library/Android/sdk}}"
ARCHES="${WHOOPSTAG_ANDROID_ARCHS:-arm64-v8a}"
OUTPUT="${WHOOPSTAG_APK_OUTPUT:-$HOME/Desktop/whoops-tag-owner.apk}"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  }
}

require_command node
require_command npm
require_command java

[[ -d "$SDK_DIR" ]] || {
  printf 'Android SDK not found: %s\n' "$SDK_DIR" >&2
  exit 1
}

cd "$APP_DIR"
printf 'Installing locked JavaScript dependencies…\n'
npm ci --no-audit --no-fund

printf 'Regenerating Android project without calling modules…\n'
npx expo prebuild --platform android --clean --no-install

cd "$ANDROID_DIR"
printf 'Building release APK for %s…\n' "$ARCHES"
bash ./gradlew clean assembleRelease "-PreactNativeArchitectures=$ARCHES"

APK="$ANDROID_DIR/app/build/outputs/apk/release/app-release.apk"
[[ -f "$APK" ]] || {
  printf 'APK was not produced: %s\n' "$APK" >&2
  exit 1
}

APKSIGNER=""
for candidate in "$SDK_DIR"/build-tools/*/apksigner; do
  [[ -x "$candidate" ]] && APKSIGNER="$candidate"
done

if [[ -n "${WHOOPSTAG_ANDROID_KEYSTORE:-}" && -n "${WHOOPSTAG_ANDROID_KEYSTORE_PASSWORD:-}" && -n "${WHOOPSTAG_ANDROID_KEY_ALIAS:-}" && -n "${WHOOPSTAG_ANDROID_KEY_PASSWORD:-}" ]]; then
  [[ -n "$APKSIGNER" ]] || {
    printf 'apksigner not found under %s\n' "$SDK_DIR/build-tools" >&2
    exit 1
  }
  printf 'Signing release APK…\n'
  SIGNED_APK="$APK.signed"
  "$APKSIGNER" sign \
    --ks "$WHOOPSTAG_ANDROID_KEYSTORE" \
    --ks-key-alias "$WHOOPSTAG_ANDROID_KEY_ALIAS" \
    --ks-pass env:WHOOPSTAG_ANDROID_KEYSTORE_PASSWORD \
    --key-pass env:WHOOPSTAG_ANDROID_KEY_PASSWORD \
    --out "$SIGNED_APK" \
    "$APK"
  mv "$SIGNED_APK" "$APK"
  "$APKSIGNER" verify "$APK"
else
  printf 'No release keystore variables supplied; keeping the generated debug-signed release APK.\n'
fi

mkdir -p "$(dirname "$OUTPUT")"
cp "$APK" "$OUTPUT"

if [[ "${WHOOPSTAG_INSTALL:-0}" == "1" ]]; then
  "$SDK_DIR/platform-tools/adb" install -r "$OUTPUT"
fi

printf 'APK: %s\n' "$OUTPUT"
if stat -f '%z bytes' "$OUTPUT" >/dev/null 2>&1; then
  printf 'Size: %s\n' "$(stat -f '%z bytes' "$OUTPUT")"
else
  printf 'Size: %s\n' "$(stat -c '%s bytes' "$OUTPUT")"
fi
