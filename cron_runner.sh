#!/bin/bash
# Production cron runner for discount scraper
# This script handles logging, error handling, and log rotation

# Set environment variables
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1417784756954730596/oVMLzhto-F-0cEDNcvQ6e9NrapVyzQFVFpsxOR_4o8UytTkgAS0wxN8U8ivt6hYk1ppw"
export DISCORD_WEBHOOK_DEV_URL="your_dev_webhook_url_here"

# Navigate to project directory
cd ~/discount-notifier

# Create logs directory if it doesn't exist
mkdir -p logs

# Set up log rotation (keep only last 10 log files)
find logs/ -name "scraper_run_*.log" -type f | sort | head -n -10 | xargs -r rm

# Activate virtual environment
source venv/bin/activate

# Log start
echo "$(date): Starting discount scraper run" >> logs/cron.log

# Run scrapers (skip Flannels due to IP blocking)
if python3 run_scrapers.py --end --harvey --harrods --selfridges >> logs/cron.log 2>&1; then
    echo "$(date): Scraper completed successfully" >> logs/cron.log
else
    echo "$(date): Scraper run failed with exit code $?" >> logs/cron.log
fi

# Log completion
echo "$(date): Cron job completed" >> logs/cron.log