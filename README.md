# 🔥 Fashion Discount Notifier

A scalable, modular web scraping service that monitors men's fashion sales across premium UK retailers and sends Discord notifications when products have high discounts (≥70%).

## 🚀 Features

- **🏪 Multi-Retailer Support**: Monitors Harvey Nichols, Flannels, Selfridges, Harrods, and END Clothing
- **🔔 Smart Notifications**: Only alerts on products with ≥70% discount via Discord webhooks
- **⚙️ Modular Architecture**: Easy to add new retailers with minimal code changes
- **🤖 Selenium Fallback**: Automatic browser automation for anti-bot protection
- **📊 Comprehensive Logging**: Detailed logging and error handling
- **💪 Robust**: Built-in retry logic, rate limiting, and health checks
- **🐳 Production Ready**: Docker, systemd, and supervisor deployment options

## 📋 Requirements

- Python 3.11+
- Discord webhook URL
- Internet connection for scraping
- Chrome browser (for Selenium fallback)

## 🚀 Quick Start

### Option 1: Simple Execution (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd discount-notifier

# Install dependencies
pip install -r requirements.txt

# Set your Discord webhook
export DISCORD_WEBHOOK_URL="your-discord-webhook-url-here"

# Run once (development)
python run_scrapers.py --dev

# Run once (production)
python run_scrapers.py
```

### Option 2: VPS/Server Deployment

```bash
# Run the automated installer (Ubuntu/Debian/CentOS)
sudo bash deploy/install.sh

# The installer will:
# - Install system dependencies
# - Create service user
# - Setup virtual environment
# - Configure systemd service
# - Start the service automatically
```

## 🎯 Usage

### Basic Commands

```bash
# Run all scrapers once (development webhook)
python run_scrapers.py --dev

# Run all scrapers once (production webhook)
python run_scrapers.py

# The script will:
# - Run all 5 scrapers (Flannels, Harrods, Harvey Nichols, Selfridges, END Clothing)
# - Send Discord notifications for products with ≥70% discount
# - Show detailed progress and results
```

### Webhook Configuration

The script automatically uses the appropriate webhook:

- **Development**: `--dev` flag uses testing webhook
- **Production**: Default uses production webhook
- **Custom**: Set `DISCORD_WEBHOOK_URL` environment variable

## 🏪 Supported Retailers

| Retailer | URL | Method | Status |
|----------|-----|--------|--------|
| Harvey Nichols | `https://www.harveynichols.com/sale/mens/` | API | ✅ Active |
| Flannels | `https://www.flannels.com/clearance/men/clothing` | API | ✅ Active |
| Selfridges | `https://www.selfridges.com/GB/en/cat/mens/on_sale/` | Selenium | ✅ Active |
| Harrods | `https://www.harrods.com/en-gb/sale/men` | HTML + JSON-LD | ✅ Active |
| END Clothing | `https://www.endclothing.com/gb/sale` | HTML | ✅ Active |

## 🔔 Discord Notifications

The system sends rich Discord notifications for high-discount products including:

- 🔥 Product name with discount percentage
- 💰 Original and sale prices
- 📊 Discount amount and percentage
- 🏪 Retailer information
- 🕐 Discovery timestamp
- 🖼️ Product image (when available)
- 🔗 Direct link to product

## 🏗️ Architecture

### Project Structure

```
discount-notifier/
├── scrapers/                    # Individual retailer scrapers
│   ├── base.py                 # Abstract scraper interface
│   ├── flannels.py             # Flannels API scraper
│   ├── harrods.py              # Harrods HTML + JSON-LD scraper
│   ├── harvey_nichols.py       # Harvey Nichols API scraper
│   ├── selfridges.py           # Selfridges Selenium scraper
│   └── end_clothing.py         # END Clothing HTML scraper
├── notifications/
│   └── discord_notifier.py     # Discord webhook handler
├── utils/
│   └── logging_setup.py        # Logging configuration
├── deploy/                     # Deployment configurations
│   ├── install.sh              # Automated installer
│   ├── systemd/                # Systemd service files
│   └── supervisor/             # Supervisor configuration
├── run_scrapers.py             # Main execution script
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Adding New Retailers

1. Create a new scraper class inheriting from `BaseScraper`:

```python
from scrapers.base import BaseScraper, Product

class NewRetailerScraper(BaseScraper):
    def __init__(self):
        super().__init__("New Retailer", "https://example.com/sale")
    
    def scrape_products(self) -> List[Product]:
        # Implementation here
        pass
    
    def parse_product_data(self, element) -> Optional[Product]:
        # Implementation here
        pass
```

2. Add it to `run_scrapers.py`:

```python
from scrapers.new_retailer import NewRetailerScraper

