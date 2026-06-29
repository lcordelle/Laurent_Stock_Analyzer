# Resilient Service Supervision (launchd split) Implementation Plan

> **For agentic workers:** Execute inline (live infra — do NOT delegate to subagents). Steps use checkbox (`- [ ]`) tracking.

**Goal:** Replace the single fragile launchd job with two independent KeepAlive jobs (API + tunnel) and a one-command `deploy.sh`, so backend deploys reload deterministically and a crash of either process self-heals.

**Architecture:** `…stock-analyzer.api` execs uvicorn on :8001 (supervised, KeepAlive); `…stock-analyzer.tunnel` execs ngrok (supervised, KeepAlive). `deploy.sh` rebuilds the frontend and `kickstart`s only the API job. Live migration with a tested rollback.

**Tech Stack:** macOS launchd (plist), bash, uvicorn, ngrok.

## Global Constraints
- :8001 is the only app port; never 8000. Only ONE ngrok may hold `laurent.ngrok.io`.
- Confirm any :8001 PID is THIS app before killing (MEDIC is :8502); never touch `com.virtualfusion.medic`.
- New files are additive — they do NOT affect the running service until the cutover (Task 2).
- Keep `start-permanent.sh` as a manual fallback. Reuse global ngrok auth.
- `$(id -u)` is 501 on this machine; scripts use `$(id -u)` dynamically.

---

### Task 1: Create the artifact files (no prod impact)

**Files:** Create `run-api.sh`, `run-tunnel.sh`, `com.virtualfusion.stock-analyzer.api.plist`, `com.virtualfusion.stock-analyzer.tunnel.plist`, `deploy.sh`.

- [ ] **Step 1: Branch.** `cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer && git checkout -b feature/launchd-split`

- [ ] **Step 2: `run-api.sh`**

```bash
#!/bin/bash
# Supervised by launchd job com.virtualfusion.stock-analyzer.api — execs uvicorn (so launchd supervises it directly).
set -e
ulimit -n 65536 2>/dev/null || true
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"
[[ -f .env ]] && { set -a; source .env; set +a; }
export PYTHONUNBUFFERED=1
exec python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8001
```

- [ ] **Step 3: `run-tunnel.sh`**

```bash
#!/bin/bash
# Supervised by launchd job com.virtualfusion.stock-analyzer.tunnel — execs ngrok (so launchd supervises it directly).
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"
exec ngrok http 8001 --url "https://laurent.ngrok.io"
```

- [ ] **Step 4: `com.virtualfusion.stock-analyzer.api.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.virtualfusion.stock-analyzer.api</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer &amp;&amp; exec ./run-api.sh</string>
  </array>
  <key>WorkingDirectory</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>LimitLoadToSessionType</key><string>Aqua</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>SoftResourceLimits</key><dict><key>NumberOfFiles</key><integer>65536</integer></dict>
  <key>HardResourceLimits</key><dict><key>NumberOfFiles</key><integer>65536</integer></dict>
  <key>StandardOutPath</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/logs/api.log</string>
  <key>StandardErrorPath</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/logs/api.err</string>
</dict>
</plist>
```

- [ ] **Step 5: `com.virtualfusion.stock-analyzer.tunnel.plist`**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.virtualfusion.stock-analyzer.tunnel</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>cd /Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer &amp;&amp; exec ./run-tunnel.sh</string>
  </array>
  <key>WorkingDirectory</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer</string>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>LimitLoadToSessionType</key><string>Aqua</string>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>StandardOutPath</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/logs/tunnel.log</string>
  <key>StandardErrorPath</key><string>/Users/laurentcordelle/Projects/VirtualFusion_Stock_Analyzer/logs/tunnel.err</string>
</dict>
</plist>
```

- [ ] **Step 6: `deploy.sh`**

```bash
#!/bin/bash
# One-command deploy: rebuild frontend + cleanly reload the API job (deterministic backend code load).
set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"; cd "$PROJECT_ROOT"
echo "[deploy] building frontend..."; ( cd frontend && npm run build )
echo "[deploy] reloading API job (uvicorn)..."
launchctl kickstart -k "gui/$(id -u)/com.virtualfusion.stock-analyzer.api"
echo "[deploy] waiting for :8001 health..."
for i in $(seq 1 20); do
  sleep 1
  if curl -sf --max-time 3 -o /dev/null http://127.0.0.1:8001/api/health 2>/dev/null; then echo "[deploy] :8001 healthy"; break; fi
  [ "$i" -eq 20 ] && { echo "[deploy] ERROR: :8001 not healthy after 20s — check logs/api.err"; exit 1; }
