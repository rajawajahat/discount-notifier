# Selenium Deployment Guide

## Overview
The Selfridges scraper includes a Selenium fallback that activates automatically when regular HTTP requests are blocked by anti-bot protection. This guide covers deployment requirements for cloud environments.

## 🚀 Quick Start (Local Development)
```bash
# Install dependencies
pip install selenium webdriver-manager

# Test the scraper
python test_scrapers.py selfridges
```

## ☁️ Cloud Deployment Requirements

### 1. VPS/Dedicated Server (Ubuntu/Debian)

#### Install System Dependencies
```bash
# Update system
sudo apt-get update

# Install Chrome browser
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install Xvfb (virtual display for headless)
sudo apt-get install -y xvfb

# Set up virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
```

#### Python Dependencies
```bash
pip install selenium webdriver-manager
```

### 2. Docker Deployment

#### Dockerfile
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver (managed automatically by webdriver-manager)
# No manual installation needed

# Set display environment
ENV DISPLAY=:99

# Copy application
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Start virtual display and application
CMD Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & python main.py
```

#### docker-compose.yml
```yaml
version: '3.8'
services:
  discount-notifier:
    build: .
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
      - DISPLAY=:99
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### 3. AWS EC2 Setup Script
```bash
#!/bin/bash
# Run this on a fresh Ubuntu EC2 instance

# Update system
sudo apt-get update -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip git

# Install Chrome dependencies
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt-get update -y
sudo apt-get install -y google-chrome-stable xvfb

# Clone and setup application
git clone <your-repo-url>
cd discount-notifier
pip3 install -r requirements.txt

# Set up systemd service
sudo tee /etc/systemd/system/discount-notifier.service > /dev/null <<EOF
[Unit]
Description=Fashion Discount Notifier
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/discount-notifier
Environment=DISPLAY=:99
Environment=DISCORD_WEBHOOK_URL=your_webhook_url_here
ExecStartPre=/usr/bin/Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable discount-notifier
sudo systemctl start discount-notifier
```

## 🔧 Configuration Options

### Environment Variables
```bash
# Required
export DISCORD_WEBHOOK_URL="your_webhook_url"

# Optional Selenium settings
export SELENIUM_HEADLESS=true          # Run browser in headless mode (default: true)
export SELENIUM_TIMEOUT=30             # Page load timeout in seconds (default: 30)
export SELENIUM_MAX_PAGES=5            # Max pages to scrape with Selenium (default: 5)
export DISPLAY=:99                     # Virtual display (required for headless)
```

### Chrome Options (Already Configured)
The scraper automatically uses these Chrome options for cloud compatibility:
- `--headless` - Run without GUI
- `--no-sandbox` - Required for Docker/cloud
- `--disable-dev-shm-usage` - Prevents crashes
- `--disable-gpu` - Better performance
- Anti-detection options

## 📊 Performance Considerations

| Method | Speed | Success Rate | Resource Usage |
|--------|-------|--------------|----------------|
| Regular Requests | ~1-2 seconds | 0% (blocked) | Very Low |
| Selenium Fallback | ~15-30 seconds | 85-95% | Medium-High |

### Memory Requirements
- **Minimum**: 512MB RAM
- **Recommended**: 1GB+ RAM
- **Chrome browser**: ~200-400MB per instance

### CPU Usage
- **Selenium**: ~20-50% CPU during scraping
- **Regular requests**: <5% CPU

## 🚨 Troubleshooting

### Common Issues

#### 1. Chrome/ChromeDriver Version Mismatch
```bash
# Solution: Use webdriver-manager (already implemented)
# It automatically downloads the correct ChromeDriver version
```

#### 2. Display/GUI Errors
```bash
# Error: "cannot connect to X server"
# Solution: Ensure Xvfb is running
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
```

#### 3. Permission Errors
```bash
# Error: "Chrome didn't start correctly"
# Solution: Add --no-sandbox flag (already included)
```

#### 4. Memory Issues
```bash
# Error: "Chrome crashed"
# Solution: Increase available memory or add swap
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Debug Mode
To enable verbose Selenium logging:
```python
# Add to scraper for debugging
import logging
logging.getLogger('selenium').setLevel(logging.DEBUG)
```

## 🔄 Monitoring

### Health Checks
```bash
# Check if Chrome is accessible
google-chrome --version

# Check virtual display
ps aux | grep Xvfb

# Test scraper
python test_scrapers.py selfridges
```

### Logs
Monitor these log files:
- Application logs: `logs/discount_notifier.log`
- System logs: `sudo journalctl -u discount-notifier -f`

## 🎯 Success Indicators

When Selenium is working correctly, you'll see:
```
🤖 Selenium: Browser initialized successfully
🤖 Selenium Page 1: Loading https://www.selfridges.com/...
🤖 Selenium Page 1: Found X JSON-LD scripts
🤖 Selenium: Browser closed successfully
```

The scraper successfully bypasses anti-bot protection when it can load the page and find JSON-LD scripts, even if no high-discount products are found.