# In the scrapers list:
scrapers = [
    (FlannelsScraper, "Flannels"),
    (HarrodsScraper, "Harrods"),
    (HarveyNicholsScraper, "Harvey Nichols"),
    (SelfridgesScraper, "Selfridges"),
    (EndClothingScraper, "END Clothing"),
    (NewRetailerScraper, "New Retailer")  # Add here
]
```

## 🤖 Selenium Deployment

The Selfridges scraper includes automatic Selenium fallback for anti-bot protection. This section covers cloud deployment requirements.

### Local Development

```bash
# Install dependencies
pip install selenium webdriver-manager

# Test the scraper
python run_scrapers.py --dev
```

### Cloud Deployment Requirements

#### VPS/Dedicated Server (Ubuntu/Debian)

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

#### AWS EC2 Setup Script

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
ExecStart=/usr/bin/python3 run_scrapers.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable discount-notifier
sudo systemctl start discount-notifier
```

### Selenium Configuration

#### Environment Variables

```bash
# Required
export DISCORD_WEBHOOK_URL="your_webhook_url"

# Optional Selenium settings
export SELENIUM_HEADLESS=true          # Run browser in headless mode (default: true)
export SELENIUM_TIMEOUT=30             # Page load timeout in seconds (default: 30)
export SELENIUM_MAX_PAGES=5            # Max pages to scrape with Selenium (default: 5)
export DISPLAY=:99                     # Virtual display (required for headless)
```

#### Chrome Options (Automatically Configured)

The scraper automatically uses these Chrome options for cloud compatibility:
- `--headless` - Run without GUI
- `--no-sandbox` - Required for Docker/cloud
- `--disable-dev-shm-usage` - Prevents crashes
- `--disable-gpu` - Better performance
- Anti-detection options

## 🐳 Deployment Options

### Systemd Service

```bash
# Install via script
sudo bash deploy/install.sh

# Manual service management
sudo systemctl start fashion-discount-notifier
sudo systemctl status fashion-discount-notifier
sudo journalctl -u fashion-discount-notifier -f
```

### Supervisor

```bash
# Copy configuration
sudo cp deploy/supervisor/fashion-discount-notifier.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fashion-discount-notifier
```

### Cron Jobs

```bash
# Add to crontab for hourly execution
crontab -e

# Add this line:
0 * * * * cd /path/to/discount-notifier && python run_scrapers.py
```

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

#### 1. Discord Webhook Not Working
```bash
# Verify webhook URL is correct
# Test with: python run_scrapers.py --dev
```

#### 2. Selenium Display Errors
```bash
# Error: "cannot connect to X server"
# Solution: Ensure Xvfb is running
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
```

#### 3. Chrome Permission Errors
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

To enable verbose logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run with debug output
python run_scrapers.py --dev
```

## 📊 Monitoring

### Health Checks

```bash
# Check if Chrome is accessible
google-chrome --version

# Check virtual display
ps aux | grep Xvfb

# Test scraper
python run_scrapers.py --dev
```

### Logs

Monitor these log files:
- Application logs: `logs/discount_notifier.log`
- System logs: `sudo journalctl -u fashion-discount-notifier -f`

## 🎯 Success Indicators

When the system is working correctly, you'll see:

```
🚀 Discount Notifier - Full Scraping Run
============================================================
⏰ Started at: 14:30:15 on 15/01/2025

🔍 Running Flannels
============================================================
✅ Flannels: Completed in 12.3s
📦 Flannels: Found 3 high discount products

🔍 Running Selfridges
============================================================
🤖 Selenium: Browser initialized successfully
🤖 Selenium Page 1: Loading https://www.selfridges.com/...
✅ Selfridges: Completed in 45.2s
📦 Selfridges: Found 0 high discount products

📊 FINAL SUMMARY
============================================================
✅ Successful scrapers: 5/5
❌ Failed scrapers: 0
📦 Total high discount products: 3
⏰ Total runtime: 120.5s
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd discount-notifier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Testing Individual Scrapers

```bash
# Test single scraper
python -c "
from scrapers.flannels import FlannelsScraper
scraper = FlannelsScraper()
products = scraper.scrape_products()
print(f'Found {len(products)} products')
"

# Test Discord notifications
python -c "
from notifications.discord_notifier import DiscordNotifier
notifier = DiscordNotifier('your-webhook-url')
notifier.test_webhook()
"
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

- Create an issue for bugs or feature requests
- Check logs for troubleshooting
- Use `python run_scrapers.py --dev` for testing

---

**⚠️ Disclaimer**: This tool is for educational purposes. Please respect robots.txt and terms of service of the scraped websites. Use reasonable scraping intervals to avoid overloading servers.