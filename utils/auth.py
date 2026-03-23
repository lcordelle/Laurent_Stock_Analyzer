"""
In-app authentication for mobile compatibility.
Replaces ngrok Basic Auth (which fails on iOS Safari) with a Streamlit login form.
Credentials are loaded from .env (NGROK_AUTH_USER, NGROK_AUTH_PASS).
"""

import os
import streamlit as st
from pathlib import Path


def _load_env_credentials():
    """Load auth credentials from .env file."""
    env_path = Path(__file__).resolve().parent.parent / '.env'
    if not env_path.exists():
        return None, None
    
    user, pwd = None, None
    try:
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k == 'NGROK_AUTH_USER':
                        user = v
                    elif k == 'NGROK_AUTH_PASS':
                        pwd = v
    except Exception:
        pass
    return user, pwd


def require_auth():
    """
    Check authentication. If .env has credentials and user is not logged in,
    show login form and stop. Otherwise, allow access.
    """
    expected_user, expected_pass = _load_env_credentials()
    
    # No auth configured - allow access
    if not expected_user or not expected_pass:
        return
    
    # Already authenticated
    if st.session_state.get('authenticated', False):
        return
    
    # Show login form
    st.set_page_config(page_title="Login - Stock Analyzer", page_icon="🔐", layout="centered")
    st.markdown("## 📈 Stock Analyzer")
    st.markdown("Sign in to access the app")
    
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter username", autocomplete="username")
        password = st.text_input("Password", type="password", placeholder="Enter password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in")
    
    if submitted:
        if username == expected_user and password == expected_pass:
            st.session_state.authenticated = True
            st.success("Signed in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password")
    
    st.stop()
