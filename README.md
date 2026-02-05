# Echo Archery Detection System
## Installation Guide for Raspberry Pi 5

---

## Prerequisites

- Raspberry Pi 5 (8GB)
- Camera Module 3 (connected via CSI port)
- MicroSD card (32GB+ recommended, Class 10)
- Power bank (20,000mAh+ recommended for full day)
- Tripod with phone mount adapter
- Fresh Raspberry Pi OS Lite image

---

## Step 1: Initial Raspberry Pi Setup

### 1.1 Flash Raspberry Pi OS

1. Download **Raspberry Pi Imager**: https://www.raspberrypi.com/software/
2. Insert microSD card into your computer
3. Run Raspberry Pi Imager:
   - **Device**: Raspberry Pi 5
   - **OS**: Raspberry Pi OS Lite (64-bit) - under "Raspberry Pi OS (other)"
   - **Storage**: Your microSD card

4. Click **Settings** (gear icon):
   - Set hostname: `echo`
   - Enable SSH (use password authentication)
   - Set username: `pi`
   - Set password: `echo2024` (or your choice)
   - Configure wireless LAN (your home WiFi for initial setup)
   - Set locale settings (timezone, keyboard)

5. Click **Save**, then **Write**

### 1.2 First Boot

1. Insert microSD into Raspberry Pi 5
2. Connect Camera Module 3 to CSI port (gently lift connector, insert ribbon with contacts facing connector pins, press down)
3. Power on with USB-C power supply or power bank
4. Wait 2-3 minutes for first boot

### 1.3 Connect via SSH

From your computer (on same WiFi):

```bash
ssh pi@echo.local
# Password: echo2024 (or what you set)
```

If `echo.local` doesn't work, find IP from your router and use:
```bash
ssh pi@192.168.1.xxx
```

---

## Step 2: Automated Installation

### 2.1 Download Installation Script

Once connected via SSH:

```bash
cd ~
wget https://raw.githubusercontent.com/YOUR_REPO/inoxia-echo/main/install.sh
chmod +x install.sh
```

**OR** copy the install.sh script manually (provided below) to the Pi.

### 2.2 Run Installation

```bash
./install.sh
```

This will:
- Update system packages
- Install Python dependencies (OpenCV, Flask, picamera2)
- Install Echo software
- Configure WiFi Access Point
- Set up systemd service for auto-start
- Enable camera interface

**Installation takes 15-30 minutes.** The Pi will reboot automatically when done.

### 2.3 After Reboot

The Pi will now:
- Create WiFi network: **Echo-Archery**
- Password: **arrows2024**
- Web interface available at: **http://10.0.0.1**

---

## Step 3: First Use

### 3.1 Connect iPad to Echo

1. On iPad, go to Settings → WiFi
2. Connect to network: **Echo-Archery**
3. Password: **arrows2024**
4. Open Chrome browser
5. Navigate to: **http://10.0.0.1**

### 3.2 Initial Calibration

1. Mount Pi camera on tripod, position 2-4m from target
2. Target should be empty (no arrows)
3. In web interface, select target size (80cm or 122cm)
4. Click **"Calibrate Camera"**
5. Verify target is detected (rings should be highlighted)
6. Click **"Start Detection"**

### 3.3 Shooting Session

- Shoot arrows normally
- System automatically detects each new arrow
- Arrow positions appear on virtual target in real-time
- Session data logged continuously

### 3.4 End Session

- Click **"Shutdown System"** in web interface
- Wait 30 seconds for safe shutdown
- Disconnect power

---

## Manual Installation (if automated script fails)

### Install System Dependencies

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3-pip python3-opencv python3-flask \
    python3-numpy hostapd dnsmasq git
```

### Install Python Packages

```bash
pip3 install --break-system-packages picamera2 flask opencv-python-headless numpy
```

### Enable Camera

```bash
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
# Finish and reboot
```

### Configure Access Point

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add:
```
interface=wlan0
driver=nl80211
ssid=Echo-Archery
hw_mode=g
channel=6
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=arrows2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

```bash
sudo nano /etc/dnsmasq.conf
```

Add:
```
interface=wlan0
dhcp-range=10.0.0.2,10.0.0.20,255.255.255.0,24h
```

```bash
sudo nano /etc/dhcpcd.conf
```

Add at end:
```
interface wlan0
    static ip_address=10.0.0.1/24
    nohook wpa_supplicant
```

### Enable Services

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq
```

### Clone Echo Software

```bash
cd /home/pi
git clone https://github.com/YOUR_REPO/inoxia-echo.git
cd echo-archery
```

Or manually create the directory structure and copy files (see next sections).

### Create Systemd Service

```bash
sudo nano /etc/systemd/system/echo.service
```

Add:
```ini
[Unit]
Description=Echo Archery Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/echo
ExecStart=/usr/bin/python3 /home/pi/echo/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable echo.service
```

### Reboot

```bash
sudo reboot
```

---

## Troubleshooting

### Camera Not Detected

```bash
# Test camera
libcamera-still -o test.jpg

# If fails, check cable connection
# Ensure camera is enabled: sudo raspi-config
```

### WiFi AP Not Starting

```bash
# Check hostapd status
sudo systemctl status hostapd

# Check dnsmasq status
sudo systemctl status dnsmasq

# View logs
sudo journalctl -u hostapd -n 50
```

### Web Server Not Starting

```bash
# Check Echo service
sudo systemctl status echo

# View logs
sudo journalctl -u echo -n 50

# Run manually for debugging
cd /home/pi/echo
python3 main.py
```

### Can't Connect to WiFi

- Ensure you're in range (10-30m typical)
- Try restarting Pi
- Check password: **arrows2024**
- Forget network on iPad and reconnect

### Detection Not Working

- Recalibrate with empty target
- Check lighting (avoid direct sun into camera)
- Ensure target is in frame (check preview)
- Try adjusting camera position/angle
- Check arrow colors (bright fletching helps)

---

## File Structure

After installation, your Pi should have:

```
/home/pi/echo/
├── main.py                 # Main application
├── detector.py             # Arrow detection logic
├── camera_manager.py       # Camera interface
├── config.py              # Configuration
├── templates/
│   └── index.html         # Web interface
├── static/
│   └── style.css          # Styling
└── sessions/              # Session data (auto-created)
```

---

## Default Configuration

Edit `/home/pi/echo/config.py` to change:

- Detection sensitivity
- WiFi credentials
- Web server port
- Camera resolution
- Target sizes
- Processing parameters

After changes:
```bash
sudo systemctl restart echo
```

---

## Performance Tips

1. **Power**: Use 20,000mAh+ power bank for all-day use
2. **Positioning**: 2-3 meters from target ideal
3. **Lighting**: Overcast or even lighting best
4. **Angle**: Keep camera perpendicular to target (±15° max)
5. **Calibration**: Recalibrate if lighting changes significantly

---

## Safety Shutdown

Always use **"Shutdown System"** button in web interface before disconnecting power.

Force shutdown only if frozen:
```bash
sudo shutdown -h now
```

Wait for green LED to stop flashing before removing power.

---

## Updates

To update Echo software:

```bash
cd /home/pi/echo
git pull
sudo systemctl restart echo
```

---

## Support

System logs:
```bash
sudo journalctl -u echo -f
```

Camera test:
```bash
libcamera-still -o /tmp/test.jpg
```

Network test:
```bash
ip addr show wlan0
```

---

## Next Steps

Proceed to copy the application files in the following order:
1. config.py
2. camera_manager.py
3. detector.py
4. main.py
5. templates/index.html

All files will be provided in subsequent artifacts.
