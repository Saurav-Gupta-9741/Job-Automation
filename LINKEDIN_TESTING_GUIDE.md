# LinkedIn Easy Apply - Step-by-Step Testing Guide

## 🎯 Goal
Successfully complete 5 LinkedIn Easy Apply applications with Career OS to validate production readiness.

---

## 🛠️ Pre-Test Setup (5 minutes)

### 1. Start Backend
```bash
cd services/ml-core
.venv\Scripts\activate
python -m app.main
```
✅ **Verify:** Terminal shows `INFO: Uvicorn running on http://127.0.0.1:8000`

### 2. Load Extension
1. Chrome → `chrome://extensions`
2. Enable "Developer mode"
3. Refresh if already loaded
4. Verify no errors in "Errors" section

### 3. Enable Safety Mode
```bash
cd services/ml-core
# Edit .env file
# Set: REVIEW_BEFORE_SUBMIT=true
```
✅ **Why:** Manual review before each submission during testing

### 4. Open Developer Tools
- Press F12 in Chrome
- Go to Console tab
- Keep it open throughout testing
✅ **Why:** Monitor for errors in real-time

---

## 📋 Test 1: Simple Easy Apply (No Screening Questions)

### Step 1: Find a Simple Job
1. Go to: `https://www.linkedin.com/jobs/`
2. Search: "software engineer" (or your field)
3. Filter: "Easy Apply" only
4. Look for jobs with **0 additional questions** (most basic)

**How to identify:**
- Usually internships or junior roles
- "Easy Apply" badge visible
- No "+" indicator next to Easy Apply button

### Step 2: Click Job Card
- Click on a job from the list
- Job details appear on right side
- "Easy Apply" button should be visible

### Step 3: Start Career OS
1. Click "Apply on this page" in Career OS widget
2. **Observe:**
   - Widget status changes to "Starting..."
   - Backend terminal shows incoming request
   - Console shows scanner activity

### Step 4: Monitor Progress
Watch for these stages:
1. **Perceive:** Scanner finds Easy Apply button
2. **Think:** Backend returns `click` action
3. **Act:** Modal opens with basic fields
4. **Perceive:** Scanner detects fields
5. **Think:** Backend fills from profile
6. **Act:** Fields auto-populated
7. **Think:** Backend returns "review" action
8. **Handoff:** You review and confirm

### Step 5: Review & Submit
1. Widget shows "Review the application..."
2. **Manually check:**
   - Name is correct
   - Email is correct
   - Phone is correct
   - Resume attached (if required)
3. Click "Confirm & submit" in widget
4. **Observe:** Application submits

### Step 6: Verify Success
✅ **Expected:** LinkedIn shows "Application sent" confirmation  
✅ **Widget:** Shows "✅ Application complete"  
✅ **Backend:** Terminal shows "DONE" action

### Step 7: Check Telemetry
```bash
curl http://localhost:8000/api/stats?days=1
```
✅ **Expected:**
- `total_sessions: 1`
- `completed_sessions: 1`
- `completion_rate: 100`

---

## 📋 Test 2: Easy Apply with 2-3 Screening Questions

### Step 1: Find a Standard Job
Look for jobs with **2-3 additional questions**:
- "Years of experience?"
- "Current location?"
- "Work authorization?"

### Step 2: Start & Monitor
Same as Test 1, but watch for:
1. **First page:** Basic info auto-filled
2. **Click Next:** Agent advances automatically
3. **Second page:** Screening questions appear
4. **Auto-fill:** Most questions filled from profile
5. **Handoff:** Unknown questions ask for input

### Step 3: Handle Handoffs
If widget asks for input:
1. Read the question carefully
2. Type your answer
3. Click "Save & continue"
4. **Observe:** Answer saved to memory for future

### Step 4: Complete & Verify
Same verification steps as Test 1

**📊 Expected Metrics:**
- `memory_hits` increased (reused answers)
- `handoffs` = 0-2 max
- `llm_calls` = 1-3

---

