# Career OS Robustness - Testing Guide

## Quick Start

This guide helps you verify that all robustness enhancements are working correctly.

---

## Prerequisites

1. **Python environment** with dependencies installed:
   ```bash
   cd services/ml-core
   pip install -r requirements.txt
   ```

2. **Chrome browser** with extension loaded

3. **Groq API key** configured in `.env`

---

## Test Suite 1: Python Backend Tests

### Run Automated Tests
```bash
cd services/ml-core
python -m pytest tests/test_robustness.py -v
```

**Expected output:**
```
test_robustness.py::TestErrorClassification::test_transient_errors_detected PASSED
test_robustness.py::TestErrorClassification::test_permanent_errors_detected PASSED
test_robustness.py::TestRetryConfig::test_exponential_backoff_delays PASSED
test_robustness.py::TestRetryConfig::test_max_delay_capped PASSED
test_robustness.py::TestLoopDetection::test_no_cycle_with_few_states PASSED
test_robustness.py::TestLoopDetection::test_oscillation_detected PASSED
test_robustness.py::TestLoopDetection::test_three_state_cycle_detected PASSED
... [more tests]
```

✅ **Pass criteria:** All tests pass without errors

---

## Test Suite 2: Error Recovery

### Test 2.1: LLM API Retry Logic

**Setup:**
1. Start the backend: `python -m app.main`
2. Temporarily modify `.env` to use an invalid API key
3. Open browser console on a LinkedIn Easy Apply job

**Execute:**
1. Click "Start" on the Career OS widget
2. Watch the widget status

**Expected behavior:**
- First error: "Backend error (1/5) ... retrying in 2s"
- Second error: "Backend error (2/5) ... retrying in 4s"
- Third error: "Backend error (3/5) ... retrying in 8s"
- Delays increase exponentially

**Recovery test:**
1. Restore the valid API key
2. Backend should reconnect automatically
3. Widget shows normal status

✅ **Pass criteria:** Exponential backoff observed, automatic recovery on fix

---

### Test 2.2: Network Timeout Handling

**Setup:**
1. Start backend
2. Disconnect network temporarily

**Execute:**
1. Start agent on a job page
2. Observe retry behavior

**Expected:**
- Agent retries with increasing delays
- "Backend error" message displayed
- No crash or freeze

**Recovery:**
1. Reconnect network
2. Agent resumes automatically

✅ **Pass criteria:** Graceful handling, auto-recovery

---

## Test Suite 3: Loop Detection

### Test 3.1: Oscillation Detection

**Create test scenario:**
```python
# In Python console or test script
from app.storage import detect_cycle_pattern, init_db

init_db()
session = "test_oscillation"

# Simulate A→B→A→B pattern
detect_cycle_pattern(session, "hash_a")
detect_cycle_pattern(session, "hash_b")
detect_cycle_pattern(session, "hash_a")
result = detect_cycle_pattern(session, "hash_b")

print(result)  # Should contain "oscillation"
```

✅ **Pass criteria:** Returns `"oscillation: hash_a↔hash_b"` or similar

---

### Test 3.2: 3-State Cycle Detection

```python
from app.storage import detect_cycle_pattern

session = "test_3cycle"

# Simulate A→B→C→A→B→C
for _ in range(2):
    detect_cycle_pattern(session, "hash_a")
    detect_cycle_pattern(session, "hash_b")
    result = detect_cycle_pattern(session, "hash_c")

print(result)  # Should contain "3-cycle"
```

✅ **Pass criteria:** Returns `"3-cycle: ..."` pattern

---

## Test Suite 4: Stale Element Recovery

### Test 4.1: Manual DOM Manipulation

**Setup:**
1. Start agent on a LinkedIn job
2. Open browser console

**Execute:**
```javascript
// Let agent start scanning
// After first scan, remove an element it's tracking
const btn = document.querySelector('button[aria-label="Submit application"]');
if (btn) {
    setTimeout(() => {
        btn.remove();
        console.log('Removed submit button');
    }, 2000);
}
```

**Expected behavior:**
- Agent attempts to click removed element
- Sees stale/detached error
- Retries up to 3 times
- Re-resolves element if it reappears
- OR escalates to user if permanently gone

✅ **Pass criteria:** No crashes, retry attempts visible, graceful fallback

---

## Test Suite 5: Telemetry Tracking

### Test 5.1: Stats API Endpoint

**Execute:**
```bash
# Start backend
cd services/ml-core
python -m app.main

# In another terminal, query stats
curl http://localhost:8000/api/stats?days=7
```

**Expected response:**
```json
{
  "period_days": 7,
  "total_sessions": 0,  // Initially zero
  "completed_sessions": 0,
  "completion_rate": 0,
  "avg_completion_time_seconds": 0,
  "total_errors": 0,
  "avg_errors_per_session": 0,
  "total_loops": 0,
  "loop_incident_rate": 0,
  "memory_hit_rate": 0,
  "avg_handoffs_per_session": 0
}
```

✅ **Pass criteria:** Endpoint returns valid JSON without errors

---

### Test 5.2: Live Telemetry Tracking

**Execute:**
1. Complete 2-3 LinkedIn Easy Apply applications
2. Query stats again: `curl http://localhost:8000/api/stats?days=1`

**Expected:**
- `total_sessions` increases
- `completed_sessions` shows successful applications
- `memory_hit_rate` shows percentage of zero-token field resolutions
- `avg_handoffs_per_session` shows human intervention frequency

