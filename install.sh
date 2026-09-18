#!/data/data/com.termux/files/usr/bin/bash
set -e
echo "[*] Installing ShadowChat deps..."
pkg update -y && pkg upgrade -y
pkg install -y python git cmake libffi openssl termux-api
pip install --upgrade pip
pip install -r requirements.txt
chmod +x shadowchat.py
echo "[+] Done. Run: python shadowchat.py"
