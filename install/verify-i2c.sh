#!/usr/bin/env bash
# SvxLink-OLED I2C preflight. Read-only by default.
set -euo pipefail
MODE="${1:---check}"
BUS="${OLED_I2C_BUS:-1}"
if ! [[ "$BUS" =~ ^[0-9]+$ ]]; then echo 'Invalid OLED_I2C_BUS' >&2; exit 2; fi
case "$MODE" in --check|--enable) ;; *) echo "Usage: $0 [--check|--enable]" >&2; exit 2;; esac
printf 'I2C preflight: bus=%s, target=0x3c\n' "$BUS"
if [[ -e "/dev/i2c-$BUS" ]]; then
  echo "I2C adapter present: /dev/i2c-$BUS"
  echo 'Address scanning is not performed automatically.'
  echo 'Use i2cdetect manually after verifying attached hardware.'
  echo 'PASS: kernel I2C adapter present (physical OLED detection still pending).'
  exit 0
fi
echo "I2C adapter /dev/i2c-$BUS is absent."
if [[ "$MODE" == --check ]]; then
  echo 'No configuration changed. On a standard Raspberry Pi, run --enable after confirming pin availability.'
  echo 'For ICS/NanoPi/other boards, use the existing board-specific preparation procedure.'
  exit 3
fi
if [[ ! -r /proc/device-tree/model ]] || ! grep -aq 'Raspberry Pi' /proc/device-tree/model; then
  echo 'Automatic enable refused: not positively identified as Raspberry Pi.' >&2; exit 4
fi
if ! command -v raspi-config >/dev/null; then
  echo 'raspi-config not present; follow device-specific installation instructions.' >&2; exit 4
fi
echo 'WARNING: This can alter Raspberry Pi boot I2C settings. Verify ICS overlays and pin sharing first.'
read -r -p 'Enable the default Raspberry Pi I2C interface using raspi-config? [y/N] ' confirm
[[ "$confirm" == [yY] ]] || { echo 'No change made.'; exit 0; }
sudo raspi-config nonint do_i2c 0
echo 'I2C enable requested. A reboot may be required for the interface to appear.'
read -r -p 'Reboot this machine now? [y/N] ' restart
if [[ "$restart" == [yY] ]]; then sudo reboot; else echo 'Reboot deferred. Repeat --check after reboot.'; fi
