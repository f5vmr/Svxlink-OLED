#!/usr/bin/env bash
# Run from repository root on target Linux SBC; does not start service.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Use sudo ./install/install-oled.sh' >&2; exit 1; }
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$SOURCE/oled/renderer.py" && -f "$SOURCE/oled/status_source.py" && -f "$SOURCE/oled/hardware.py" ]] || {
  echo 'Missing OLED application files. Install kit into the existing project first.' >&2; exit 1;
}
if ! id svxlink >/dev/null 2>&1; then echo 'svxlink service account missing; stopping.' >&2; exit 1; fi
BUS="${OLED_I2C_BUS:-1}"
if ! [[ "$BUS" =~ ^[0-9]+$ ]] || [[ ! -e "/dev/i2c-$BUS" ]]; then
  echo "I2C adapter /dev/i2c-$BUS missing. Run install/verify-i2c.sh first." >&2; exit 1
fi
# Verify that the I2C group exists.
if ! getent group i2c >/dev/null; then
  echo 'Creating i2c group...'
  groupadd --system i2c
fi

# Verify access permissions for the selected I2C device.
I2C_DEVICE="/dev/i2c-$BUS"

DEVICE_GROUP="$(stat -c '%G' "$I2C_DEVICE")"

if [[ "$DEVICE_GROUP" != "i2c" ]]; then
  echo "WARNING: $I2C_DEVICE belongs to group $DEVICE_GROUP, not i2c."
  echo 'The OLED service may not be able to access this device.'
  echo 'Check the device permissions and udev configuration before starting.'
fi
# Attempt to restore a previously running OLED service
# if installation fails after the service was stopped.
OLED_STOPPED_FOR_UPGRADE=false

restore_on_failure() {
  local result=$?

  trap - EXIT

  if [[ $result -ne 0 ]]; then
    echo "ERROR: SvxLink-OLED installation failed." >&2

    if [[ "$OLED_STOPPED_FOR_UPGRADE" == true ]]; then
      echo "Attempting to restore the OLED service..." >&2

      if ! systemctl start svxlink-oled.service; then
        echo "WARNING: OLED service could not be restored." >&2
        echo "Check: journalctl -u svxlink-oled -n 50" >&2
      fi
    fi
  fi

  exit "$result"
}

trap restore_on_failure EXIT
# Record whether an existing OLED service is running.
OLED_WAS_ACTIVE=false

if systemctl is-active --quiet svxlink-oled.service; then
  OLED_WAS_ACTIVE=true
  echo 'Stopping existing SvxLink-OLED service for upgrade...'
  systemctl stop svxlink-oled.service
  OLED_STOPPED_FOR_UPGRADE=true
fi
apt-get update
apt-get install -y python3 python3-venv python3-pip i2c-tools
install -d -m 0755 /opt/svxlink-oled /etc/svxlink-oled
install -d -m 0755 /opt/svxlink-oled/oled
for f in __init__.py renderer.py scroll.py status_source.py hardware.py; do
  install -m 0644 "$SOURCE/oled/$f" "/opt/svxlink-oled/oled/$f"
done
# Install configuration only on first installation.
# Never overwrite an existing operator configuration.

OLED_CONFIG="/etc/svxlink-oled/oled.ini"

if [[ ! -e "$OLED_CONFIG" ]]; then
  echo 'New SvxLink-OLED installation.'

  install -m 0644 \
    "$SOURCE/config/oled.ini" \
    "$OLED_CONFIG"

  echo 'Discovering local SvxLink-Dash API...'

  DETECTED_API=""

  for API_URL in \
    "http://127.0.0.1/api/status" \
    "http://127.0.0.1:5000/api/status"
  do
    if curl --noproxy '*' -fsS \
      --max-time 3 \
      --output /dev/null \
      "$API_URL" 2>/dev/null; then

      DETECTED_API="$API_URL"
      break
    fi
  done

  if [[ -n "$DETECTED_API" ]]; then
    sed -i \
      "s|^status_url *=.*|status_url = $DETECTED_API|" \
      "$OLED_CONFIG"

    echo "Local SvxLink-Dash API detected: $DETECTED_API"
  else
    echo 'WARNING: No local SvxLink-Dash API detected.'
    echo 'Check that SvxLink-Dash is running on port 80 or 5000.'
    echo "Review status_url in $OLED_CONFIG before starting OLED."
  fi

else
  echo "Existing OLED configuration retained: $OLED_CONFIG"
  echo 'Automatic API discovery skipped for existing installation.'
fi
python3 -m venv /opt/svxlink-oled/.venv
/opt/svxlink-oled/.venv/bin/python -m pip install --upgrade 'luma.oled>=3.15,<4' 'Pillow>=10,<14'
install -m 0644 "$SOURCE/install/svxlink-oled.service" /etc/systemd/system/svxlink-oled.service
systemctl daemon-reload
# Restore the previous service state after installation.
if [[ "$OLED_WAS_ACTIVE" == true ]]; then
  echo 'Restarting previously active SvxLink-OLED service...'
  systemctl start svxlink-oled.service
else
  echo 'SvxLink-OLED service remains stopped.'
fi
printf '\nInstalled but NOT started. Review OLED config, bus and device.\n'
printf 'Selected I2C bus: %s\n' "$BUS"
printf 'To scan manually, after checking attached hardware: sudo i2cdetect -y %s\n' "$BUS"
printf 'After connecting and verifying hardware: sudo systemctl enable --now svxlink-oled\n'
