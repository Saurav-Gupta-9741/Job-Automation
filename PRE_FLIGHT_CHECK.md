# Career OS - Pre-Flight Checklist

## Before Testing on LinkedIn Easy Apply

Run through this checklist to ensure all systems are operational.

---

## ✅ Backend Health Check

### 1. Start Backend
```bash
cd services/ml-core
.venv\Scripts\activate
python -m app.main
```

**Expected:** Server starts on `http://127.0.0.1:8000`

### 2. Verify Health Endpoint
```bash
curl http://127.0.0.1:8000/health
```

**Expected Response:**
```json
{
  "ok": true,
  "tokens_spent_60s": 0,
  "tpm_budget": 5000,
  "circuit_open": false
}
```

### 3. Check Database Tables
```bash
cd services/ml-core/app/data
sqlite3 career_os.db

.tables
# Should show: applications field_memory stage_counts state_transitions telemetry_events session_metrics

.schema applications
# Should show all required columns

.quit
```

### 4. Verify Profile Loaded
```bash
curl http://127.0.0.1:8000/api/profile
```

**Check:** Returns profile data (even if default/empty)

### 5. Test Stats Endpoint
```bash
curl http://127.0.0.1:8000/api/stats?days=7
```

**Expected:** Returns telemetry stats (may be zeros initially)

---

## ✅ Extension Health Check

### 1. Load Extension
1. Chrome → `chrome://extensions`
2. Enable "Developer mode" (top-right toggle)
3. Click "Load unpacked"
4. Select `apps/extension/` folder
5. Verify "Career OS" appears in list

### 2. Check Extension Errors
- Click "Errors" button on Career OS extension card
- **Expected:** No errors listed

### 3. Verify Background Script
- Click "Service worker" link (or "background page")
- Console should open
- **Expected:** No errors in console

### 4. Test Content Script Injection
1. Open any website (e.g., google.com)
2. Open Developer Tools (F12)
3. Go to Console tab
4. Type: `window.COS`
5. **Expected:** Object with {CONFIG, Scanner, Executor, State, Widget, ...}

---

## ✅ Widget Functionality Check

### 1. Navigate to LinkedIn
```
https://www.linkedin.com/jobs/
```

### 2. Verify Widget Appears
- Look for "Career OS" widget in bottom-right corner
- **Expected:** Widget visible with "Apply on this page" button

### 3. Check Widget Controls
- [ ] Minimize button (–) works
- [ ] Widget expands/collapses
- [ ] Status shows "Idle"

### 4. Test Backend Communication
1. Open Developer Tools Console
2. Click "Apply on this page" button
3. Check console for errors
4. Check widget status updates
5. Click "Stop" button

**Expected:** No "backend error" messages

---

## ✅ Scanner Functionality Check

### 1. Open LinkedIn Job Page
```
https://www.linkedin.com/jobs/search/?keywords=software%20engineer
```

### 2. Click Any Job Card
- Job details should appear on right side

### 3. Test Scanner in Console
```javascript
// In Developer Tools Console
const elements = window.COS.Scanner.scan();
console.log('Scanned elements:', elements.length);
console.table(elements.slice(0, 10));
```

**Expected:**
- Returns array of 20-80 elements
- Elements have properties: id, tag, type, text, etc.

### 4. Verify Easy Apply Button Detected
```javascript
const buttons = elements.filter(e => e.tag === 'button');
const easyApply = buttons.find(e => e.text?.toLowerCase().includes('easy apply'));
console.log('Easy Apply button:', easyApply);
```

**Expected:** Easy Apply button found (if job has it)

### 5. Test Signature Stability
```javascript
const sig1 = window.COS.Scanner.scan()[0]?.signature;
// Wait 2 seconds
setTimeout(() => {
  const sig2 = window.COS.Scanner.scan()[0]?.signature;
  console.log('Signatures match:', sig1 === sig2);
}, 2000);
```

**Expected:** `Signatures match: true`

---

## ✅ State Management Check

### 1. Test Session Creation
```javascript
await window.COS.State.start('apply');
console.log('Session:', window.COS.State.session);
```

**Expected:** Session object with id, running: true, etc.

### 2. Verify Persistence
```javascript
await window.COS.State.save();
// Refresh page (Ctrl+R)
// After page loads:
await window.COS.State.load();
console.log('Loaded session:', window.COS.State.session);
```

**Expected:** Session persists across refresh

### 3. Test Stop
```javascript
await window.COS.State.stop();
console.log('Is running:', window.COS.State.isRunning());
```

**Expected:** `Is running: false`

---

## ✅ Executor Functionality Check

### 1. Test Click Action
```javascript
const testAction = {
  type: 'click',
  target_id: elements.find(e => e.tag === 'button')?.id
};
const result = await window.COS.Executor.runAction(testAction);
console.log('Click result:', result);
```

**Expected:** `{ ok: true }` (and button was clicked)

### 2. Test Type Action
```javascript
const input = elements.find(e => e.tag === 'input' && e.type === 'text');
if (input) {
  const result = await window.COS.Executor.runAction({
    type: 'type',
    target_id: input.id,
    value: 'test value'
  });
  console.log('Type result:', result);
  console.log('Input value:', document.querySelector(`[data-cos-sig="${input.signature}"]`).value);
}
```

**Expected:** Value appears in input field

---

## ✅ Backend Integration Check

### 1. Test Step Endpoint
```bash
curl -X POST http://127.0.0.1:8000/api/agent/step \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "url": "https://linkedin.com/jobs/test",
    "title": "Test Job",
    "elements": [],
    "total_elements": 0,
    "stage_hash": "test",
    "objective": "apply"
  }'
```

**Expected:** Returns JSON with `script` array

