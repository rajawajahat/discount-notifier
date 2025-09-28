#!/bin/bash
# Production cron runner for discount scraper
# This script handles logging, error handling, and cleanup for cron jobs

# Set working directory
cd /root/discount-notifier

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH=/root/discount-notifier
export PATH="/usr/local/bin:$PATH"

# Create logs directory if it doesn't exist
mkdir -p logs

# Set up log rotation (keep only last 10 log files)
find logs/ -name "scraper_run_*.log" -type f | sort | head -n -10 | xargs -r rm

# Run the scraper with minimal output
echo "$(date): Starting discount scraper run" >> logs/cron.log

# Run the production script and capture output
python3 run_scrapers_production.py >> logs/cron.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "$(date): Scraper completed successfully" >> logs/cron.log
else
    echo "$(date): Scraper failed with exit code $?" >> logs/cron.log
fi

# Clean up old logs (keep last 7 days)
find logs/ -name "scraper_run_*.log" -type f -mtime +7 -delete

# Deactivate virtual environment
deactivate
