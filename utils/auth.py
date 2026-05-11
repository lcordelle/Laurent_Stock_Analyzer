"""
In-app authentication for mobile compatibility.
Credentials: .env (APP_AUTH_* or legacy NGROK_AUTH_*), or environment variables.
If unset, defaults to laurent / changeme — override in production via .env.
"""

import os
import streamlit as st
from pathlib import Path

# Defaults when nothing is configured (change via .env)
_DEFAULT_USER = "laurent"
_DEFAULT_PASS = "changeme"


def _parse_env_file(path: Path) -> dict:
    out = {}
    if not path.exists():
        return out
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def _auth_disabled() -> bool:
    """Set APP_AUTH_DISABLED=true in .env to skip login (local dev / trusted networks only)."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    file_vals = _parse_env_file(env_path)
    v = file_vals.get("APP_AUTH_DISABLED") or os.environ.get("APP_AUTH_DISABLED", "")
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def _load_env_credentials():
    """
    Returns (username, password, using_defaults: bool).
    Priority: APP_AUTH_* pair, then NGROK_AUTH_* pair (legacy), then os.environ, then defaults.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    file_vals = _parse_env_file(env_path)

    def getv(key: str) -> str:
        v = file_vals.get(key) or os.environ.get(key)
        if v is None:
            return ""
        return str(v).strip()

    for ku, kp in (
        ("APP_AUTH_USER", "APP_AUTH_PASS"),
        ("NGROK_AUTH_USER", "NGROK_AUTH_PASS"),
    ):
        u, p = getv(ku), getv(kp)
        if u and p:
            return u, p, False

    return _DEFAULT_USER, _DEFAULT_PASS, True


def require_auth():
    """
    Require sign-in unless APP_AUTH_DISABLED=true in .env (or env).
    Otherwise defaults apply if .env has no credential pair.
    """
    if _auth_disabled():
        return

    expected_user, expected_pass, using_defaults = _load_env_credentials()

    if st.session_state.get("authenticated", False):
        if using_defaults and not st.session_state.get("_auth_default_warned"):
            st.session_state._auth_default_warned = True
            st.sidebar.warning(
                "Using default login (laurent / changeme). Set **APP_AUTH_USER** and "
                "**APP_AUTH_PASS** in `.env` for production."
            )
        return

    st.set_page_config(page_title="Login - Stock Analyzer", page_icon="🔐", layout="centered")
    st.markdown("## 📈 Laurent Stock Analyzer")
    st.caption("Sign in to continue")

    if using_defaults:
        st.info(
            "Using built-in credentials until you set a pair in `.env`. "
            "Copy `.env.example` to `.env` and set **APP_AUTH_USER** and **APP_AUTH_PASS**."
        )

    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Username", autocomplete="username")
        password = st.text_input("Password", type="password", placeholder="Password", autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary")

    if submitted:
        if username == expected_user and password == expected_pass:
            st.session_state.authenticated = True
            st.session_state._auth_default_warned = False
            st.success("Signed in.")
            st.rerun()
        else:
            st.error("Invalid username or password")

    st.stop()
