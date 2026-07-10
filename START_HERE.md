# 🚀 START HERE - Quick Start Guide

## Welcome to Career OS!

This guide gets you from zero to testing in 15 minutes.

---

## ⚡ Super Quick Start (5 Steps)

### Step 1: Install Dependencies (2 minutes)

```bash
cd services/ml-core
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure (2 minutes)

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your Groq API key
# Get key from: https://console.groq.com/keys
```

Required in `.env`:
```bash
GROQ_API_KEY=gsk_your_actual_key_here
```

### Step 3: Start Backend (1 minute)

```bash
python -m app.main
```

Expected output:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Load Extension (2 minutes)

1. Open Chrome
2. Go to `chrome://extensions`
3. Enable "Developer mode" (top-right toggle)
4. Click "Load unpacked"
5. Select the `apps/extension/` folder
6. Done! Extension should appear in list

### Step 5: Verify (1 minute)

Open browser console (F12) and check:
```javascript
window.COS  // Should return an object
```

Open LinkedIn:
```
https://www.linkedin.com/jobs/
```

Widget should appear in bottom-right corner!

---

## ✅ Pre-Flight Check (2 minutes)

### Backend Health

```bash
curl http://127.0.0.1:8000/health
```

Expected response:
```json
{
  "ok": true,
  "tokens_spent_60s": 0,
  "tpm_budget": 5000,
  "circuit_open": false
}
```

### Extension Check

In Chrome on any page, press F12, then:
```javascript
console.log(window.COS.CONFIG)
```

Should show configuration object.

### Widget Check

On LinkedIn job page:
- Look for "Career OS" widget bottom-right
- Widget shows "Idle" status
- "Apply on this page" button visible

---

## 🧪 First Test (5 minutes)

### Find a Test Job

1. Go to LinkedIn Jobs
2. Search for "software engineer"
3. Filter: "Easy Apply" only
4. Click any simple job (internship or junior role best for first test)

### Run First Application

1. Click "Apply on this page" in Career OS widget
2. Watch the console (F12) for logs
3. Watch the widget status update
4. Observe the application flow

**For safety:** Set `REVIEW_BEFORE_SUBMIT=true` in `.env` first!

### Expected Flow

1. Widget: "Starting..."
2. Easy Apply modal opens
3. Widget: "working · linkedin"
4. Fields auto-fill
5. Widget: "Review the application..."
6. You manually review
7. Click "Confirm & submit" in widget
8. Application submits!
9. Widget: "✅ Application complete"

---

## 📊 Check Results

### View Telemetry

```bash
curl http://localhost:8000/api/stats?days=1
```

### View Applications

```bash
curl http://localhost:8000/api/applications
```

### Check Database

```bash
cd services/ml-core/app/data
sqlite3 career_os.db
SELECT * FROM applications;
.quit
```

---

## 🎯 What's Next?

After your first successful test:

### Option A: Continue Testing
Follow `LINKEDIN_TESTING_GUIDE.md` for comprehensive testing:
- Test 2: Jobs with screening questions
- Test 3: Multi-step applications
- Test 4: Bulk apply (3+ jobs)
- Test 5: Error recovery scenarios

### Option B: Full Pre-Flight
Follow `PRE_FLIGHT_CHECK.md` for complete system verification (45+ checks)

### Option C: Configuration
Read `CONFIGURATION_GUIDE.md` to customize settings:
- Timing delays
- Bulk apply mode
- Dry run mode
- Profile data

---

## 🐛 Troubleshooting

### Backend won't start

**Check Python version:**
```bash
python --version  # Should be 3.8+
```

**Check if port 8000 is free:**
```bash
netstat -ano | findstr :8000
```

**Solution:** Kill any process using port 8000 or change port in `main.py`

### Extension won't load

**Check for errors:**
1. Go to `chrome://extensions`
2. Find Career OS
3. Click "Errors" button
4. Fix any JavaScript errors shown

**Solution:** Reload extension, hard refresh page (Ctrl+Shift+R)

### Widget doesn't appear

**Check console:**
```javascript
window.COS  // Should not be undefined
```

**Solution:** Reload extension, clear cache, hard refresh

### Backend errors

**Check logs:**
```bash
# Backend terminal shows detailed errors
# Look for "ERROR" lines
```

**Common issues:**
- `GROQ_API_KEY` not set or invalid
- Database permissions issue
- Missing dependencies

---

## ⚙️ Configuration Quick Tips

### For Testing (Safety First)

