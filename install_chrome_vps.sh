#!/bin/bash

# Chrome Installation Script for VPS
# This script installs Chrome and all required dependencies for Selenium

echo "🔧 Installing Chrome and dependencies for VPS..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required dependencies
echo "📦 Installing dependencies..."
sudo apt install -y wget gnupg software-properties-common curl unzip

# Install Chrome
echo "🌐 Installing Google Chrome..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install -y google-chrome-stable

# Install additional dependencies for headless Chrome
echo "📦 Installing additional dependencies..."
sudo apt install -y xvfb fonts-liberation libasound2 libatk-bridge2.0-0 libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libnss3

# Verify Chrome installation
echo "✅ Verifying Chrome installation..."
if command -v google-chrome &> /dev/null; then
    echo "✅ Chrome installed successfully"
    google-chrome --version
else
    echo "❌ Chrome installation failed, trying Chromium..."
    
    # Install Chromium as fallback
    sudo apt install -y chromium-browser
    
    if command -v chromium-browser &> /dev/null; then
        echo "✅ Chromium installed successfully"
        chromium-browser --version
    else
        echo "❌ Both Chrome and Chromium installation failed"
        exit 1
    fi
fi

# Test headless Chrome
echo "🧪 Testing headless Chrome..."
if command -v google-chrome &> /dev/null; then
    google-chrome --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Chrome headless test successful"
    else
        echo "⚠️  Chrome headless test failed, but Chrome is installed"
    fi
elif command -v chromium-browser &> /dev/null; then
    chromium-browser --headless --disable-gpu --no-sandbox --dump-dom https://www.google.com > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Chromium headless test successful"
    else
        echo "⚠️  Chromium headless test failed, but Chromium is installed"
    fi
fi

echo "🎉 Chrome installation completed!"
echo ""
echo "📋 Next steps:"
echo "1. Test Selfridges scraper: python3 run_selfridges_vps.py --dev"
echo "2. If you get Chrome errors, try: python3 run_selfridges_vps.py --dev"
echo "3. Check logs in logs/ directory for detailed error messages"