### 2. Test Resume Endpoint
```bash
curl http://127.0.0.1:8000/api/resume
```

**Expected:** 
- Returns JSON with `base64` field if resume staged
- OR returns 404 with helpful message if no resume

---

## ✅ Critical Fixes Verification

### 1. Verify Iframe Support
```javascript
// On a page with iframe
const roots = [];
function collectRoots(root, acc) {
  acc.push(root);
  if (root.querySelectorAll) {
    const iframes = root.querySelectorAll('iframe');
    console.log('Found iframes:', iframes.length);
  }
}
collectRoots(document, roots);
console.log('Total roots (including iframes):', roots.length);
```

**Expected:** Detects iframes if present

### 2. Verify Shadow DOM Support
```javascript
// On a page with shadow DOM
const hasShadow = Array.from(document.querySelectorAll('*'))
  .some(el => el.shadowRoot);
console.log('Page has shadow DOM:', hasShadow);
```

**Expected:** True on pages with web components

### 3. Verify Rate Limit Detection
```javascript
// Simulate rate limit message
const testElements = [{
  id: 'test1',
  tag: 'div',
  text: "You're applying too fast. Please slow down.",
  type: null
}];
// Check if blocker is detected in backend
```

**Expected:** Detected as rate_limit blocker

### 4. Verify Already Applied Detection
```javascript
// On a job you already applied to
const elements = window.COS.Scanner.scan();
const alreadyApplied = elements.some(e => 
  e.text?.toLowerCase().includes('you applied') ||
  e.text?.toLowerCase().includes('application submitted')
);
console.log('Already applied detected:', alreadyApplied);
```

**Expected:** True if job was applied to

---

## ✅ Telemetry Check

### 1. Start a Test Session
```javascript
await window.COS.State.start('apply');
// Perform some actions
// Stop session
await window.COS.State.stop();
```

### 2. Verify Events Recorded
```bash
cd services/ml-core/app/data
sqlite3 career_os.db

SELECT COUNT(*) FROM telemetry_events;
SELECT COUNT(*) FROM session_metrics;

.quit
```

**Expected:** Counts > 0

### 3. Check Stats API
```bash
curl http://127.0.0.1:8000/api/stats?days=1
```

**Expected:** Updated statistics

---

## ✅ Error Handling Check

### 1. Test Backend Offline Recovery
1. Stop backend (Ctrl+C)
2. Click "Apply on this page" on LinkedIn
3. Observe error message and retry counter
4. Start backend again
5. Verify auto-recovery

**Expected:** 
- Widget shows "Backend error (1/5)"
- Retries with exponential backoff
- Recovers when backend starts

### 2. Test Stale Element Recovery
```javascript
// Get an element
const btn = document.querySelector('button');
const sig = btn.getAttribute('data-cos-sig');

// Remove it
btn.remove();

// Try to click via executor
const result = await window.COS.Executor.runAction({
  type: 'click',
  target_id: sig
});
console.log('Stale element result:', result);
```

**Expected:** Retries and handles gracefully

---

## ✅ Configuration Check

### 1. Verify Environment Variables
```bash
cd services/ml-core
cat .env
```

**Required:**
- `GROQ_API_KEY` is set
- `GROQ_MODEL` is set (or defaults to llama-3.1-8b-instant)

### 2. Verify Frontend Config
```javascript
console.log('Config:', window.COS.CONFIG);
```

**Check:**
- `BULK_APPLY_ENABLED` is true/false as desired
- `MIN_ACTION_DELAY_MS` is reasonable (700-1000ms)
- `MAX_ELEMENTS` is 80

---

## ✅ Final Sanity Checks

### Before Going Live

- [ ] Backend health returns `ok: true`
- [ ] Extension loads without errors
- [ ] Widget appears on LinkedIn
- [ ] Scanner detects Easy Apply button
- [ ] State persists across page refresh
- [ ] Backend communication works
- [ ] Telemetry recording works
- [ ] Error recovery tested
- [ ] Profile data loaded
- [ ] Resume available (if using upload)

### Known Limitations to Note

- ⚠️ Cross-origin iframes won't be scanned (expected)
- ⚠️ Closed shadow DOM won't be accessible (expected)
- ⚠️ Some custom dropzones may need manual intervention
- ⚠️ Rate limits from LinkedIn require wait time

---

## 🚨 Red Flags - DO NOT PROCEED

- ❌ Backend health returns error
- ❌ Extension shows errors in console
- ❌ Widget doesn't appear on LinkedIn
- ❌ Scanner returns empty array on job pages
- ❌ State doesn't persist across refresh
- ❌ Backend returns 500 errors
- ❌ Database tables missing
- ❌ GROQ_API_KEY not configured

---

## ✅ Ready for LinkedIn Testing

Once all checks pass, proceed to:
1. Find an Easy Apply job (preferably one you don't care about)
2. Have `REVIEW_BEFORE_SUBMIT=true` for safety
3. Monitor both browser console and backend terminal
4. Start with widget "Apply on this page"
5. Observe each step carefully
6. Be ready to click "Stop" if anything looks wrong

---

## 📊 Post-Test Analysis

After completing 1-2 test applications, check:

```bash
# View telemetry
curl http://127.0.0.1:8000/api/stats?days=1

# View applications
curl http://127.0.0.1:8000/api/applications

# Check database
cd services/ml-core/app/data
sqlite3 career_os.db
SELECT * FROM session_metrics ORDER BY updated_at DESC LIMIT 5;
.quit
```

**Success Criteria:**
- Application completed or reached expected handoff
- No crash/freeze
- Telemetry data recorded
- Clear error messages if any failures
- Loop detection worked if needed
- Confidence scores reasonable

---

**Ready to test!** 🚀
