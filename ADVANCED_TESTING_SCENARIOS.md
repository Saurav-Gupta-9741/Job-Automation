# Advanced Testing Scenarios

## Complete Edge Case Testing Guide for Career OS

---

## 🎯 Overview

This guide covers advanced testing scenarios beyond the basic LinkedIn tests. Use these to ensure Career OS handles edge cases gracefully.

---

## 📋 Test Categories

1. **Error Recovery Tests** - How the system handles failures
2. **Network Resilience Tests** - Connection issues
3. **DOM Manipulation Tests** - Dynamic page changes
4. **Rate Limiting Tests** - LinkedIn throttling
5. **Data Validation Tests** - Invalid input handling
6. **Concurrency Tests** - Multiple jobs/tabs
7. **Security Tests** - Token handling, sensitive data
8. **Performance Tests** - Speed and efficiency

---

## 🔴 CATEGORY 1: Error Recovery Tests

### Test 1.1: Stale Element Recovery

**Objective:** Verify agent recovers when elements become stale

**Steps:**
1. Start application on a job
2. Wait for modal to open
3. During field filling, open browser DevTools
4. In console, run: `document.querySelector('.jobs-easy-apply-modal').innerHTML = document.querySelector('.jobs-easy-apply-modal').innerHTML`
5. This re-renders the modal, making all elements stale
6. Agent should detect stale elements and retry

**Expected Result:**
- Widget shows "Retrying..." (1/3, 2/3, 3/3)
- Agent successfully re-scans and continues
- No crash or infinite loop

**Pass Criteria:**
- ✅ Application completes successfully
- ✅ Console shows "Stale element detected, retrying..."
- ✅ Max 3 retry attempts

---

### Test 1.2: Backend Connection Lost

**Objective:** Verify graceful handling when backend crashes

**Steps:**
1. Start application
2. Let it reach step 2 or 3
3. In backend terminal, press Ctrl+C to stop backend
4. Agent should detect connection failure

**Expected Result:**
- Widget shows "Backend error (1/5)"
- Agent retries 5 times with exponential backoff
- After 5 failures, shows clear error message

**Pass Criteria:**
- ✅ No browser crash
- ✅ Error message is clear: "Backend unavailable"
- ✅ Can restart backend and resume

---

### Test 1.3: Mid-Application Page Crash

**Objective:** Verify recovery from accidental page refresh

**Steps:**
1. Start application
2. Wait for modal to open and fields to start filling
3. Press F5 (refresh page)
4. Agent state should persist
5. Widget should offer session recovery

**Expected Result:**
- Widget shows recovery dialog
- Options: "Resume" or "Start Fresh"
- Session ID persists in chrome.storage

**Pass Criteria:**
- ✅ Session recovery dialog appears
- ✅ Can resume from last known state
- ✅ Or can cleanly start fresh

---

## 🌐 CATEGORY 2: Network Resilience Tests

### Test 2.1: Intermittent Connection

**Objective:** Handle spotty WiFi gracefully

**Steps:**
1. Start application
2. During execution, toggle WiFi off for 5 seconds
3. Turn WiFi back on
4. Agent should retry failed requests

**Expected Result:**
- Widget shows "Connection error, retrying..."
- Exponential backoff (2s, 4s, 8s delays)
- Resumes when connection restored

**Pass Criteria:**
- ✅ No data loss
- ✅ Continues from exact same state
- ✅ All filled fields remain filled

---

### Test 2.2: Groq API Timeout

**Objective:** Handle slow/timeout from Groq API

**Steps:**
1. In `.env`, temporarily set invalid API endpoint (impossible)
2. Start application with unknown fields
3. Agent will timeout trying to call LLM

**Expected Result:**
- Widget shows "LLM timeout, need help"
- Falls back to handoff for that field
- Doesn't retry infinitely

**Pass Criteria:**
- ✅ Times out after 30 seconds
- ✅ Shows handoff dialog
- ✅ Can manually answer and continue

---

## 🔄 CATEGORY 3: DOM Manipulation Tests

### Test 3.1: Dynamic Shadow DOM

**Objective:** Verify shadow DOM scanning works

**Steps:**
1. Find a job with custom web components (check DevTools)
2. Start application
3. Check console for "Shadow root detected" messages

**Expected Result:**
- Agent scans shadow roots
- Finds elements inside shadow DOM
- Fills fields correctly

