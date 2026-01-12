#!/bin/bash
# Startup script for Render deployment

# Get port from environment variable (Render sets this)
PORT=${PORT:-10000}

# Debug: Print port
echo "Starting Streamlit on port: $PORT" >&2

# Export port for Streamlit
export PORT

# Run Streamlit with explicit port binding
# Use exec to ensure proper signal handling
exec streamlit run main.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false

