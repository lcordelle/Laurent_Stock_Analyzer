# Resilient Service Supervision (launchd split) — Design Spec

**Date:** 2026-06-29
**Status:** Approved design, pending implementation plan

## Problem

The Stock Analyzer runs under ONE launchd job (`com.virtualfusion.stock-analyzer`) whose script
starts uvicorn as a backgrounded child guarded by a `curl /api/health` check, then `exec ngrok`.
Consequences (two production incidents on 2026-06-29):
- launchd supervises only ngrok (the exec'd process); **uvicorn is an unsupervised child** →
  `kickstart` races it and can leave :8001 down (outage).
- the `if ! healthy` guard means a stale/manual uvicorn **blocks new code from loading** on
  redeploy (kickstart skips restarting uvicorn).
Net: backend deploys are a fragile manual dance and restarts can drop the service.

## Solution: two independent KeepAlive jobs + a deploy script

### Job 1 — API (`com.virtualfusion.stock-analyzer.api`)
- Runs `run-api.sh` which: `ulimit -n 65536`, source `.env`, then **`exec python3 -m uvicorn
  api.main:app --host 127.0.0.1 --port 8001`** (exec → uvicorn IS the supervised process).
- `RunAtLoad` + `KeepAlive` true → auto-restarts if uvicorn dies. `LimitLoadToSessionType Aqua`,
  `EnvironmentVariables.PATH` (homebrew first), `SoftResourceLimits.NumberOfFiles 65536`.
  Logs → `logs/api.log` / `logs/api.err`.

### Job 2 — Tunnel (`com.virtualfusion.stock-analyzer.tunnel`)
- Runs `run-tunnel.sh` → **`exec ngrok http 8001 --url https://laurent.ngrok.io`**.
- `RunAtLoad` + `KeepAlive` true → auto-restarts independently. Same PATH env. Logs →
  `logs/tunnel.log` / `logs/tunnel.err`. (No inter-job ordering needed: ngrok returns 502 until
  uvicorn is up; both self-heal.)

### Deploy — `deploy.sh` (one reliable command)
1. `cd frontend && npm run build` (frontend is static-served → live immediately).
2. `launchctl kickstart -k gui/$(id -u)/com.virtualfusion.stock-analyzer.api` (clean uvicorn
   restart → new backend code loads deterministically; ngrok untouched).
3. Poll `:8001/api/health` until 200 (timeout → error). Print `laurent.ngrok.io/api/health` status.
4. Optional: verify a caller-supplied marker is live. Exit non-zero on failure.

### Manual fallback
`start-permanent.sh` is kept for ad-hoc manual all-in-one use, but is **no longer the launchd
entrypoint**. The two jobs are the supervised path.

## Migration (live cutover, with rollback)
Performed carefully on the live system (brief ~seconds downtime):
1. Write `run-api.sh`, `run-tunnel.sh`, the two `.plist` files, `deploy.sh`; `chmod +x` scripts;
   copy plists to `~/Library/LaunchAgents/`.
2. **Stop current service:** `launchctl bootout gui/$(id -u)/com.virtualfusion.stock-analyzer`
   (kills the old job + its ngrok); `kill` the manual uvicorn on :8001; confirm no ngrok holds
   :8001 / laurent.ngrok.io (avoid ngrok ERR_334).
3. **Bootstrap new jobs:** `launchctl bootstrap gui/$(id -u) <api.plist>` then `<tunnel.plist>`.
4. **Verify:** both jobs in `launchctl list` with a real PID (not just exit code); `:8001/api/health`
   200; `laurent.ngrok.io/api/health` 200; the new `action` field present in an analyze response.
5. **Finalize:** remove the OLD `~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist`
   so it doesn't reload at next login.
6. **Rollback (if any step 3–4 fails):** bootout the new jobs, restore by re-bootstrapping the old
   plist (kept until step 5) or running `./start-permanent.sh`; confirm :8001 + public back to 200.

## Constraints / safety
- Port 8001 stays the only app port; never bind 8000. Only ONE ngrok may hold laurent.ngrok.io —
  ensure the old one is dead before the tunnel job starts.
- Confirm any :8001 PID is THIS app before killing (MEDIC is :8502). Keep MEDIC's launchd job
  (`com.virtualfusion.medic`) untouched.
- Reuse the existing global ngrok auth/config (no secrets in repo).
- New files are additive and do not affect the running service until cutover.

## Testing / verification
- No unit tests (shell/launchd). Verification is operational, done live during migration (step 4)
  and re-runnable via `deploy.sh`:
  - `launchctl print gui/$(id -u)/com.virtualfusion.stock-analyzer.api` shows state=running, a PID.
  - kill the api job's uvicorn PID → confirm KeepAlive restarts it within seconds (supervision works).
  - `deploy.sh` after a trivial backend change → confirm the new code is live without manual steps.
- Update `CLAUDE.md` Run section + the `stock-analyzer-deploy-restart` memory to the new model.
