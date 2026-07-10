# Troubleshooting Flowchart

## Decision Tree for Diagnosing Career OS Issues

---

## 🎯 Quick Diagnosis

Start here based on your symptom:

1. **Backend won't start** → [Section A](#section-a-backend-wont-start)
2. **Extension won't load** → [Section B](#section-b-extension-wont-load)
3. **Widget not visible** → [Section C](#section-c-widget-not-visible)
4. **Application gets stuck** → [Section D](#section-d-application-gets-stuck)
5. **Fields not filling** → [Section E](#section-e-fields-not-filling)
6. **Backend errors** → [Section F](#section-f-backend-errors)
7. **Slow performance** → [Section G](#section-g-slow-performance)
8. **Submission fails** → [Section H](#section-h-submission-fails)

---

## Section A: Backend Won't Start

### Symptom: `python -m app.main` fails or crashes

```
START
  ↓
Is Python installed?
  ├─ NO → Install Python 3.8+ from python.org
  ↓      Then retry
  YES
  ↓
Check Python version: python --version
  ↓
Is version 3.8 or higher?
  ├─ NO → Upgrade Python
  ↓      Then retry
  YES
  ↓
Is virtual environment activated?
  ├─ NO → cd services\ml-core
  │       .venv\Scripts\activate.bat
  ↓      Then retry
  YES
  ↓
Are dependencies installed?
  ├─ NO → pip install -r requirements.txt
  ↓      Then retry
  YES
  ↓
Does .env file exist?
  ├─ NO → copy .env.example .env
  ↓      Add GROQ_API_KEY
  ↓      Then retry
  YES
  ↓
Is GROQ_API_KEY set in .env?
  ├─ NO → Get key from console.groq.com
  │       Add to .env
  ↓      Then retry
  YES
  ↓
Is port 8000 already in use?
  ├─ YES → netstat -ano | findstr :8000
  │       Kill process or change port
  ↓      Then retry
  NO
  ↓
Check error message in terminal
  ↓
Common errors:
  • "ModuleNotFoundError" → pip install [module]
  • "PermissionError" → Run as admin
  • "Port already in use" → Change port or kill process
  • "Invalid API key" → Check GROQ_API_KEY
```


**Quick Fix Commands:**
```bash
# Reinstall dependencies
cd services\ml-core
.venv\Scripts\activate
pip install --upgrade -r requirements.txt

# Check port usage
netstat -ano | findstr :8000

# Test backend manually
python -m app.main
```

---

## Section B: Extension Won't Load

### Symptom: Extension shows errors in chrome://extensions

```
START
  ↓
Go to chrome://extensions
  ↓
Is Developer mode enabled?
  ├─ NO → Enable toggle (top-right)
  ↓      Then click "Load unpacked"
  YES
  ↓
Do extension files exist?
  ├─ NO → Verify apps/extension/ folder exists
  │       Check all files present
  ↓      Then retry
  YES
  ↓
Click "Load unpacked"
  ↓
Select apps/extension/ folder
  ↓
Does extension appear in list?
  ├─ NO → Check for errors in console
  ↓      Click "Pack extension" errors
  YES
  ↓
Is there an "Errors" button?
  ├─ YES → Click "Errors"
  │       Read error message
  ↓      ↓
  │      Common errors:
  │      • "manifest.json not found" → Wrong folder selected
  │      • "Unexpected token" → JSON syntax error
  │      • "Cannot load extension" → File permissions
  ↓
  NO (extension loaded successfully)
  ↓
Test in console: window.COS
  ↓
Returns object?
  ├─ NO → Reload extension
  │       Hard refresh page (Ctrl+Shift+R)
  ↓
  YES
  ↓
SUCCESS ✓
```

**Quick Fix Commands:**
```bash
# Verify extension files
dir apps\extension\manifest.json
dir apps\extension\background.js
dir apps\extension\content\

# Check manifest syntax
python -m json.tool apps\extension\manifest.json
```

---

## Section C: Widget Not Visible

### Symptom: No Career OS widget on LinkedIn job pages

```
START
  ↓
Is extension loaded in Chrome?
  ├─ NO → See Section B
  ↓
  YES
  ↓
Are you on a LinkedIn job page?
  ├─ NO → Go to linkedin.com/jobs
  │       Click any job
  ↓
  YES
  ↓
Open DevTools (F12) → Console
  ↓
Type: window.COS
  ↓
Is COS object present?
  ├─ NO → Extension not running
  │       Reload extension
  │       Hard refresh page
  ↓
  YES
  ↓
Check for JavaScript errors in console
  ↓
Any red errors?
  ├─ YES → Read error message
  │       Common errors:
  │       • "COS.Widget is not a function" → Code error
  │       • "Cannot read property" → Missing dependency
  ↓
  NO
  ↓
Type: document.querySelector('.cos-widget')
  ↓
Returns null?
  ├─ YES → Widget not mounted
  │       Check console for mount errors
  │       Try: COS.Widget.mount()
  ↓
  NO (widget element exists)
  ↓
Is widget hidden by CSS?
  ├─ YES → Check z-index, display, visibility
  │       May conflict with LinkedIn styles
  ↓
  NO
  ↓
SUCCESS ✓
```

**Quick Fix Commands:**
```javascript
// In browser console
window.COS  // Should return object

// Force remount widget
COS.Widget.mount({
  onStart: () => console.log('Start'),
  onStop: () => console.log('Stop')
})

// Check widget element
document.querySelector('.cos-widget')
```

---

## Section D: Application Gets Stuck

### Symptom: Widget shows "working" but nothing happens

```
START
  ↓
What does widget status say?
  ├─ "Starting..." → Check backend connection
  ├─ "working · linkedin" → Check modal open
  ├─ "Backend error" → See Section F
  ├─ "I'm stuck" → Loop detected (good!)
  └─ Other → Check console logs
  ↓
Is backend running?
  ├─ NO → Start: start.bat
  ↓
  YES
  ↓
Check backend terminal for errors
  ↓
Any errors?
  ├─ YES → Read error and fix
  │       Common: API timeout, rate limit
  ↓
  NO
  ↓
Is Easy Apply modal open?
  ├─ NO → Modal detection failed
  │       Manually click "Easy Apply"
  │       Then click "Resume" in widget
  ↓
  YES
  ↓
Check console for loop detection
  ↓
Says "Loop detected"?
  ├─ YES → GOOD! System is working
  │       Manually advance to next step
  │       Click "Resume" in widget
  ↓
  NO
  ↓
Check for "Stale element" errors
  ↓
Stale elements?
  ├─ YES → Widget should retry 3 times
  │       If still stuck, reload page
  ↓
  NO
  ↓
Manual recovery:
  1. Click "Stop" in widget
  2. Check what step LinkedIn is on
  3. Manually complete step if needed
  4. Click "Apply on this page" to restart
```

**Quick Fix Commands:**
```javascript
// Check current state
COS.State.load().then(s => console.log(s))

// Stop current session
COS.State.stop()

// Check for loops
// Backend will log: "Loop detected: A→B→A"
```

---

## Section E: Fields Not Filling

### Symptom: Modal opens but fields stay empty

```
START
  ↓
Check console for "Filling: [field]" messages
  ↓
Any fill messages?
  ├─ NO → Scanner not detecting fields
  │       Type: COS.Scanner.scan()
  │       Check output
  ↓
  YES (messages present)
  ↓
Are fields actually filling?
  ├─ YES but → Wrong values being filled
  │   wrong   Check profile.json
  ↓          Update values
  NO
  ↓
Check for "No answer for [field]" in console
  ↓
Missing answers?
  ├─ YES → Expected! Handoff dialog should appear
  │       Widget asks for manual input
  │       Answer and agent learns
  ↓
  NO
  ↓
Check for element visibility issues
  ↓
Console says "Element not visible"?
  ├─ YES → Element hidden or covered
  │       Check for overlays
  │       May need to scroll
  ↓
  NO
  ↓
Check profile.json is loaded
  ↓
Backend logs: "Profile loaded from ..."?
  ├─ NO → Profile not found
  │       Check: services\ml-core\app\data\profile.json
  │       Run: python -m app.seed_profile
  ↓
  YES
  ↓
Is profile.json still using defaults?
  ├─ YES → Update with your real info
  │       Restart backend
  ↓
  NO
  ↓
Check field_memory in database
  ↓
```

**Quick Fix Commands:**
```bash
# Check profile exists
type services\ml-core\app\data\profile.json

# Restart backend to reload profile
# Ctrl+C in backend terminal
# Then: python -m app.main

# Check what agent learned
cd services\ml-core\app\data
sqlite3 career_os.db
SELECT * FROM field_memory LIMIT 10;
.quit
```

```javascript
// Force scan in console
COS.Scanner.scan().then(els => console.log(`Found ${els.length} elements`))

// Check specific element
COS.Scanner.scan().then(els => {
  const emailField = els.find(e => e.text?.includes('email'))
  console.log(emailField)
})
```

---

## Section F: Backend Errors

### Symptom: Backend terminal shows ERROR messages

```
START
  ↓
Read the error message
  ↓
What type of error?
  ├─ "Invalid API key" → Check GROQ_API_KEY in .env
  │                       Get new key from console.groq.com
  ├─ "Rate limit exceeded" → Wait 60 seconds
  │                          Or increase TPM_BUDGET
  ├─ "Connection timeout" → Check internet
  │                         Check Groq status
  ├─ "Database locked" → Close other programs using DB
  │                      Restart backend
  ├─ "ModuleNotFoundError" → pip install [module]
  ├─ "PermissionError" → Run as admin
  └─ Other → Check logs: services\ml-core\career_os.log
  ↓
Still failing?
  ↓
Check logs in detail
```

**Quick Fix Commands:**
```bash
# View recent logs
powershell -command "Get-Content services\ml-core\career_os.log -Tail 20"

# Test API key
curl -H "Authorization: Bearer gsk_your_key" https://api.groq.com/openai/v1/models

# Check database
cd services\ml-core\app\data
sqlite3 career_os.db "SELECT COUNT(*) FROM applications;"

# Repair database if corrupted
sqlite3 career_os.db "PRAGMA integrity_check;"
```

---

## Section G: Slow Performance

### Symptom: Application takes too long or browser lags

```
START
  ↓
What is slow?
  ├─ Scanning → Too many elements
  ├─ Filling → Network slow or LLM timeout
  ├─ Overall → Check system resources
  └─ Browser → Memory leak or too many tabs
  ↓
Measure scan time
```

**Quick Fix Commands:**
```javascript
// Benchmark scan
console.time('scan')
COS.Scanner.scan().then(els => {
  console.timeEnd('scan')
  console.log(`Found ${els.length} elements`)
})

// Should be < 2 seconds for typical pages
// If > 5 seconds, page has too many elements

// Check element limit
console.log(COS.CONFIG.MAX_ELEMENTS)  // Should be 80
```

**Solutions:**
1. **Scanning slow:** Reduce MAX_ELEMENTS in config.js
2. **LLM slow:** Check TPM_BUDGET, may be rate limited
3. **Browser slow:** Close other tabs, check Chrome Task Manager
4. **Network slow:** Check internet speed, backend ping time

```bash
# Check backend response time
curl -w "@-" -o nul -s "http://localhost:8000/health" << EOF
time_total: %{time_total}s
EOF

# Should be < 0.1 seconds
```

---

## Section H: Submission Fails

### Symptom: Application fills but doesn't submit

```
START
  ↓
Does widget show "Review the application"?
  ├─ YES → This is EXPECTED
  │       Review manually
  │       Click "Confirm & submit" in widget
  ↓
  NO (no review prompt)
  ↓
Check .env: REVIEW_BEFORE_SUBMIT=?
  ├─ true → Expected behavior
  ├─ false → Should auto-submit
  ↓
Check console for "Clicking Submit" message
  ↓
Message present?
  ├─ NO → Submit button not found
  │       Check button text/selector
  ↓
  YES
  ↓
Did button actually click?
  ├─ NO → Element not clickable
  │       May be disabled or covered
  ↓
  YES
  ↓
Check LinkedIn response
  ↓
LinkedIn shows error?
  ├─ "Application failed" → LinkedIn rejected
  │                         Check required fields
  ├─ "Already applied" → Duplicate application
  │                      Agent should skip
  └─ Other → Check network tab
  ↓
Check backend response
```

**Quick Fix Commands:**
```javascript
// Find Submit button
COS.Scanner.scan().then(els => {
  const submit = els.find(e => 
    e.text?.toLowerCase().includes('submit') ||
    e.text?.toLowerCase().includes('send')
  )
  console.log('Submit button:', submit)
})

// Test button click manually
const submitBtn = document.querySelector('[aria-label="Submit application"]')
submitBtn?.click()
```

---

## 🛠️ Universal Diagnostic Commands

Run these anytime to check system health:

### Backend Health
```bash
curl http://localhost:8000/health
```
Expected:
```json
{"ok": true, "tokens_spent_60s": 0, "tpm_budget": 5000, "circuit_open": false}
```

### Extension Status
```javascript
// In browser console
window.COS  // Should return object
COS.State.load()  // Current session
```

### Database Check
```bash
cd services\ml-core\app\data
sqlite3 career_os.db
.tables  -- Should show: applications, field_memory, stage_counts
SELECT COUNT(*) FROM applications;
.quit
```

### Log Review
```bash
# Last 20 errors
findstr "ERROR" services\ml-core\career_os.log | more +0

# Last 20 log lines
powershell -command "Get-Content services\ml-core\career_os.log -Tail 20"
```

---

## 🚨 Emergency Recovery

### Nuclear Option: Complete Reset

Only use if nothing else works!

```bash
# 1. Stop backend (Ctrl+C)

# 2. Backup database (just in case)
copy services\ml-core\app\data\career_os.db career_os_backup.db

# 3. Clear all state
del services\ml-core\app\data\career_os.db
del services\ml-core\career_os.log

# 4. Reinstall dependencies
cd services\ml-core
rmdir /s /q .venv
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 5. Reload extension in Chrome
# Go to chrome://extensions
# Click reload icon on Career OS

# 6. Restart backend
python -m app.main
```

---

## 📊 Diagnostic Decision Matrix

| Symptom | Likely Cause | First Check | Quick Fix |
|---------|--------------|-------------|-----------|
| Backend won't start | Missing deps or config | `pip list` | Run `setup.bat` |
| Extension won't load | File missing or syntax | Check manifest.json | Reload extension |
| Widget not visible | JS error or CSS issue | Console errors | Hard refresh page |
| Gets stuck | Loop or stale element | Console logs | Click "Resume" |
| Fields not filling | Missing profile data | profile.json | Update profile |
| Backend errors | API key or network | .env file | Check API key |
| Slow performance | Too many elements | Scan time | Reduce MAX_ELEMENTS |
| Submission fails | Button not found | Submit selector | Manual submit |

---

## 🔍 Advanced Debugging

### Enable Debug Mode

1. **Backend verbose logging:**
```python
# services/ml-core/app/config.py
LOG_LEVEL = "DEBUG"  # Was "INFO"
```

2. **Frontend verbose logging:**
```javascript
// apps/extension/content/config.js
DEBUG_MODE: true,  // Add this line
```

3. **Restart everything:**
```bash
# Restart backend
# Reload extension
# Hard refresh page
```

### Read Telemetry

```bash
# Get session details
curl "http://localhost:8000/api/stats?session=sess-abc123"

# Get error patterns
curl "http://localhost:8000/api/stats?days=7" | findstr "errors"
```

---

## 💡 Pro Tips

1. **Always check logs first** - 90% of issues show up in logs
2. **Use diagnose.bat** - Automated health check
3. **Enable dry run for testing** - Safe to experiment
4. **Backup before major changes** - Use backup.bat
5. **Monitor during testing** - Use monitor.bat

---

## 📞 Still Stuck?

If none of these solutions work:

1. **Run full diagnostic:**
   ```bash
   diagnose.bat
   ```

2. **Export detailed report:**
   ```bash
   export_report.bat
   ```

3. **Check documentation:**
   - `QUICK_REFERENCE.md`
   - `CONFIGURATION_GUIDE.md`
   - `IDENTIFIED_FLAWS_AND_FIXES.md`

4. **Search logs for specific errors:**
   ```bash
   findstr "YOUR_ERROR_TEXT" services\ml-core\career_os.log
   ```

---

## ✅ Prevention Checklist

Avoid issues by following these practices:

- [ ] Run `setup.bat` on first install
- [ ] Always activate virtual environment
- [ ] Keep GROQ_API_KEY valid
- [ ] Update profile.json with real data
- [ ] Check backend is running before testing
- [ ] Use dry run mode for initial tests
- [ ] Backup database regularly
- [ ] Monitor telemetry for patterns
- [ ] Keep Chrome and extension updated
- [ ] Clear cache if behavior changes unexpectedly

---

**Most issues can be solved by running `diagnose.bat` first!**

**For systematic testing, follow `PRE_FLIGHT_CHECK.md`**

---

*This flowchart is part of Career OS comprehensive troubleshooting suite.*
