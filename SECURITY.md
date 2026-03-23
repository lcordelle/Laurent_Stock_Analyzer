# Security Guide — VirtualFusion Stock Analyzer

How to keep your computer and data safe when using the ngrok tunnel.

---

## Quick Setup (Required for remote access)

**Before using the tunnel**, create a `.env` file with login credentials:

```bash
cp .env.example .env
# Edit .env and set:
# NGROK_AUTH_USER=your_username
# NGROK_AUTH_PASS=your_secure_password_min_8_chars
```

**Password rules:** 8–128 characters. Use a strong, unique password.

---

## Security Layers

| Layer | Protection |
|-------|------------|
| **In-app login** | Only users with your username/password can access the app. Credentials checked against `.env`. Works on mobile. |
| **Localhost binding** | Streamlit listens on `127.0.0.1` only. Your app is not reachable from the network; only ngrok (on the same machine) can connect. |
| **No hardcoded secrets** | API keys live in `.env` (gitignored). Never commit credentials. |
| **File upload limits** | Max 10MB for portfolio CSV/Excel uploads. Reduces abuse risk. |
| **Error details hidden** | Stack traces are not shown to users, limiting information leakage. |

---

## In-App Login (Mobile-Friendly)

We use in-app login because iOS Safari blocks Basic Auth. When you visit the URL from any device, you see a Sign in form. Enter your username and password from `.env`, then use the door icon in the nav bar to sign out. Works on all browsers including iOS Safari.


---

## Best Practices

1. **Keep `.env` private** — It’s in `.gitignore`. Never share it or commit it.
2. **Use a strong password** — At least 12 characters, mix of letters, numbers, symbols.
3. **Rotate credentials** — Change `NGROK_AUTH_PASS` periodically.
4. **Stop when not in use** — Close the tunnel when you’re done to reduce exposure.
5. **Mac sleep** — Sleep drops the tunnel. Use `caffeinate -d` or prevent sleep when plugged in.

---

## API Keys (Optional)

If you use Alpha Vantage, add to `.env`:

```
ALPHA_VANTAGE_API_KEY=your_key_here
```

Get a free key at [alphavantage.co](https://www.alphavantage.co/support/#api-key). The app works without it (Yahoo Finance is the default).

---

## If You Suspect Compromise

1. **Stop the tunnel** — Close the terminal or run `launchctl stop com.virtualfusion.stock-analyzer`
2. **Change credentials** — Update `NGROK_AUTH_USER` and `NGROK_AUTH_PASS` in `.env`
3. **Rotate API keys** — If you use Alpha Vantage, generate a new key
4. **Check ngrok dashboard** — Visit [dashboard.ngrok.com](https://dashboard.ngrok.com) to review tunnel traffic

---

## Technical Details

- **Streamlit:** Binds to `127.0.0.1:8501` — not reachable from the network
- **ngrok:** Connects to `localhost:8501` and forwards to the app (in-app login handles auth)
- **Attack surface:** Reduced by binding to localhost and requiring authentication at the tunnel
