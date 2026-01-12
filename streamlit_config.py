"""
Streamlit configuration helper for Render deployment
Ensures proper port binding
"""
import os
import sys

# Get port from environment (Render sets this)
port = os.environ.get('PORT', '10000')

# Ensure port is set for Streamlit
os.environ['STREAMLIT_SERVER_PORT'] = str(port)

# Print for debugging
print(f"Starting Streamlit on port: {port}", file=sys.stderr)