## 📋 Test 3: Multi-Step Easy Apply (3+ Pages)

### Step 1: Find Complex Job
Look for jobs with **multiple steps**:
- Work experience details
- Education details
- Diversity questions
- Custom screening questions

### Step 2: Start & Monitor
Watch for progression through multiple pages:
1. Page 1: Basic info → Auto-filled → Next
2. Page 2: Experience → Partially filled → Next
3. Page 3: Screening → Mix of auto/manual → Next
4. Final: Review → Manual confirmation → Submit

### Step 3: Track Progress
Monitor widget status for step progression:
- "working · linkedin" means active processing
- "Step X" might appear if tracking enabled
- Each page should advance automatically when filled

### Step 4: Verify Loop Detection
If agent gets stuck:
✅ **Expected:** Widget shows loop detected message after 4-6 repetitions  
✅ **Telemetry:** `loops` count increased  
✅ **Action:** Click "Resume" after manually advancing

**📊 Expected Metrics:**
- `total_steps` = 8-15 (depending on job)
- `handoffs` = 1-3
- `loops` = 0 (ideally)

---

## 📋 Test 4: Bulk Apply (3 Jobs in Sequence)

### Step 1: Verify Config
```javascript
// In config.js
BULK_APPLY_ENABLED: true
```

### Step 2: Find Multiple Jobs
- LinkedIn job search results page
- At least 3 Easy Apply jobs visible
- Scroll so 3+ job cards are in view

### Step 3: Start on First Job
1. Click first job card
2. Click "Apply on this page"
3. Complete first application
4. **Observe:** Widget says "✅ Done. Loading next..."

### Step 4: Watch Automatic Progression
Agent should:
1. Dismiss success modal
2. Find next job card
3. Click it
4. Wait for job to load
5. Restart application loop automatically

### Step 5: Monitor All 3
Let it complete 3 jobs (or click Stop after 2 for testing)

**📊 Expected Metrics:**
- `total_sessions` = 3
- `completed_sessions` = 3
- Applications logged in database

---

## 📋 Test 5: Error Recovery

### Test 5a: Network Interruption
1. Start an application
2. Disconnect WiFi mid-application
3. **Observe:**
   - Widget shows "Backend error (1/5)"
   - Retry delay increases (2s, 4s, 8s)
4. Reconnect WiFi
5. **Expected:** Auto-recovery, application continues

### Test 5b: Rate Limit Simulation
1. Apply to 10+ jobs quickly
2. If LinkedIn shows "slow down" message
3. **Expected:**
   - Agent detects rate limit
   - Widget shows "LinkedIn is asking you to slow down"
   - Hands off to user

### Test 5c: Already Applied
1. Find a job you already applied to
2. Start Career OS
3. **Expected:**
   - Agent detects "You applied" message
   - Returns DONE immediately
   - No wasted actions

---

## 🐛 Common Issues & Solutions

### Issue: Widget doesn't appear
**Solution:** Reload extension, hard refresh page (Ctrl+Shift+R)

### Issue: "Backend error" persists
**Solution:** 
```bash
# Check backend health
curl http://127.0.0.1:8000/health
# Restart backend if needed
```

### Issue: Stuck in loop
**Expected:** Loop detection triggers after 4-6 repeats  
**Action:** Click "Resume" after manually advancing

### Issue: Wrong field filled
**Action:**
1. Click Stop
2. Manually correct
3. Restart or continue manually

### Issue: Resume upload fails
**Check:** `/api/resume` endpoint returns resume data  
**Fallback:** Upload manually if needed

---

## 📊 Success Criteria

After 5 tests, check telemetry:
```bash
curl http://localhost:8000/api/stats?days=1
```

### Target Metrics
- ✅ `completion_rate` ≥ 80%
- ✅ `avg_errors_per_session` < 0.5
- ✅ `loop_incident_rate` < 10%
- ✅ `avg_handoffs_per_session` < 2.5
- ✅ `memory_hit_rate` > 40%