**Pass Criteria:**
- ✅ Elements inside shadow DOM are detected
- ✅ No "element not found" errors
- ✅ Application completes

---

### Test 3.2: Iframe Application Form

**Objective:** Verify iframe scanning works

**Steps:**
1. Find a Workday or Greenhouse job (uses iframes)
2. Start application
3. Check console for "Scanning iframe" messages

**Expected Result:**
- Agent detects iframe
- Scans inside iframe
- Fills fields in iframe

**Pass Criteria:**
- ✅ Iframe content is scanned
- ✅ Elements found inside iframe
- ✅ Application progresses

**Note:** Cross-origin iframes cannot be scanned (expected limitation)

---

### Test 3.3: Modal Close Detection

**Objective:** Detect if modal closes unexpectedly

**Steps:**
1. Start application
2. During execution, manually click outside modal (to close it)
3. Agent should detect modal disappeared

**Expected Result:**
- Widget shows "Modal closed unexpectedly"
- Offers to restart or stop
- No infinite loop

**Pass Criteria:**
- ✅ Detects modal closure
- ✅ Clean error message
- ✅ Can restart application

---

## ⏱️ CATEGORY 4: Rate Limiting Tests

### Test 4.1: LinkedIn Rate Limit Warning

**Objective:** Detect and handle "slow down" messages

**Steps:**
1. Apply to 5-10 jobs rapidly (< 1 minute each)
2. LinkedIn may show rate limit warning
3. Agent should detect warning text

**Expected Result:**
- Widget shows "Rate limit detected"
- Pauses for 2-5 minutes
- Shows countdown timer

**Pass Criteria:**
- ✅ Detects rate limit message
- ✅ Pauses automatically
- ✅ Resumes after wait period

---

### Test 4.2: Too Many Applications in Session

**Objective:** Handle bulk apply limit gracefully

**Steps:**
1. Enable bulk apply
2. Queue 20+ jobs
3. LinkedIn may block after 10-15 applications
4. Agent should stop gracefully

**Expected Result:**
- Widget shows "Daily limit reached"
- Stops bulk apply
- Saves progress

**Pass Criteria:**
- ✅ Detects application limit
- ✅ Doesn't retry blocked applications
- ✅ Telemetry shows reason for stop

---

## ✅ CATEGORY 5: Data Validation Tests

### Test 5.1: Invalid Email Format

**Objective:** Validate email before submission

**Steps:**
1. In `profile.json`, set email to: `"invalid-email"`
2. Start application on job requiring email
3. Agent should validate and reject

**Expected Result:**
- Validation fails: "Invalid email format"
- Falls back to handoff
- Asks user for correct email

**Pass Criteria:**
- ✅ Validation catches invalid email
- ✅ Doesn't submit invalid data
- ✅ User can correct via handoff

---

### Test 5.2: Phone Number Validation

**Objective:** Validate phone format

**Steps:**
1. Set phone in profile to: `"123"` (too short)
2. Apply to job requiring phone
3. Validation should fail

**Expected Result:**
- Validation error: "Phone number too short"
- Handoff dialog appears
- User can provide valid phone

**Pass Criteria:**
- ✅ Catches invalid phone
- ✅ Clear error message
- ✅ Learns corrected value

---

### Test 5.3: Required Field Detection

**Objective:** Never skip required fields

**Steps:**
1. Apply to job with required field marked `*`
2. Don't provide answer in profile
3. Agent should request via handoff, not skip

**Expected Result:**
- Agent detects `required` attribute
- Shows handoff: "Required field: [field name]"
- Waits for user input

**Pass Criteria:**
- ✅ Doesn't skip required fields
- ✅ Clear indication field is required
- ✅ Blocks submission until answered

---

## 🔀 CATEGORY 6: Concurrency Tests

### Test 6.1: Multiple Tabs

**Objective:** Handle Career OS in multiple LinkedIn tabs

**Steps:**
1. Open 2 LinkedIn job tabs
2. Load Career OS in both
3. Start application in Tab 1
4. Switch to Tab 2 and try to start

**Expected Result:**
- Tab 2 shows: "Application in progress in another tab"
- Only one session runs at a time
- No race conditions

**Pass Criteria:**
- ✅ Only one session active
- ✅ Clear message in second tab
- ✅ No database conflicts