**Verify in database:**
```bash
cd services/ml-core/app/data
sqlite3 career_os.db

# Check telemetry tables
SELECT COUNT(*) FROM telemetry_events;
SELECT * FROM session_metrics ORDER BY updated_at DESC LIMIT 5;
```

✅ **Pass criteria:** Data properly recorded, stats accurately reflect sessions

---

## Test Suite 6: Confidence Tiers

### Test 6.1: High Confidence Auto-Fill

**Monitor LLM responses:**
1. Add logging to `pipeline.py` to print confidence scores
2. Run through a job application
3. Observe which fields are auto-filled

**Expected:**
- Fields with confidence ≥0.85 fill immediately
- No user prompts for high-confidence fields
- Check logs for "confidence: 0.9" type messages

✅ **Pass criteria:** High-confidence fields auto-filled without handoff

---

### Test 6.2: Low Confidence Handling

**Test scenario:**
1. Encounter an unusual question (e.g., "What's your spirit animal?")
2. Observe LLM response

**Expected:**
- Low confidence (<0.40) triggers handoff
- User asked to provide answer
- Answer saved to memory for future use

✅ **Pass criteria:** Appropriate escalation, learning happens

---

## Test Suite 7: End-to-End Integration

### Test 7.1: Complete Application Flow

**Execute:**
1. Find a LinkedIn Easy Apply job
2. Click "Start" on Career OS widget
3. Let it run through completion

**Monitor:**
- Widget status updates
- No infinite loops
- Reasonable number of handoffs (<3)
- Successful submission

**Post-execution checks:**
```bash
# Check session metrics
curl http://localhost:8000/api/stats?days=1

# Check application record
curl http://localhost:8000/api/applications | grep submitted
```

✅ **Pass criteria:** 
- Application submitted successfully
- Metrics recorded correctly
- No crashes or freezes

---

### Test 7.2: Bulk Auto-Apply

**Setup:**
1. Set `BULK_APPLY_ENABLED: true` in `config.js`
2. Find LinkedIn job search results page

**Execute:**
1. Click "Start"
2. Watch as agent moves through multiple jobs

**Expected:**
- Completes first job
- Dismisses success modal
- Clicks next job card
- Starts fresh application
- Repeats until no more jobs or stopped

✅ **Pass criteria:** Sequential applications work smoothly

---

## Test Suite 8: Error Edge Cases

### Test 8.1: Rate Limiting

**Simulate:**
```python
# Mock 429 responses in test
# Or trigger real rate limit by rapid requests
```

**Expected:**
- Circuit breaker may open after repeated 429s
- Exponential backoff between retries
- Eventually defers to manual mode if persistent

✅ **Pass criteria:** Graceful degradation, no crash

---

### Test 8.2: Malformed LLM Response

**Setup:**
1. Temporarily modify `llm/client.py` to return invalid JSON
2. Trigger LLM call

**Expected:**
- JSON parsing fails safely
- Returns empty dict `{}`
- Falls back to ask_user
- Doesn't crash the loop

✅ **Pass criteria:** Safe failure, fallback works

---

## Regression Tests

### Ensure Original Features Still Work

- [ ] LinkedIn Easy Apply completes successfully
- [ ] Profile fields pre-filled from memory
- [ ] Resume upload works
- [ ] Manual handoffs can be resolved
- [ ] Dashboard shows applications
- [ ] Bulk apply progresses through jobs

---

## Performance Benchmarks

### Measure Impact

**Before enhancements (if you have baseline):**
- Average completion time: ?
- Token usage per application: ?

**After enhancements:**
```bash
# Run 10 applications and measure
curl http://localhost:8000/api/stats?days=1 | jq '.avg_completion_time_seconds'
```

**Expected:**
- Similar or better completion time
- Higher memory hit rate (fewer tokens)
- Fewer loops and errors

---

## Troubleshooting

### Tests fail with "No module named 'pytest'"
```bash
pip install pytest
```

### "Database is locked" errors
```bash
# Stop all backend instances
pkill -f "python -m app.main"
# Restart fresh
```

### Widget not showing up
1. Reload extension in Chrome
2. Hard refresh page (Ctrl+Shift+R)
3. Check browser console for errors

### Telemetry tables missing
```bash
cd services/ml-core
python -c "from app.telemetry import tracker; tracker._init_tables()"
```

---

## Success Checklist

After running all tests:

- [ ] All Python tests pass
- [ ] Error retry logic works with exponential backoff
- [ ] Loop detection catches cycles early
- [ ] Stale elements are re-resolved
- [ ] Telemetry tracks all events
- [ ] Stats API returns valid data
- [ ] Confidence tiers work as expected
- [ ] End-to-end application completes
- [ ] No regressions in existing features
- [ ] Performance is maintained or improved

---

## Reporting Issues

If any test fails:

1. **Capture logs:**
   - Backend: Terminal output
   - Frontend: Browser console
   - Database: `SELECT * FROM telemetry_events ORDER BY id DESC LIMIT 20;`

2. **Note details:**
   - Which test failed?
   - Error message
   - Steps to reproduce

3. **Check known issues:**
   - See `ROBUSTNESS_ENHANCEMENT_PLAN.md` Phase 2+ for known limitations

---

## Next Steps After Testing

Once all tests pass:
1. Deploy to production
2. Monitor telemetry stats daily
3. Review `/api/stats` weekly for trends
4. Plan Phase 2 enhancements based on data
5. Iterate on confidence thresholds based on real-world performance

Happy testing! 🚀