done
code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 12 https://laurent.ngrok.io/api/health || echo ERR)
echo "[deploy] public laurent.ngrok.io/api/health -> $code"
echo "[deploy] done."
```

- [ ] **Step 7: chmod + commit.**

```bash
chmod +x run-api.sh run-tunnel.sh deploy.sh
git add run-api.sh run-tunnel.sh deploy.sh com.virtualfusion.stock-analyzer.api.plist com.virtualfusion.stock-analyzer.tunnel.plist docs/superpowers/specs/2026-06-29-launchd-split-design.md docs/superpowers/plans/2026-06-29-launchd-split.md
git commit -m "feat: split service into supervised api + tunnel launchd jobs; add deploy.sh"
```

---

### Task 2: Live cutover (with rollback)

**Files:** none (operational: `~/Library/LaunchAgents/`, launchctl).

- [ ] **Step 1: Pre-flight — capture current state for rollback.**
```bash
launchctl list | grep stock-analyzer
lsof -nP -iTCP:8001 -sTCP:LISTEN -t   # note the current uvicorn PID
pgrep -fl "ngrok http 8001"
# confirm the OLD plist still exists (rollback source):
ls -l ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist
```

- [ ] **Step 2: Install new plists.**
```bash
cp com.virtualfusion.stock-analyzer.api.plist com.virtualfusion.stock-analyzer.tunnel.plist ~/Library/LaunchAgents/
```

- [ ] **Step 3: Stop the current service (brief downtime starts).**
```bash
launchctl bootout "gui/$(id -u)/com.virtualfusion.stock-analyzer" 2>/dev/null || true
# kill any manual/stale uvicorn on :8001 (confirm it's this app first):
P=$(lsof -nP -iTCP:8001 -sTCP:LISTEN -t | head -1); [ -n "$P" ] && ps -o command= -p "$P" | grep -q "uvicorn api.main:app" && kill "$P"
# ensure no ngrok holds the endpoint (avoid ERR_NGROK_334):
pkill -f "ngrok http 8001" 2>/dev/null || true
sleep 2
lsof -nP -iTCP:8001 -sTCP:LISTEN -t || echo ":8001 clear"
```

- [ ] **Step 4: Bootstrap the two new jobs.**
```bash
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.api.plist
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.tunnel.plist
```

- [ ] **Step 5: Verify (downtime ends).**
```bash
for i in $(seq 1 15); do sleep 2; curl -sf --max-time 3 -o /dev/null http://127.0.0.1:8001/api/health && { echo "api up after ~$((i*2))s"; break; }; done
launchctl list | grep stock-analyzer            # both .api and .tunnel present with a real PID
lsof -nP -iTCP:8001 -sTCP:LISTEN -t | xargs -I{} ps -o pid=,command= -p {} | cut -c1-60
curl -s -o /dev/null -w "public %{http_code}\n" --max-time 12 https://laurent.ngrok.io/api/health
# new-code marker (action field present):
# login + analyze INTU; expect decision.action present
```
Expected: api job running (uvicorn on :8001), tunnel job running (ngrok), :8001 + public both 200, `action` present.

- [ ] **Step 6: Finalize — retire the old job's plist.**
```bash
rm ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist
```

- [ ] **Step 7 (ONLY if Step 4–5 failed): Rollback.**
```bash
launchctl bootout "gui/$(id -u)/com.virtualfusion.stock-analyzer.api" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.virtualfusion.stock-analyzer.tunnel" 2>/dev/null || true
rm -f ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.api.plist ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.tunnel.plist
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.virtualfusion.stock-analyzer.plist  # old job back
# or, if needed: ./start-permanent.sh
# verify :8001 + public back to 200.
```

- [ ] **Step 8: Supervision smoke test (prove KeepAlive works).**
```bash
P=$(lsof -nP -iTCP:8001 -sTCP:LISTEN -t | head -1); echo "killing api uvicorn $P"; kill "$P"; sleep 5
curl -sf -o /dev/null -w "after-kill :8001 %{http_code}\n" http://127.0.0.1:8001/api/health   # expect 200 (KeepAlive restarted it)
```

---

### Task 3: Docs

**Files:** Modify `CLAUDE.md`; update memory `stock-analyzer-deploy-restart`.

- [ ] **Step 1: CLAUDE.md Run section** — replace the launchd description: backend deploy is now `./deploy.sh` (rebuild + `kickstart -k …stock-analyzer.api`); the service is two KeepAlive jobs (`.api` on :8001, `.tunnel` ngrok); `start-permanent.sh` is a manual fallback only. Commit.

- [ ] **Step 2: Memory** — rewrite `stock-analyzer-deploy-restart` to the new model: deploy via `./deploy.sh`; restart api job with `launchctl kickstart -k gui/$(id -u)/com.virtualfusion.stock-analyzer.api`; jobs are independently supervised; the old single-job races/skip-guard no longer apply.

---

## Self-Review

**Spec coverage:** api job execs uvicorn supervised (T1 S2,S4); tunnel job execs ngrok supervised (T1 S3,S5); deploy.sh rebuild+kickstart+verify (T1 S6); migration stop/bootstrap/verify/finalize/rollback (T2 S1–S7); ngrok single-endpoint + PID-confirm safety (T2 S3); KeepAlive supervision proof (T2 S8); docs+memory (T3); manual fallback kept (start-permanent.sh untouched). ✓

**Placeholder scan:** none — full file contents + exact commands.

**Consistency:** job labels `com.virtualfusion.stock-analyzer.api` / `.tunnel` used identically across plists, deploy.sh, migration, and rollback; paths absolute and consistent; `$(id -u)` used for launchctl domain throughout.
