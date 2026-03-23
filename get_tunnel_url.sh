#!/bin/bash
# Quick script to get the current Cloudflare tunnel URL

if [ -f /tmp/cloudflare.log ]; then
    URL=$(grep -o 'https://[^ ]*\.trycloudflare\.com' /tmp/cloudflare.log 2>/dev/null | tail -1)
    if [ ! -z "$URL" ]; then
        echo "Current Tunnel URL:"
        echo "$URL"
    else
        echo "No active tunnel URL found. Run start_with_cloudflare.sh to start a new tunnel."
    fi
else
    echo "No tunnel log found. Run start_with_cloudflare.sh to start a new tunnel."
fi
