#!/bin/bash
set -e
echo "=== ThaiClub AutoBet APK Builder ==="
sudo apt-get update -qq
sudo apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool \
  pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 \
  cmake libffi-dev libssl-dev ccache python3-pip python3-venv
pip3 install --upgrade pip
pip3 install buildozer Cython==0.29.33 virtualenv
cd "$(dirname "$0")"
buildozer -v android debug
echo ""
echo "=== DONE ==="
ls bin/*.apk 2>/dev/null || echo "Check bin/ folder"
echo ""
echo "Install: adb install bin/*.apk"
