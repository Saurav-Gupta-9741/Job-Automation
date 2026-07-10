# Career OS - Quick Reference Card

## 🚀 Quick Start Commands

### Start Backend
```bash
cd services/ml-core
.venv\Scripts\activate  # or source .venv/bin/activate on Unix
python -m app.main
```

### Run Tests
```bash
cd services/ml-core
pytest tests/test_robustness.py -v
```

### View Stats
```bash
curl http://localhost:8000/api/stats?days=7
```

### Load Extension
1. Chrome → `chrome://extensions`
2. Enable "Developer mode"
3. "Load unpacked" → `apps/extension/`

---

## 🔧 Configuration Files

### Backend: `services/ml-core/.env`
```bash
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TPM_BUDGET=5000
REVIEW_BEFORE_SUBMIT=false
```

### Frontend: `apps/extension/content/config.js`
```javascript
BULK_APPLY_ENABLED: true,
MIN_ACTION_DELAY_MS: 800,
MAX_ACTION_DELAY_MS: 1800
```

---

## 📊 Key Metrics & Targets

| Metric | Target | Check Via |
|--------|--------|-----------|
| Completion Rate | >85% | `/api/stats` |
| Error Rate | <3% | `/api/stats` |
| Loop Incidents | <1% | `/api/stats` |
| Memory Hit Rate | >50% | `/api/stats` |
| Handoffs/Session | <2 | `/api/stats` |

---

## 🐛 Common Issues

### Backend won't start
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Unix

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Unix
```

### Extension not appearing
1. Hard refresh: `Ctrl+Shift+R`
2. Check console for errors: `F12`
3. Reload extension in `chrome://extensions`

### Database locked
```bash
# Stop all backend instances
pkill -f "python -m app.main"  # Unix
# Manually check Task Manager on Windows
```

### LLM rate limited
- Check `/api/stats` for `total_llm_calls`
- Increase `GROQ_TPM_BUDGET` if under limit
- Consider slowing down with higher `MIN_ACTION_DELAY_MS`

---

## 📁 Important Files

### Core Logic
- `services/ml-core/app/planner/pipeline.py` - Main decision cascade
- `services/ml-core/app/adapters/linkedin.py` - LinkedIn state machine
- `apps/extension/content/agent.js` - Orchestrator loop
- `apps/extension/content/executor.js` - DOM actions

### New Robustness Features
- `services/ml-core/app/llm/client.py` - Retry logic
- `services/ml-core/app/storage.py` - Loop detection
- `services/ml-core/app/telemetry.py` - Metrics tracking

### Database
- `services/ml-core/app/data/career_os.db` - SQLite database
- Tables: `applications`, `field_memory`, `stage_counts`, `state_transitions`, `telemetry_events`, `session_metrics`

---

## 🔍 Debugging Tips

### Check agent status
```javascript
// In browser console
window.COS.State.isRunning()
window.COS.State.session
```

### View recent applications
```bash
curl http://localhost:8000/api/applications | jq '.[:5]'
```

### Check database directly
```bash
cd services/ml-core/app/data
sqlite3 career_os.db

-- View recent sessions
SELECT * FROM session_metrics ORDER BY updated_at DESC LIMIT 5;

-- View error events
SELECT * FROM telemetry_events WHERE event_type='error' ORDER BY id DESC LIMIT 10;

-- View loop incidents
SELECT * FROM telemetry_events WHERE event_type='loop' ORDER BY id DESC;
```

### Backend logs
```bash
# Add logging to pipeline.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 📖 Documentation Quick Links

- **Architecture:** `architecture-blueprint.md`
- **Enhancement Plan:** `ROBUSTNESS_ENHANCEMENT_PLAN.md`
- **What's Implemented:** `ROBUSTNESS_IMPLEMENTATION_SUMMARY.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Visual Overview:** `ENHANCEMENTS_OVERVIEW.md`

---

## 🎯 Workflow Cheatsheet

### First-time Setup
1. Clone repo
2. Create `.env` from `.env.example`
3. Add `GROQ_API_KEY`
4. Install Python dependencies
5. Load extension in Chrome
6. Start backend
7. Run tests

### Daily Use
1. Start backend: `python -m app.main`
2. Open LinkedIn job search
3. Click "Start" on widget
4. Monitor progress
5. Check stats: `curl http://localhost:8000/api/stats`

### Development Cycle
1. Make changes
2. Run tests: `pytest tests/test_robustness.py -v`
3. Test manually on LinkedIn
4. Check telemetry data
5. Iterate

---

## 🆘 Getting Help

### Check logs
- Backend: Terminal output
- Frontend: Browser console (`F12`)
- Database: SQLite queries

### Review documentation
- Read `architecture-blueprint.md` for system understanding
- Check `TESTING_GUIDE.md` for test scenarios
- See `ROBUSTNESS_ENHANCEMENT_PLAN.md` for known limitations

### Debug process
1. Identify which component failed (perceive/think/act)
2. Check relevant logs
3. Verify configuration
4. Run isolated tests
5. Check telemetry events

---

## 🔐 Security Notes

- Never commit `.env` file
- API keys are stored in `.env` only
- No credentials in browser storage
- CORS configured for `localhost` only

---

## 📝 Quick SQL Queries

### Top 5 most resolved fields (memory)
```sql
SELECT q_raw, answer, uses, confidence 
FROM field_memory 
ORDER BY uses DESC 
LIMIT 5;
```

### Recent errors by type
```sql
SELECT json_extract(details, '$.error_type') as error_type, COUNT(*) 
FROM telemetry_events 
WHERE event_type='error' 
GROUP BY error_type;
```

### Sessions with loops
```sql
SELECT session_id, loops, handoffs 
FROM session_metrics 
WHERE loops > 0 
ORDER BY updated_at DESC;
```

### LLM efficiency per session
```sql
SELECT 
    session_id,
    memory_hits,
    llm_calls,
    ROUND(CAST(memory_hits AS FLOAT) / (memory_hits + llm_calls) * 100, 1) as hit_rate
FROM session_metrics
WHERE (memory_hits + llm_calls) > 0
ORDER BY hit_rate DESC;
```

---

## ⚡ Performance Tips

1. **Increase memory hit rate:** Manually answer uncommon questions once
2. **Reduce LLM calls:** Build better adapters for your target ATSs
3. **Speed up execution:** Lower `MIN_ACTION_DELAY_MS` (carefully)
4. **Avoid loops:** Review state transitions for problem patterns
5. **Monitor telemetry:** Check `/api/stats` regularly for trends

---

## 📞 Support Channels

- **Issues:** GitHub issues
- **Discussions:** GitHub discussions
- **Documentation:** All `.md` files in repo root

---

**Last Updated:** Phase 1 Implementation Complete
**Version:** 6.0 (Robustness Enhanced)
