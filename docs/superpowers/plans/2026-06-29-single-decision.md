# Single-Source Decision Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collapse the Analysis page's four competing verdict surfaces into one authoritative action verdict, computed server-side from the single `/analyze` response and rendered once at the top.

**Architecture:** A pure `decide_action(grade, band, direction)` maps Quality×Setup to one action word; the route puts it on `Decision.action`. The frontend shows the action as the hero of the Decision panel and removes the VerdictBanner (separate fetch) and the chart-sidebar "Tech Signal" verdict card.

**Tech Stack:** Python (pure + pytest), FastAPI/Pydantic, React/TS.

## Global Constraints
- python3, py3.9-safe. NEVER bind/disturb :8001; use :8011 for tests.
- ONE fetch (`/analyze`) drives the page; no new endpoint. Keep backend `_compute_verdict` (alerts/opportunities use it).
- Action vocabulary + matrix exactly: STRONG BUY/BUY/ACCUMULATE/WATCH/SPECULATIVE/AVOID; Short→AVOID; Stand aside→WATCH; None→WATCH.
- Action color map: STRONG BUY/BUY `#00e676`, ACCUMULATE `#84cc16`, WATCH `#ffab00`, SPECULATIVE `#ff7043`, AVOID `#ff1744`.
- Commit only on `feature/single-decision`.

---

### Task 1: `decide_action` (pure) + tests

**Files:** Modify `utils/decision_engine.py`; Test `tests/test_decision_engine.py`

**Interfaces — Produces:** `decide_action(grade: Optional[str], band: Optional[str], direction: str) -> str`

- [ ] **Step 1: Write failing tests**

```python
# append to tests/test_decision_engine.py
from utils.decision_engine import decide_action


def test_decide_action_matrix():
    assert decide_action("A", "Prime", "Long") == "STRONG BUY"
    assert decide_action("B", "Strong", "Long") == "BUY"
    assert decide_action("A", "Fair", "Long") == "ACCUMULATE"
    assert decide_action("A", "Weak", "Long") == "WATCH"
    assert decide_action("C", "Strong", "Long") == "BUY"
    assert decide_action("C", "Fair", "Long") == "WATCH"
    assert decide_action("F", "Prime", "Long") == "SPECULATIVE"
    assert decide_action("D", "Weak", "Long") == "AVOID"


def test_decide_action_direction_and_missing():
    assert decide_action("A", "Prime", "Short") == "AVOID"
    assert decide_action("A", "Strong", "Stand aside") == "WATCH"
    assert decide_action(None, "Strong", "Long") == "WATCH"
    assert decide_action("A", None, "Long") == "WATCH"
```

- [ ] **Step 2: Run → fail** — `cd <root> && python3 -m pytest tests/test_decision_engine.py -k decide_action -v` → ImportError.

- [ ] **Step 3: Implement (append to `utils/decision_engine.py`)**

```python
def decide_action(grade: Optional[str], band: Optional[str], direction: str) -> str:
    if direction == "Short":
        return "AVOID"
    if direction == "Stand aside":
        return "WATCH"
    if grade is None or band is None:
        return "WATCH"
    if grade in ("A", "B"):
        if band == "Prime":
            return "STRONG BUY"
        if band == "Strong":
            return "BUY"
        if band == "Fair":
            return "ACCUMULATE"
        return "WATCH"
    if grade == "C":
        return "BUY" if band in ("Prime", "Strong") else "WATCH"
    return "SPECULATIVE" if band in ("Prime", "Strong") else "AVOID"
```

- [ ] **Step 4: Run → pass.** **Step 5: Commit** `git add utils/decision_engine.py tests/test_decision_engine.py && git commit -m "feat: decide_action verdict synthesis"`

---

### Task 2: `action` on Decision + route

**Files:** Modify `api/models/responses.py`, `api/routes/stocks.py`

- [ ] **Step 1: Add field.** In `api/models/responses.py`, the `Decision` model — add `action: str` (after `read: str`, or before; both required):

```python
class Decision(BaseModel):
    quality: Quality
    setup: Setup
    read: str
    action: str
```

- [ ] **Step 2: Route sets action.** In `api/routes/stocks.py`: add `decide_action` to the decision-engine import (`from utils.decision_engine import compute_conviction, quality_grade, read_line, decide_action`). Then in the `Decision(...)` constructor (currently `Decision(quality=quality, setup=setup, read=read_line(quality.grade, band, setup_raw["direction"]))`), add the action:

```python
        decision = Decision(
            quality=quality, setup=setup,
            read=read_line(quality.grade, band, setup_raw["direction"]),
            action=decide_action(quality.grade, band, setup_raw["direction"]),
        )
```

- [ ] **Step 3: Verify on :8011 (never 8001).**

