# SvxLink-OLED — installation and operating manual

**Foundation V0.1 — development/pre-release. No physical OLED has yet been tested.**

SvxLink-OLED is a standalone, read-only local status accessory to SvxLink-Dash V4.1. It uses the existing HTTP `/api/status` endpoint. It cannot select nodes, switch talkgroups, send DTMF, change reflectors, or control transmitters. SvxLink-Dash and SvxLink do not need modification.

## 1. What the screen shows

- Top line: local callsign aligned left; reflector name aligned right, truncated if necessary.
- Middle line: receiver RX active/idle and transmitter TX active/idle.
- Bottom line: talkgroup number/name or Standby; long text can scroll horizontally.
- If the local API is unreachable, display an unavailable/offline status rather than showing stale activity as live.

The supplied renderer has previously been tested in a macOS/Tkinter simulator using live MB5HT data. A physical I²C OLED has **not** been tested. The present renderer is primarily laid out for 128×64; 128×128 rendering requires visual refinement before release.

## 2. Hardware supported in principle

| Controller | Nominal resolution | Notes |
| --- | --- | --- |
| SSD1315 | 128×64 | Default; luma.oled 3.15+ needed |
| SSD1306 | 128×64 | Monochrome or fixed yellow/blue region module |
| SH1106 | 128×64 | Select correct controller |
| SH1107 | 128×128 | Physical layout not yet optimised |

Default I²C **7-bit** device address is `0x3C`. Printed `0x78` on a display PCB is generally the 8-bit *write* address byte, not the value to put in Linux software. Actual module controller/address and operating voltage must be confirmed from the manufacturer's information.

A typical four-pin module has VCC, GND, SDA and SCL. Verify the module's voltage requirements and physical pin order **before** wiring it. For Raspberry Pi, SDA1 is normally GPIO2 / physical pin 3 and SCL1 GPIO3 / physical pin 5; do not assume these are exposed or electrically free on an ICS-equipped board. No modifications to ICS overlays or GPIO expander settings are included in this installer.


## 3. Prerequisites and installation sequence

SvxLink-OLED is an optional accessory for an existing SvxLink installation. It requires SvxLink-Dash V4.1 to provide local node status.

### 3.1 Install SvxLink using SvxLink Bootstrap

For a new installation, first install and configure SvxLink using the established SvxLink Bootstrap procedure.

Follow the current instructions at:

https://g4nab.co.uk/svxlink-single-node-initial-setup/

The Bootstrap process establishes the SvxLink environment and supports installation of SvxLink-Dash V4.1.

Complete the SvxLink configuration and verify normal radio and reflector operation before adding an OLED.

Existing operational installations do not need to repeat this procedure.

### 3.2 Confirm SvxLink-Dash V4.1

SvxLink-OLED obtains its information from the existing SvxLink-Dash status API.

Confirm that SvxLink-Dash V4.1 is installed, operational and reporting the correct local node status.

On the Raspberry Pi, check:

```bash
curl -fsS http://127.0.0.1/api/status
```

If Dash uses port 5000:

```bash
curl -fsS http://127.0.0.1:5000/api/status
```

The API must report the local callsign, receiver and transmitter activity, reflector status and active talkgroup.

No changes to the SvxLink-Dash API are necessary.

### 3.3 OLED hardware and software requirements

- Raspberry Pi running Debian Bookworm, Trixie or a compatible Linux distribution.
- Python 3.11 or newer recommended.
- Operational SvxLink-Dash V4.1 installation.
- Suitable SSD1315, SSD1306, SH1106 or SH1107 I²C OLED.
- Accessible I²C interface with compatible electrical connections.
- Root privileges for installation.
- Existing `svxlink` service account.
- Network access during installation for APT and Python dependencies.

The installer creates a separate Python virtual environment for SvxLink-OLED.

### 3.4 ICS controller installations

For ICS-equipped Raspberry Pis, retain the existing ICS hardware preparation and configuration.

The OLED installer must not automatically modify ICS overlays, GPIO assignments, audio configuration or GPIO expanders.

Verify that the selected I²C bus and physical connections can safely accommodate the OLED before connecting it.

### 3.5 Installation order

1. Install and configure SvxLink using Bootstrap.
2. Confirm SvxLink-Dash V4.1 is operational.
3. Verify the local status API.
4. Check the selected I²C bus and physical pin availability.
5. Connect and verify the OLED hardware.
6. Run the SvxLink-OLED installer.
7. Review the OLED configuration.
8. Enable and test the SvxLink-OLED systemd service.

Existing SvxLink installations begin at step 2.

## 4. Verify I²C — do this before installation

From the repository root:

```bash
./install/verify-i2c.sh --check
```
The verification script checks for the selected I²C adapter without automatically scanning attached devices. Address scanning is a separate manual diagnostic operation, particularly on ICS-equipped systems.

