#!/bin/bash
# Local Flannels runner with dual webhook notifications and retry logic
# This script runs Flannels scraper locally and sends to both dev and production webhooks

# Set environment variables
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/1417784756954730596/oVMLzhto-F-0cEDNcvQ6e9NrapVyzQFVFpsxOR_4o8UytTkgAS0wxN8U8ivt6hYk1ppw"
export DISCORD_WEBHOOK_DEV_URL="https://discord.com/api/webhooks/1419426002094002347/WPX3QUO1Ow2QjAhKQMpZ2bC3H49f6nKZAF0JcwqVvfOTXmdvo2ROHBWkaaKroapFFZn5"

# Navigate to project directory
cd ~/discount-notifier

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment
source .venv/bin/activate

# Log start
echo "$(date): Starting local Flannels scraper run" >> logs/flannels_local.log

# Function to send notification with retry logic
send_notification_with_retry() {
    local webhook_url="$1"
    local webhook_name="$2"
    local max_retries=3
    local retry_count=0
    
    while [ $retry_count -lt $max_retries ]; do
        echo "$(date): Attempting to send notification to $webhook_name (attempt $((retry_count + 1))/$max_retries)" >> logs/flannels_local.log
        
        # Run Flannels scraper and capture output
        if python3 run_scrapers.py --flannel >> logs/flannels_local.log 2>&1; then
            echo "$(date): Flannels scraper completed successfully" >> logs/flannels_local.log
            
            # Check if any high discount products were found
            if grep -q "high discount products found" logs/flannels_local.log; then
                echo "$(date): High discount products found, notification should be sent to $webhook_name" >> logs/flannels_local.log
                return 0
            else
                echo "$(date): No high discount products found, no notification needed" >> logs/flannels_local.log
                return 0
            fi
        else
            echo "$(date): Flannels scraper failed (attempt $((retry_count + 1))/$max_retries)" >> logs/flannels_local.log
            retry_count=$((retry_count + 1))
            
            if [ $retry_count -lt $max_retries ]; then
                echo "$(date): Waiting 1 minute before retry..." >> logs/flannels_local.log
                sleep 60
            fi
        fi
    done
    
    echo "$(date): Failed to send notification to $webhook_name after $max_retries attempts" >> logs/flannels_local.log
    return 1
}

# Send to production webhook
echo "$(date): Sending to production webhook" >> logs/flannels_local.log
send_notification_with_retry "$DISCORD_WEBHOOK_URL" "Production"

# Wait 30 seconds between webhook calls
sleep 30

# Send to development webhook
echo "$(date): Sending to development webhook" >> logs/flannels_local.log
send_notification_with_retry "$DISCORD_WEBHOOK_DEV_URL" "Development"

# Log completion
echo "$(date): Local Flannels scraper run completed" >> logs/flannels_local.log
