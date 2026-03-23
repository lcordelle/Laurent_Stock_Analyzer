#!/bin/bash

# Get the current Cloudflare tunnel URL

# Check multiple log locations
CF_URL=""

# Check nohup log
if [ -f /tmp/cloudflare_nohup.log ]; then
    CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare_nohup.log 2>/dev/null | tail -1)
fi

# Check main log
if [ -z "$CF_URL" ] && [ -f /tmp/cloudflare.log ]; then
    CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare.log 2>/dev/null | tail -1)
fi

# Check test log
if [ -z "$CF_URL" ] && [ -f /tmp/cloudflare_test.log ]; then
    CF_URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare_test.log 2>/dev/null | tail -1)
fi

if [ ! -z "$CF_URL" ]; then
    echo "$CF_URL"
    exit 0
else
    echo "No active tunnel URL found."
    echo "Run ./restart_cloudflare.sh to start a new tunnel."
    exit 1
fi