If `/dev/i2c-1` exists, the script displays the adapter and, if `i2cdetect` is installed, addresses currently present. A visible `3c` may indicate the OLED, but does **not** identify the controller. `UU` means an address is claimed by a kernel driver; do not attempt to reassign or disturb it. A bus being present does not establish that a free connector is available.

If I²C is absent on a **plain Raspberry Pi** after checking pins and overlays, you may opt in to:

```bash
./install/verify-i2c.sh --enable
```

This explicitly asks for permission to run `sudo raspi-config nonint do_i2c 0`, and separately asks before rebooting. It refuses automatic enabling on unidentified hardware. On remote repeaters, plan the reboot in a maintenance window. After reboot, rerun `--check`.

For a nondefault I²C bus, use e.g. `OLED_I2C_BUS=0 ./install/verify-i2c.sh --check` and set the matching bus in `config/oled.ini` before installation.

## 5. Install (does not enable the service)

From the repo on the target Raspberry Pi or SBC (not the MacBook):

```bash
sudo ./install/install-oled.sh
```

The installer copies the OLED application to `/opt/svxlink-oled`, preserves `/etc/svxlink-oled/oled.ini` if present, creates `/opt/svxlink-oled/.venv`, installs the hardware library, and places a systemd service definition. It does **not** start a newly installed OLED service or modify SvxLink-Dash. It stops a previously running OLED service running and attempts to restart it, so maintenance requires coordination. No reboot is triggered by the installer.

Before actual activation, confirm the configured controller, I²C bus, address, resolution and URL in `/etc/svxlink-oled/oled.ini`. Make sure the service's `svxlink` user has access to `/dev/i2c-N`; the example service requests the `i2c` group. Verify the device at the expected address and **only after hardware validation** run:

```bash
sudo systemctl enable --now svxlink-oled.service
sudo systemctl status svxlink-oled.service
journalctl -u svxlink-oled.service -n 50 --no-pager
```

To disable without stopping SvxLink:

```bash
sudo systemctl disable --now svxlink-oled.service
```

## 6. Configuration reference

Edit `/etc/svxlink-oled/oled.ini` on the SBC:

```ini
[oled]
controller = ssd1315
interface = i2c
bus = 1
address = 0x3c
width = 128
height = 64
status_url = http://127.0.0.1/api/status
poll_seconds = 1.0
scroll_frames_per_second = 10
```

If the local Dash API uses port 5000, set `status_url = http://127.0.0.1:5000/api/status`. The hardware program deliberately accepts **localhost only** to avoid silently becoming a remote-node monitor. The MacBook's existing graphical simulator remains separate and may use its own development source URL.

## 7. Troubleshooting

- **Missing `/dev/i2c-1`:** check boot configuration, DT overlays, I²C driver and bus number. Reboot only when an enable operation actually needs it.
- **No `3c`:** check wiring, power, address, bus, module polarity and bus visibility. Do not infer that the module is defective from one scan alone.
- **Address already used:** stop; identify whether it is an OLED or an existing ICS component. Never write to an unknown address.
- **Permission denied:** check `/dev/i2c-N` permissions and membership of the `i2c` group; do not chmod the whole bus to 777.
- **Display blank:** verify installed controller, supported driver version and display power; check service journal.
- **OFFLINE:** confirm local Dash API URL and port using `curl -fsS http://127.0.0.1/api/status` (or configured local port).
- **Talkgroup doesn't move:** numerical TGs normally fit and should remain stationary. Only overflowed text scrolls.
- **SH1107:** 128×128 controller support is planned, but the current renderer still needs a tailored layout.

## 8. Test and release boundaries

Previously established on MacBook: Pillow image generation, correct status retrieval from MB5HT, RF-driven RX/TX detection, Tkinter simulation, text clipping and scroll calculations. The new `oled/hardware.py` and installation scripts have not yet been exercised on an actual Linux target. Do not deploy them to a critical site without review, I²C validation and a physical display test. This is a foundation, not a production release.

## 9. Developer repository hygiene

Keep `.venv/`, `.venv-python39/`, `__pycache__/`, `*.py[cod]` and `.DS_Store` in `.gitignore`. From the repository root:

```bash
python3 -m compileall -q oled
bash -n install/verify-i2c.sh install/install-oled.sh
git diff --check
git status --short
```

Stage and commit only after checking the new and modified files, then test installations on a noncritical Raspberry Pi before releasing.

## 10. Acknowledgements

SvxLink is developed by Tobias Blomberg SM0SVX and contributors. SvxLink-OLED is a separate accessory project by Chris Jackson G4NAB, building on the established SvxLink-Dash, SvxLink-Touch and SvxLink-LCD workflows.