---

### Test 6.2: Rapid Start/Stop

**Objective:** Handle quick stop/restart cycles

**Steps:**
1. Start application
2. Immediately click Stop
3. Immediately click Start again
4. Repeat 5 times rapidly

**Expected Result:**
- Each stop cleanly terminates
- Each start begins fresh scan
- No zombie sessions

**Pass Criteria:**
- ✅ Clean start/stop every time
- ✅ No orphaned sessions
- ✅ State is consistent

---

## 🔐 CATEGORY 7: Security Tests

### Test 7.1: CSRF Token Extraction

**Objective:** Verify CSRF tokens are captured

**Steps:**
1. Apply to job with CSRF protection
2. Check backend logs for "CSRF token"
3. Verify token is sent to backend

**Expected Result:**
- Console shows: "Extracted CSRF token: csrf_abc..."
- Backend logs show token received
- Form submission includes token

**Pass Criteria:**
- ✅ Token extracted from page
- ✅ Token sent to backend
- ✅ Submission succeeds

---

### Test 7.2: No Sensitive Data in Logs

**Objective:** Ensure passwords/SSN not logged

**Steps:**
1. Apply to job with sensitive fields
2. Check browser console logs
3. Check backend logs (career_os.log)
4. Search for sensitive patterns

**Expected Result:**
- Logs show field names, not values
- Example: "Filled: SSN" not "Filled: SSN = 123-45-6789"
- Password fields show "***"

**Pass Criteria:**
- ✅ No SSN in logs
- ✅ No passwords in logs
- ✅ Field names only

---

## ⚡ CATEGORY 8: Performance Tests

### Test 8.1: Large Form Performance

**Objective:** Handle forms with 50+ fields

**Steps:**
1. Find complex job application (government, large corp)
2. Form has 30+ fields
3. Measure time to scan and fill

**Expected Result:**
- Scan completes in < 5 seconds
- Filling completes in < 30 seconds
- No browser slowdown

**Pass Criteria:**
- ✅ Fast scanning even with many elements
- ✅ No memory leaks
- ✅ Smooth UI throughout

---

### Test 8.2: Token Budget Management

**Objective:** Verify LLM token budget is respected

**Steps:**
1. Set `GROQ_TPM_BUDGET=1000` (low limit)
2. Apply to multiple jobs rapidly
3. Should hit token limit

**Expected Result:**
- Circuit breaker opens
- Widget shows "Rate limited, waiting..."
- Automatically resumes after 60 seconds

**Pass Criteria:**
- ✅ Respects token budget
- ✅ Doesn't exceed Groq limits
- ✅ Auto-recovers when budget resets

---

### Test 8.3: Memory Efficiency

**Objective:** No memory leaks during long sessions

**Steps:**
1. Apply to 10 jobs in sequence
2. Monitor browser memory (Chrome Task Manager)
3. Check for memory growth

**Expected Result:**
- Memory stable or grows slowly
- No exponential growth
- Garbage collection works

**Pass Criteria:**
- ✅ Memory < 200MB after 10 jobs
- ✅ No leaked DOM nodes
- ✅ Extension stays responsive

---

## 🎭 CATEGORY 9: LinkedIn A/B Test Variations

### Test 9.1: Different Modal Layouts

**Objective:** Handle LinkedIn UI variations

**Steps:**
1. Apply to multiple jobs on different days
2. LinkedIn may show different modal layouts (A/B tests)
3. Agent should adapt

**Expected Result:**
- Agent detects modal regardless of layout
- Finds "Next" or "Submit" button despite class changes
- Completes application

**Pass Criteria:**
- ✅ Works across UI variations
- ✅ Multiple detection strategies succeed
- ✅ No hardcoded selectors fail

---

### Test 9.2: Different Button Text

**Objective:** Handle localized or variant button text

**Steps:**
1. If possible, switch LinkedIn language
2. Or find jobs with "Review" instead of "Next"
3. Agent should recognize button

**Expected Result:**
- Multiple button word lists checked
- "Next", "Continue", "Review", "Submit" all work
- Application progresses

**Pass Criteria:**
- ✅ Finds buttons by multiple text options
- ✅ Not hardcoded to one word
- ✅ Adapts to variants

---

## 🧪 CATEGORY 10: Bulk Apply Stress Tests

