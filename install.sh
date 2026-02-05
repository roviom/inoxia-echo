#!/bin/bash
#
# Echo Archery Detection System - Automated Installation
# For Raspberry Pi 5 with Camera Module 3
#
# Usage: ./install.sh
#

set -e  # Exit on error

echo "=========================================="
echo "Echo Archery Detection System Installer"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo "ERROR: Do not run this script as root/sudo"
    echo "Run as: ./install.sh"
    exit 1
fi

# Confirm installation
echo "This will install Echo on your Raspberry Pi 5."
echo "Installation takes 15-30 minutes."
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 0
fi

echo ""
echo "[1/8] Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "[2/8] Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-opencv \
    python3-flask \
    python3-numpy \
    hostapd \
    dnsmasq \
    git \
    libcamera-apps

echo ""
echo "[3/8] Installing Python packages..."
pip3 install --break-system-packages \
    picamera2 \
    flask \
    opencv-python-headless \
    numpy

echo ""
echo "[4/8] Enabling camera interface..."
sudo raspi-config nonint do_camera 0

echo ""
echo "[5/8] Creating Echo directory structure..."
mkdir -p /home/pi/echo/templates
mkdir -p /home/pi/echo/static
mkdir -p /home/pi/echo/sessions

echo ""
echo "[6/8] Configuring WiFi Access Point..."

# Stop services if running
sudo systemctl stop hostapd 2>/dev/null || true
sudo systemctl stop dnsmasq 2>/dev/null || true

# Configure hostapd
sudo tee /etc/hostapd/hostapd.conf > /dev/null <<EOF
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
EOF

# Point hostapd to config file
sudo tee /etc/default/hostapd > /dev/null <<EOF
DAEMON_CONF="/etc/hostapd/hostapd.conf"
EOF

# Configure dnsmasq
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig 2>/dev/null || true
sudo tee /etc/dnsmasq.conf > /dev/null <<EOF
interface=wlan0
dhcp-range=10.0.0.2,10.0.0.20,255.255.255.0,24h
domain=local
address=/echo.local/10.0.0.1
EOF

# Configure static IP for wlan0
sudo tee -a /etc/dhcpcd.conf > /dev/null <<EOF

# Echo Archery AP Configuration
interface wlan0
    static ip_address=10.0.0.1/24
    nohook wpa_supplicant
EOF

# Enable IP forwarding (optional, for future internet sharing)
sudo sed -i 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf

# Unmask and enable services
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl enable dnsmasq

echo ""
echo "[7/8] Creating Echo systemd service..."
sudo tee /etc/systemd/system/echo.service > /dev/null <<EOF
[Unit]
Description=Echo Archery Detection System
After=network.target hostapd.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/echo
ExecStart=/usr/bin/python3 /home/pi/echo/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable echo.service

echo ""
echo "[8/8] Installation complete!"
echo ""
echo "=========================================="
echo "IMPORTANT: Next Steps"
echo "=========================================="
echo ""
echo "1. Copy the Echo application files to /home/pi/echo/"
echo "   Required files:"
echo "   - config.py"
echo "   - camera_manager.py"
echo "   - detector.py"
echo "   - main.py"
echo "   - templates/index.html"
echo ""
echo "2. After copying files, reboot:"
echo "   sudo reboot"
echo ""
echo "3. After reboot, Echo will create WiFi network:"
echo "   SSID: Echo-Archery"
echo "   Password: arrows2024"
echo "   Web interface: http://10.0.0.1"
echo ""
echo "=========================================="
echo ""

read -p "Reboot now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
else
    echo "Remember to reboot before using Echo!"
fi
