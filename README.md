# SvxLink-OLED — Installation and User Guide

**Small, read-only display for an existing SvxLink node**  
**Version 0.1 — first hardware-test release**

SvxLink-OLED shows your node callsign, the connected reflector, RX and TX activity, and the current talkgroup. It does not control the radio or change any SvxLink settings.

This guide is for someone who **already has SvxLink and SvxLink-Dash V4.1 working on a Raspberry Pi**, has attached a compatible OLED, and wants to turn it on.

If SvxLink and SvxLink-Dash are not installed yet, follow [the SvxLink initial setup guide](https://g4nab.co.uk/svxlink-single-node-initial-setup/) first. **Do not repeat that installation if your node already works.**

## 1. Before you begin

You need:

- A Raspberry Pi running SvxLink and SvxLink-Dash V4.1.
- A supported I²C OLED display connected to the Raspberry Pi.
- An internet connection on the Raspberry Pi for downloading the software and its dependencies.
- Terminal access to the Pi, either directly or by SSH.

Supported display configurations for this first version:

| Display controller | Screen resolution |
| --- | --- |
| SSD1315 (default) | 128 × 64 |
| SSD1306 | 128 × 64 |
| SH1106 | 128 × 64 |
| SH1107 | 128 × 128 (layout still being refined) |

The usual OLED address is **0x3C**. Some boards mark this as **0x78**; do not enter 0x78 in the software.

**If the Pi uses an ICS controller or other hardware on its GPIO header, confirm that the OLED connections and I²C address are compatible before proceeding.** Do not reconnect wires while the Raspberry Pi is powered.

## 2. Enable I²C

If you have already enabled I²C using `sudo raspi-config` and rebooted, move straight to Step 3.

Otherwise, in the Raspberry Pi terminal, enter:

```bash
sudo raspi-config
```

Choose **Interface Options → I2C → Enable**. Exit and reboot if requested. Then reconnect to the Pi.

This procedure is for an ordinary Raspberry Pi. On an ICS-equipped installation, follow the controller's existing hardware preparation instructions instead of changing overlays without checking.

## 3. Download SvxLink-OLED

Enter these commands **on the Raspberry Pi**, not on your desktop computer:

```bash
sudo apt-get update
sudo apt-get install -y git
cd /home/pi
git clone https://github.com/f5vmr/Svxlink-OLED.git
cd Svxlink-OLED
```

**Maintainer check before publication:** confirm the exact GitHub address above matches the published SvxLink-OLED project. If your Pi username is not `pi`, use `cd ~` instead of `cd /home/pi`.

The download creates a folder containing the program and installation scripts. You do not need to edit any source code.

## 4. Check that the I²C connection is available

While still in the `Svxlink-OLED` folder, run:

```bash
./install/verify-i2c.sh --check
```

A successful check reports **`I2C adapter present: /dev/i2c-1`** and **PASS**.

This proves the Raspberry Pi has an I²C interface; it does **not** prove that the OLED is connected correctly. The check deliberately does not scan other devices on the bus.

If it reports that `/dev/i2c-1` is missing, recheck Step 2. Do not proceed with the installation until the interface is available.

## 5. Install the display software

Run:

```bash
sudo ./install/install-oled.sh
```

The installer downloads the required Python libraries, installs the OLED program, and prepares it to run automatically when enabled. It may take a little time on the first installation.

**The installer does not switch on a new OLED service.** That is done in Step 7, after the settings have been checked.

## 6. Check the display settings

Most owners of a **128 × 64 SSD1315 OLED on I²C bus 1, address 0x3C** can keep the default settings.

To view or change them, run:

```bash
sudo nano /etc/svxlink-oled/oled.ini
```

The standard settings are:

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

Only change the values that differ from your display. For example, for an SH1106 use `controller = sh1106`. For a 128 × 128 SH1107, use `controller = sh1107` and `height = 128`.

The status address beginning `127.0.0.1` is intentional: it means **this Raspberry Pi**. Do not replace it with the address of another node. If SvxLink-Dash runs on port 5000 instead of its usual port 80, use:

```ini
status_url = http://127.0.0.1:5000/api/status
```

To save in Nano, press **Ctrl+O**, then **Enter**, followed by **Ctrl+X** to exit.

## 7. Start the OLED

After checking the display type, connections and settings, enter:

```bash
sudo systemctl enable --now svxlink-oled.service
```

The OLED should now display the local node's status. It will start automatically whenever the Raspberry Pi boots.

To check whether the program is running:

```bash
sudo systemctl status svxlink-oled.service --no-pager
```

Look for **`active (running)`**. A running service does not by itself prove that pixels are visible; check the OLED itself as well.

## 8. What you should see

The display shows:

- **Top left:** your node's callsign.
- **Top right:** the reflector name, if available.
- **Middle:** RX and TX indicators, showing active or idle.
- **Bottom:** the current talkgroup or Standby.

Long talkgroup text may scroll from side to side. Short talkgroup numbers remain still. When local status cannot be read, the display should show an offline indication rather than pretend the receiver or transmitter is active.

## 9. If the display remains blank

First check the program's messages:

```bash
sudo journalctl -u svxlink-oled.service -n 50 --no-pager
```

Then check these common causes:

| Problem | What to check |
| --- | --- |
| OLED stays black | Power connections, correct controller in `oled.ini`, and service messages |
| I²C interface missing | I²C enabled in `raspi-config`, correct bus, reboot if required |
| Service says permission denied | I²C device permissions and the `i2c` group |
| Display reports OFFLINE | SvxLink-Dash running locally, and correct API port in `oled.ini` |
| Text appears incorrect | Display controller and resolution settings |

On a **plain Raspberry Pi with no other I²C peripherals**, an optional address check is:

```bash
sudo apt-get install -y i2c-tools
sudo i2cdetect -y 1
```

A response at `3c` is consistent with the usual OLED address, but does not identify its controller. **Do not scan an I²C bus shared with an ICS controller or unknown peripherals without checking that it is safe.**

## 10. Everyday use

No buttons or controls are needed. The display updates automatically as SvxLink operates.

To restart just the display software:

```bash
sudo systemctl restart svxlink-oled.service
```

To stop the display:

```bash
sudo systemctl stop svxlink-oled.service
```

To stop it and prevent it from starting at boot:

```bash
sudo systemctl disable --now svxlink-oled.service
```

These commands affect **SvxLink-OLED only**, not the SvxLink radio service or SvxLink-Dash.

## 11. Updating SvxLink-OLED

When an update is published, return to the folder used in Step 3:

```bash
cd ~/Svxlink-OLED
git pull
sudo ./install/install-oled.sh
```

The installer retains your existing `/etc/svxlink-oled/oled.ini` settings. If the OLED service was running, the upgrade procedure attempts to restart it when installation completes. If an upgrade fails, check the messages in Step 9. The installer does not provide automatic rollback.

## 12. Acknowledgements and support

SvxLink is developed by Tobias Blomberg **SM0SVX** and contributors. SvxLink-OLED is an independent, optional accessory developed by **Chris Jackson G4NAB**, using status information provided by SvxLink-Dash V4.1.

For dashboard-related support: **dashboard-support@g4nab.co.uk**.

**Release note:** Version 0.1 is undergoing its first physical-display tests. Controller support and the 128 × 128 layout have not yet been fully verified on hardware.