### Test 10.1: Bulk Apply 10 Jobs

**Objective:** Handle bulk apply reliably

**Steps:**
1. Enable bulk apply in config
2. Queue 10 Easy Apply jobs
3. Let agent run through all

**Expected Result:**
- Completes all 10 (or stops at rate limit)
- Properly advances to next job
- No stuck loops between jobs

**Pass Criteria:**
- ✅ >80% completion rate (8/10)
- ✅ Moves to next job automatically
- ✅ Stops gracefully if issues

---

### Test 10.2: Mixed Job Types

**Objective:** Handle mix of Easy Apply and external

**Steps:**
1. Queue contains Easy Apply + external redirect jobs
2. Start bulk apply
3. Agent should skip external links

**Expected Result:**
- Skips non-Easy Apply jobs
- Logs: "Skipping external application"
- Continues to next Easy Apply

**Pass Criteria:**
- ✅ Only applies to Easy Apply jobs
- ✅ Doesn't get stuck on external links
- ✅ Bulk apply continues

---

## 📊 Test Result Tracking

Use this template to track results:

```
Test ID: [e.g., 1.1]
Test Name: [e.g., Stale Element Recovery]
Date: [YYYY-MM-DD]
Pass/Fail: [✅ / ❌]
Notes: [Any observations]
Session ID: [From telemetry]
Telemetry Link: http://localhost:8000/api/stats?session=[id]
```

---

## 🎯 Success Criteria Summary

**To declare Career OS production-ready:**

- [ ] All Category 1 tests pass (Error Recovery)
- [ ] 80%+ Category 2 tests pass (Network)
- [ ] 80%+ Category 3 tests pass (DOM)
- [ ] All Category 4 tests pass (Rate Limiting)
- [ ] All Category 5 tests pass (Validation)
- [ ] 80%+ Category 6 tests pass (Concurrency)
- [ ] All Category 7 tests pass (Security)
- [ ] 80%+ Category 8 tests pass (Performance)
- [ ] 70%+ Category 9 tests pass (A/B Tests)
- [ ] 70%+ Category 10 tests pass (Bulk Apply)

**Overall Target:** 85% pass rate across all categories

---

## 🛠️ Troubleshooting During Tests

### Issue: Test is unclear

**Solution:** Check console logs, widget status, backend logs for clues

### Issue: Can't reproduce edge case

**Solution:** Use DevTools to manually trigger conditions (see Test 1.1 example)

### Issue: Test fails unexpectedly

**Solution:** 
1. Check telemetry: `curl http://localhost:8000/api/stats?session=[id]`
2. Check logs: `type services\ml-core\career_os.log`
3. Open GitHub issue with details

---

## 📈 Continuous Improvement

After each test cycle:

1. **Review telemetry data**
   ```bash
   curl http://localhost:8000/api/stats?days=7
   ```

2. **Identify patterns**
   - Which error types are most common?
   - Which confidence levels are frequent?
   - How many handoffs per session?

3. **Update field memory**
   - Review learned questions
   - Add common answers to profile

4. **Adjust configuration**
   - Tune delays if too fast/slow
   - Adjust confidence thresholds
   - Update synonyms

---

## 🎓 Expert Tips

### Tip 1: Use Dry Run First
Always test new scenarios in dry run mode first:
```javascript
// config.js
DRY_RUN_MODE: true
```

### Tip 2: Enable Verbose Logging
For debugging, increase log verbosity:
```python
# config.py
LOG_LEVEL = "DEBUG"
```

### Tip 3: Backup Before Tests
Before stress testing:
```bash
backup.bat
```

### Tip 4: Monitor During Tests
Keep monitor running:
```bash
monitor.bat
```

### Tip 5: Export Results
After test cycle:
```bash
export_report.bat
```

---

## 📚 Related Documentation

- **Basic Testing:** `LINKEDIN_TESTING_GUIDE.md`
- **Pre-Flight Checks:** `PRE_FLIGHT_CHECK.md`
- **Visual Guide:** `VISUAL_TESTING_GUIDE.md`
- **Known Issues:** `IDENTIFIED_FLAWS_AND_FIXES.md`

---

**Ready to test edge cases? Start with Category 1!** 🚀

---

*This guide is part of the Career OS comprehensive testing suite. For production readiness, complete all test categories with >85% pass rate.*