```bash
cd <root> && python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8011 &
sleep 5
# login, then INTU:
curl -s -X POST http://127.0.0.1:8011/api/analyze -H "Content-Type: application/json" \
 -H "Authorization: Bearer $TOKEN" -d '{"ticker":"INTU","period":"1y"}' \
 | python3 -c "import sys,json;d=json.load(sys.stdin)['decision'];print('action',d['action'],'| grade',d['quality']['grade'],'| band',d['setup']['band'])"
kill %1
```
Expected: `action WATCH | grade A | band Weak`.

- [ ] **Step 4: Commit** `git add api/models/responses.py api/routes/stocks.py && git commit -m "feat: serve single action verdict on Decision"`

---

### Task 3: Frontend — hero action + remove competing surfaces

**Files:** Modify `frontend/src/lib/types.ts`, `frontend/src/components/stocks/DecisionPanel.tsx`, `frontend/src/pages/Analysis.tsx`

- [ ] **Step 1: Type.** In `frontend/src/lib/types.ts`, the `Decision` interface — add `action: string`:

```ts
export interface Decision { quality: Quality; setup: Setup; read: string; action: string }
```

- [ ] **Step 2: Hero action in DecisionPanel.** In `frontend/src/components/stocks/DecisionPanel.tsx`:
  - Add an action color map near the other maps:
    ```ts
    const ACTION_COLOR: Record<string, string> = { 'STRONG BUY': '#00e676', BUY: '#00e676', ACCUMULATE: '#84cc16', WATCH: '#ffab00', SPECULATIVE: '#ff7043', AVOID: '#ff1744' }
    ```
  - Destructure `action` from `decision` (`const { quality, setup, read, action } = decision`).
  - Replace the small "Decision" label header (the `<span ...>Decision</span>`) with a hero row: the big action word + the `read` instruction beside it:
    ```tsx
    <div className="flex items-start gap-3 flex-wrap">
      <span className="text-2xl font-black px-3 py-1 rounded-lg" style={{ backgroundColor: (ACTION_COLOR[action] ?? '#94a3b8') + '22', color: ACTION_COLOR[action] ?? '#94a3b8' }}>{action}</span>
      <span className="text-sm flex-1 min-w-[12rem]" style={{ color: '#cbd5e1' }}>{read}</span>
    </div>
    ```
  - Remove the now-redundant standalone "Read" block lower down (the `▸ {read}` row), since `read` is now beside the action. Keep the two axes, drivers, regime, EV, sizing.

- [ ] **Step 3: Remove VerdictBanner.** In `frontend/src/pages/Analysis.tsx`: delete the import line `import VerdictBanner from '../components/stocks/VerdictBanner'` and the usage line `{ticker && <VerdictBanner ticker={ticker} period={period} />}`.

- [ ] **Step 4: Remove the sidebar "Verdict card".** In `frontend/src/pages/Analysis.tsx`, delete the entire `{/* Verdict card */}` block — the `<div className="rounded-xl border p-4 flex flex-col gap-3" style={{ ... borderColor: `${sc}25` }}>` … through its matching closing `</div>` (it contains the "Tech Signal" `{signal}`, the VF Score, `{tier}`, signal_quality/confidence, AI Forecast, `{whyNow}`, and drivers chips). Read the exact span first to delete cleanly; the sibling "Trade Setup" card BELOW it (entry/SL/TP/RSI/S-R) stays untouched. After removal, if `computeTier`/`computeWhyNow`/`tier`/`whyNow`/`sc`/`drivers` become unused, remove those now-dead locals/helpers to keep `tsc` (noUnusedLocals) green — but KEEP any that the surviving Trade Setup card still uses (verify by build).

- [ ] **Step 5: Build.** `cd <root>/frontend && npm install && npm run build` → passes, 0 TS errors. Fix any unused-symbol errors from Step 4 by removing the dead code.

- [ ] **Step 6: Commit** `git add frontend/src/lib/types.ts frontend/src/components/stocks/DecisionPanel.tsx frontend/src/pages/Analysis.tsx && git commit -m "feat: single action verdict hero; remove VerdictBanner + sidebar verdict"`

---

## Self-Review

**Spec coverage:** decide_action matrix + Short/Stand-aside/None (T1); action on Decision + route (T2); hero action + read (T3 S2); remove VerdictBanner (T3 S3) + sidebar verdict (T3 S4); keep trade levels (T3 S4 leaves Trade Setup card); single fetch (no new endpoint; VerdictBanner's separate fetch removed); action colors (T3 S2). ✓

**Placeholder scan:** none — Step 4 explicitly says read the exact span before deleting and to clean resulting dead locals via the build.

**Type consistency:** `decide_action(grade,band,direction)->str` ↔ route call uses `quality.grade, band, setup_raw["direction"]` ↔ `Decision.action: str` (py) ↔ `Decision.action: string` (ts) ↔ panel `ACTION_COLOR[action]`. `read`/`quality`/`setup` unchanged from the prior shape. ✓