```bash
# .env
REVIEW_BEFORE_SUBMIT=true

# config.js
DRY_RUN_MODE: true,  # Logs actions without executing
BULK_APPLY_ENABLED: false
```

### For Production (Fully Autonomous)

```bash
# .env
REVIEW_BEFORE_SUBMIT=false

# config.js
DRY_RUN_MODE: false,
BULK_APPLY_ENABLED: true
```

### For Speed

```javascript
// config.js
MIN_ACTION_DELAY_MS: 400,
MAX_ACTION_DELAY_MS: 800,
```

### For Stealth

```javascript
// config.js
MIN_ACTION_DELAY_MS: 1500,
MAX_ACTION_DELAY_MS: 2500,
```

---

## 📚 Documentation Map

**Just getting started?**
- `START_HERE.md` ← You are here
- `README.md` - Overview
- `QUICK_REFERENCE.md` - Common commands

**Ready to test?**
- `PRE_FLIGHT_CHECK.md` - Verify everything works
- `LINKEDIN_TESTING_GUIDE.md` - Step-by-step tests

**Need configuration help?**
- `CONFIGURATION_GUIDE.md` - All settings explained

**Want to understand the system?**
- `architecture-blueprint.md` - How it all works
- `ENHANCEMENTS_OVERVIEW.md` - What's been built

**Developer?**
- `IDENTIFIED_FLAWS_AND_FIXES.md` - Known issues
- `FINAL_STATUS.md` - Implementation status

---

## 🎓 Learning Path

### Day 1: Setup & First Test
1. ✅ Install dependencies
2. ✅ Configure `.env`
3. ✅ Start backend
4. ✅ Load extension
5. ✅ First test job

### Day 2: Comprehensive Testing
6. Run Tests 1-5 from `LINKEDIN_TESTING_GUIDE.md`
7. Review telemetry data
8. Document any issues

### Day 3: Configuration & Optimization
9. Customize timing based on results
10. Populate full profile data
11. Fine-tune confidence thresholds

### Day 4+: Production Use
12. Enable bulk apply
13. Monitor `/api/stats` daily
14. Export applications weekly

---

## 💡 Pro Tips

### 1. Start Conservative
- Use `REVIEW_BEFORE_SUBMIT=true` initially
- Test on jobs you don't care about
- Enable `DRY_RUN_MODE` for first few runs

### 2. Monitor Closely
- Keep browser console open (F12)
- Watch backend terminal for errors
- Check `/api/stats` after each session

### 3. Build Memory
- First few jobs need more handoffs (agent is learning)
- Each manual answer is saved forever
- Memory hit rate improves over time

### 4. Respect Rate Limits
- Don't apply to 50 jobs in 10 minutes
- If LinkedIn warns "slow down", listen
- Agent detects and pauses for rate limits

### 5. Keep Profile Updated
- Review `profile.json` accuracy
- Add new skills as you learn them
- Update work authorization if changes

---

## 🎯 Success Checklist

After first test, you should have:

- [ ] Backend running without errors
- [ ] Extension loaded in Chrome
- [ ] Widget visible on LinkedIn
- [ ] 1 successful test application
- [ ] Telemetry data recorded
- [ ] No crashes or freezes

If all checked, you're ready for comprehensive testing!

---

## 🆘 Need Help?

### Quick Diagnostics

```bash
# Check everything at once
curl http://127.0.0.1:8000/health && echo "Backend OK"
```

```javascript
// In browser console
console.log(window.COS ? "Extension OK" : "Extension FAIL")
```

### Common Commands

```bash
# Restart backend
cd services/ml-core
.venv\Scripts\activate
python -m app.main

# View stats
curl http://localhost:8000/api/stats?days=1

# Check database
cd services/ml-core/app/data && sqlite3 career_os.db
```

### Documentation

- **Quick fixes:** `QUICK_REFERENCE.md`
- **Detailed testing:** `LINKEDIN_TESTING_GUIDE.md`
- **All settings:** `CONFIGURATION_GUIDE.md`
- **System design:** `architecture-blueprint.md`

---

## ✨ You're All Set!

**Backend running?** ✅  
**Extension loaded?** ✅  
**Widget visible?** ✅  
**First test successful?** ⏳ Let's do it!

**Go to LinkedIn and click "Apply on this page"!** 🚀

---

**Next Step:** `LINKEDIN_TESTING_GUIDE.md` → Test 1: Simple Easy Apply

**Good luck!** 🎉
