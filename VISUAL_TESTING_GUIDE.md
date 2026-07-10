# 📸 Visual Step-by-Step Testing Guide

## Complete visual walkthrough with screenshots of what you'll see at each step

---

## 🎯 Overview: What You'll Be Doing

```
[Setup] → [Verify] → [Test on LinkedIn] → [Check Results]
  5 min     2 min         10 min             5 min
```

Total time: **~25 minutes for complete first test**

---

## 📦 PART 1: Automated Setup (5 minutes)

### Step 1.1: Run Setup Script

**What to do:**
```bash
# Double-click this file:
setup.bat
```

**What you'll see:**
```
========================================
Career OS - Automated Setup Script
========================================

[1/6] Checking Python installation...
✓ Python found

[2/6] Setting up backend...
✓ Virtual environment created

[3/6] Installing dependencies...
✓ Dependencies installed

[4/6] Setting up configuration...
✓ Created .env from template

⚠️  IMPORTANT: Edit .env and add your GROQ_API_KEY
   Get your key from: https://console.groq.com/keys

[5/6] Setting up profile...
✓ Created default profile

⚠️  IMPORTANT: Edit app\data\profile.json with your real information

[6/6] Running automated tests...
✓ All tests passed!

========================================
Setup Complete!
========================================
```

### Step 1.2: Add Your API Key

**What to do:**
1. Open `services/ml-core/.env` in notepad
2. Find the line: `GROQ_API_KEY=`
3. Add your key: `GROQ_API_KEY=gsk_your_actual_key_here`
4. Save and close

**Get API key from:** https://console.groq.com/keys (Free tier works!)

**Your .env should look like:**
```bash
# Required
GROQ_API_KEY=gsk_abc123xyz456...

# Optional - keep defaults
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TPM_BUDGET=5000
REVIEW_BEFORE_SUBMIT=true
```

### Step 1.3: Add Your Profile Info

**What to do:**
1. Open `services/ml-core/app/data/profile.json`
2. Replace with your real information
3. Save

**Example:**
```json
{
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah.johnson@email.com",
  "phone": "+1-415-555-1234",
  "location": "San Francisco, CA",
  "years_experience": "5",
  "current_company": "TechCorp",
  "current_title": "Software Engineer",
  "linkedin": "https://linkedin.com/in/sarahjohnson",
  "work_authorization": "Authorized to work in the United States",
  "requires_sponsorship": "No",
  "willing_to_relocate": "Yes"
}
```

---

## 🚀 PART 2: Start Backend (1 minute)

### Step 2.1: Start Backend

**What to do:**
```bash
# Double-click this file:
start.bat
```

**What you'll see:**
```
========================================
Career OS - Starting Backend
========================================

Starting Career OS backend...

ℹ️  Backend will run at: http://127.0.0.1:8000
ℹ️  Health check: http://127.0.0.1:8000/health
ℹ️  Stats: http://127.0.0.1:8000/api/stats

Press Ctrl+C to stop
========================================

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

✅ **Success indicator:** Last line shows "Uvicorn running on..."

⚠️ **Keep this window open!** Don't close it.

---

## ✅ PART 3: Verify System (2 minutes)

### Step 3.1: Run System Test

**Open new command prompt and run:**
```bash
# Double-click this file:
test.bat
```

**What you'll see:**
```
========================================
Career OS - System Test
========================================

[Test 1/5] Checking backend health...
✓ Backend is running

[Test 2/5] Checking backend details...
{
  "ok": true,
  "tokens_spent_60s": 0,
  "tpm_budget": 5000,
  "circuit_open": false
}

[Test 3/5] Checking database...
✓ Database exists

[Test 4/5] Checking stats endpoint...
✓ Stats endpoint working

[Test 5/5] Checking applications...
✓ Found 0 applications in database

========================================
All Tests Passed! ✓
========================================
```

✅ **All checkmarks = System ready!**

### Step 3.2: Load Chrome Extension

**Visual steps:**

1. **Open Chrome**
   - Launch Google Chrome browser

2. **Go to Extensions Page**
   - Type in address bar: `chrome://extensions`
   - Press Enter

3. **Enable Developer Mode**
   - Look for toggle switch in **top-right corner**
   - Should say "Developer mode"
   - Click to turn it **ON** (should be blue)