### Qualitative Success
- ✅ No crashes or freezes
- ✅ Clear error messages when issues occur
- ✅ Graceful handling of edge cases
- ✅ Reasonable execution time (< 2 minutes per job)

---

## 📝 Document Findings

### For Each Test, Record:
1. **Job Title & Company:** 
2. **Application Complexity:** Simple / Standard / Complex
3. **Completion:** Yes / No / Partial
4. **Handoffs Required:** Number and reasons
5. **Errors Encountered:** Type and recovery
6. **Time Taken:** Start to completion
7. **Notes:** Any unusual behavior

### Template:
```
Test #: ___
Job: _________________
Status: [ ] Complete [ ] Failed [ ] Partial
Handoffs: ___
Time: ___ seconds
Issues: _______________
Notes: ________________
```

---

## 🔍 Post-Test Analysis

### 1. Review Telemetry
```bash
curl http://localhost:8000/api/stats?days=1 | jq
```

### 2. Check Applications
```bash
curl http://localhost:8000/api/applications | jq
```

### 3. Database Deep Dive
```bash
cd services/ml-core/app/data
sqlite3 career_os.db

-- Session metrics
SELECT * FROM session_metrics ORDER BY updated_at DESC LIMIT 5;

-- Error events
SELECT json_extract(details, '$.error_type'), COUNT(*) 
FROM telemetry_events 
WHERE event_type='error' 
GROUP BY json_extract(details, '$.error_type');

-- Loop incidents
SELECT * FROM telemetry_events WHERE event_type='loop';

-- LLM efficiency
SELECT 
  SUM(memory_hits) as memory, 
  SUM(llm_calls) as llm,
  ROUND(CAST(SUM(memory_hits) AS FLOAT) / (SUM(memory_hits) + SUM(llm_calls)) * 100, 1) as hit_rate
FROM session_metrics;

.quit
```

### 4. Identify Patterns
- Which jobs had highest success rate?
- What types of questions required handoffs?
- Were there any recurring errors?
- Did loop detection trigger appropriately?

---

## ✅ Test Completion Checklist

- [ ] Test 1: Simple Easy Apply completed successfully
- [ ] Test 2: Standard Easy Apply with screening questions
- [ ] Test 3: Multi-step application completed
- [ ] Test 4: Bulk apply on 3 jobs
- [ ] Test 5a: Network interruption recovery tested
- [ ] Test 5b: Rate limit handling verified
- [ ] Test 5c: Already applied detection works
- [ ] Telemetry data reviewed
- [ ] Success criteria met (≥80% completion)
- [ ] Issues documented
- [ ] Database analysis complete

---

## 🚀 Next Steps After Testing

### If Success Rate ≥ 80%
1. Proceed to Phase 2 testing (10 varied jobs)
2. Enable bulk apply for real usage
3. Start tracking long-term metrics

### If Success Rate < 80%
1. Review all failures
2. Categorize issues (adapter, LLM, executor)
3. Prioritize fixes based on frequency
4. Implement fixes and retest

### Common Improvements Needed
- Fine-tune confidence thresholds
- Add more field synonyms
- Improve LinkedIn selector robustness
- Enhance error messages

---

## 🎓 Learning Objectives

By end of testing, you should understand:
- ✅ How the Perceive → Think → Act loop works
- ✅ When and why handoffs occur
- ✅ How loop detection saves you from infinite loops
- ✅ How telemetry helps identify issues
- ✅ What makes some jobs harder than others

---

## 📞 Quick Commands Reference

```bash
# Start backend
cd services/ml-core && .venv\Scripts\activate && python -m app.main

# Check health
curl http://127.0.0.1:8000/health

# View stats
curl http://localhost:8000/api/stats?days=1 | jq

# View applications
curl http://localhost:8000/api/applications | jq '.[:5]'

# Check database
cd services/ml-core/app/data && sqlite3 career_os.db
SELECT COUNT(*) FROM applications WHERE submitted=1;
.quit
```

---

**Ready to test!** Start with Test 1 and work through systematically. Good luck! 🚀
