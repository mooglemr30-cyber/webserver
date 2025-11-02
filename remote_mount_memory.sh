#!/usr/bin/env bash
set -euo pipefail

# Mount Samba share for AI agent memory (/home/admin1/aimemory)
# Adjust variables below as needed for your environment.

SAMBA_SERVER="192.168.1.29"
SAMBA_SHARE="aimemory"   # remote share name
MOUNT_POINT="/home/admin1/aimemory"  # local mount target
USER="pearce"
PASS="pearce"

echo "[+] Ensuring mount point exists: $MOUNT_POINT"
sudo mkdir -p "$MOUNT_POINT"

echo "[+] Installing cifs-utils if missing"
if ! dpkg -s cifs-utils >/dev/null 2>&1; then
  sudo apt-get update && sudo apt-get install -y cifs-utils
fi

echo "[+] Mounting //${SAMBA_SERVER}/${SAMBA_SHARE} to $MOUNT_POINT"
sudo mount -t cifs //${SAMBA_SERVER}/${SAMBA_SHARE} "$MOUNT_POINT" \
  -o username=${USER},password=${PASS},rw,uid=$(id -u),gid=$(id -g),file_mode=0664,dir_mode=0775

echo "[+] Verifying mount"
mount | grep "$MOUNT_POINT" || { echo "[-] Mount failed"; exit 1; }

echo "[+] Success. Export these for application startup:"
echo "    export AGENT_MEMORY_PATH=$MOUNT_POINT"
echo "    export AGENT_STORAGE_PATH=/home/admin1/Documents/AIAGENTSTORAGE"

echo "[+] To persist across reboots, add to /etc/fstab (optional):"
echo "//${SAMBA_SERVER}/${SAMBA_SHARE}  $MOUNT_POINT  cifs  username=${USER},password=${PASS},rw,uid=$(id -u),gid=$(id -g),file_mode=0664,dir_mode=0775  0  0"