4. **Load Extension**
   - Click button "**Load unpacked**" (top-left area)
   - Browse to: `ARBITER_v6_FINAL\apps\extension\`
   - Click "**Select Folder**"

5. **Verify Loaded**
   - You should see **"Career OS"** card appear
   - Status should show: **No errors**
   - Extension icon appears in toolbar

**What the extension card looks like:**
```
┌─────────────────────────────────────┐
│ Career OS                        🔧 │
│ Autonomous job application agent    │
│                                     │
│ ID: abcdefghijk                     │
│ Version: 0.1.0                      │
│                                     │
│ [Details] [Remove] [Errors]         │
└─────────────────────────────────────┘
```

### Step 3.3: Test Extension Load

**What to do:**
1. Open Chrome
2. Press **F12** (opens Developer Tools)
3. Click **Console** tab
4. Type: `window.COS`
5. Press **Enter**

**What you should see:**
```javascript
{
  CONFIG: {
    BULK_APPLY_ENABLED: true,
    DRY_RUN_MODE: false,
    MIN_ACTION_DELAY_MS: 700,
    ...
  },
  Scanner: { scan: f, diff: f, ... },
  Executor: { runAction: f, ... },
  State: { load: f, start: f, ... },
  Widget: { mount: f, ... }
}
```

✅ **Success:** You see an object with CONFIG, Scanner, etc.  
❌ **Failure:** Says "undefined"

---

## 🎯 PART 4: First LinkedIn Test (10 minutes)

### Step 4.1: Find a Test Job

**Visual steps:**

1. **Go to LinkedIn Jobs**
   - Navigate to: `https://www.linkedin.com/jobs/`

2. **Search for Jobs**
   - In search box, type: **"software engineer"** (or your field)
   - Click Search

3. **Filter for Easy Apply**
   - Look for "All filters" button
   - OR look for "Easy Apply" toggle
   - Click to enable **Easy Apply only**

4. **Find a Simple Job**
   - Look for job cards on left side
   - Look for **green "Easy Apply" badge**
   - Choose **internship** or **junior** role for first test
   - Click the job card

**What you see on a job page:**
```
┌────────────────────────────────────────┐
│ Software Engineer Intern               │
│ TechCorp • San Francisco, CA           │
│ Posted 2 days ago                      │
│                                        │
│ [🟢 Easy Apply]    [Save]             │
│                                        │
│ About the job...                       │
└────────────────────────────────────────┘
```

### Step 4.2: Check Widget Appears

**Look at bottom-right corner of screen:**

**What you should see:**
```
┌──────────────────────┐
│ ● Career OS       – │  ← Minimize button
├──────────────────────┤
│ Idle                 │  ← Status
│                      │
│ [Apply on this page] │  ← Main button
└──────────────────────┘
```

✅ **Widget is there:** You're ready!  
❌ **No widget:** Reload extension, refresh page

### Step 4.3: Open Developer Tools

**Before clicking "Apply", do this:**

1. Press **F12** (opens Developer Tools)
2. Click **Console** tab
3. Position window so you can see:
   - LinkedIn page
   - Career OS widget
   - Console logs

**Recommended layout:**
```
┌─────────────────┬─────────────┐
│                 │             │
│  LinkedIn       │  Console    │
│  Page           │  (logs)     │
│                 │             │
│  [Widget here]  │             │
└─────────────────┴─────────────┘
```

### Step 4.4: Start Application!

**What to do:**
1. Click **"Apply on this page"** in widget

**What happens next (watch carefully):**

**Phase 1: Starting (2-3 seconds)**
```
Widget shows:
  "Starting..."

Console shows:
  [COS] Scanning page...
  [COS] Found 45 elements
  [COS] Sending to backend...

Backend terminal shows:
  INFO: POST /api/agent/step
```

**Phase 2: Opening Modal (2-3 seconds)**
```
Widget shows:
  "working · linkedin"

Console shows:
  [COS] Action: click Easy Apply button

LinkedIn:
  Easy Apply modal opens!
  (Popup window appears with form)
```

**Phase 3: Filling Fields (5-10 seconds)**
```
Widget shows:
  "Step 1 · working"
  "Step 2 · working"

Console shows:
  [COS] Action: fill_all
  [COS] Filling: First Name = Sarah
  [COS] Filling: Last Name = Johnson
  [COS] Filling: Email = sarah@...
  [COS] Filling: Phone = +1-415...

LinkedIn:
  Watch fields fill automatically!
  Text appears in inputs
```

**Phase 4: Review (Manual - YOU ACT NOW!)**
```
Widget shows:
  ⏸ Review the application, then
     confirm to submit.
  
  [Confirm & submit]
  [Not yet]

LinkedIn:
  Form is filled out
  All fields have values
```

**What YOU do:**
1. **Look at LinkedIn form**
2. **Check each field is correct**
3. **If all looks good:** Click **"Confirm & submit"** in widget
4. **If something wrong:** Click **"Not yet"**, fix manually, then restart

**Phase 5: Submitting (2-3 seconds)**
```
Widget shows:
  "Submitting..."

Console shows:
  [COS] Action: click Submit button

LinkedIn:
  Submit button clicks
  "Sending application..." appears
```

**Phase 6: Complete! 🎉**
```
Widget shows:
  "✅ Application complete"

Console shows:
  [COS] Action: done
  [COS] Session complete

LinkedIn:
  "Application sent!" confirmation
  Success message displayed

Backend terminal shows:
  INFO: Application marked as submitted
```

### Step 4.5: What If Something Goes Wrong?

**Scenario 1: Widget says "Backend error"**
- Check backend terminal is still running
- Check no errors in backend logs
- Wait 2-4 seconds, it will retry automatically
- Widget shows retry count: "Backend error (2/5)"

**Scenario 2: Widget says "I'm stuck"**
- Loop detected!
- Click **"Resume"** after manually clicking Next
- Or click **"Stop"** and restart

**Scenario 3: Widget asks a question**
- Agent doesn't know the answer
- Example: "Please answer: How did you hear about us?"
- Type your answer in the text box
- Click **"Save & continue"**
- Agent remembers for next time!

**Scenario 4: Nothing happens**
- Check console for errors (red text)
- Check backend terminal for errors
- Try clicking **"Stop"** then **"Apply on this page"** again

---

## 📊 PART 5: Check Results (5 minutes)

### Step 5.1: View Statistics

**Open new command prompt:**
```bash
curl http://localhost:8000/api/stats?days=1
```

**What you'll see:**
```json
{
  "period_days": 1,
  "total_sessions": 1,
  "completed_sessions": 1,
  "completion_rate": 100.0,
  "avg_completion_time_seconds": 45.2,
  "total_errors": 0,
  "avg_errors_per_session": 0.0,
  "total_loops": 0,
  "loop_incident_rate": 0.0,
  "total_memory_hits": 8,
  "total_llm_calls": 2,
  "memory_hit_rate": 80.0,
  "avg_handoffs_per_session": 1.0
}
```

**What it means:**
- ✅ **completion_rate: 100** = All applications succeeded
- ✅ **memory_hit_rate: 80** = 80% fields filled from memory (no tokens)
- ✅ **avg_handoffs: 1** = Only 1 human intervention needed

### Step 5.2: View Applications

```bash
curl http://localhost:8000/api/applications
```

**What you'll see:**
```json
[
  {
    "session_id": "sess-abc123",
    "url": "https://linkedin.com/jobs/view/12345",
    "company": null,
    "title": "Software Engineer Intern",
    "status": "submitted",
    "submitted": 1,
    "created_at": "2024-01-15 10:30:45",
    "updated_at": "2024-01-15 10:31:30"
  }
]
```

### Step 5.3: Check Database

```bash
cd services\ml-core\app\data
sqlite3 career_os.db
```

**Run these queries:**
```sql
-- See all applications
SELECT * FROM applications;

-- See what agent learned
SELECT q_raw, answer, source, uses 
FROM field_memory 
ORDER BY uses DESC 
LIMIT 10;

-- See session metrics
SELECT * FROM session_metrics;

-- Exit
.quit
```

---

## 🎉 SUCCESS CHECKLIST

After your first test, check all these:

- [ ] ✅ Backend started without errors
- [ ] ✅ Extension loaded successfully
- [ ] ✅ Widget appeared on LinkedIn job page
- [ ] ✅ Easy Apply modal opened automatically
- [ ] ✅ Fields filled in automatically
- [ ] ✅ Review prompt appeared
- [ ] ✅ Application submitted to LinkedIn
- [ ] ✅ Widget showed "Complete" message
- [ ] ✅ LinkedIn showed success confirmation
- [ ] ✅ Stats endpoint shows 100% completion
- [ ] ✅ Application logged in database
- [ ] ✅ No crashes or freezes occurred

**If all checked: CONGRATULATIONS! 🎉**

Your system is working perfectly!

---

## 🚀 NEXT STEPS

### Run More Tests

1. **Test 2:** Job with 2-3 screening questions
2. **Test 3:** Multi-step application (3+ pages)
3. **Test 4:** Bulk apply (3 jobs in sequence)
4. **Test 5:** Error recovery (disconnect WiFi mid-app)

### Fine-Tune Configuration

Based on your results:
- Adjust timing in `config.js`
- Add more profile info
- Customize field synonyms

### Go to Production

Once you have 5 successful tests:
- Set `REVIEW_BEFORE_SUBMIT=false` for full automation
- Enable `BULK_APPLY_ENABLED=true`
- Apply to real jobs!

---

## 📞 Need Help?

**Quick checks:**
```bash
# Is backend running?
curl http://127.0.0.1:8000/health

# Any errors?
# Check: services/ml-core/career_os.log

# Extension loaded?
# Browser console: window.COS
```

**Common issues solved in:** `QUICK_REFERENCE.md`

---

## 🎯 Visual Troubleshooting

### Problem: "Backend not responding"

**Check this terminal:**
```
services/ml-core/
```

**Should show:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**If not running:** Run `start.bat`

### Problem: "Widget not appearing"

**Check extension page:**
```
chrome://extensions
```

**Should see:**
```
Career OS ✓ ON
No errors
```

**If errors:** Click "Errors" button, read error, fix issue

### Problem: "Fields not filling"

**Check profile:**
```
services/ml-core/app/data/profile.json
```

**Should have real data:**
```json
{
  "email": "your.real@email.com",  ← Not "john.doe@..."
  "phone": "+1-555-YOUR-NUMBER",   ← Real number
  ...
}
```

---

**You're all set! Start with Part 1 above!** 🚀
