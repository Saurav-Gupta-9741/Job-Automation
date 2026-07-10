# Command Reference - Quick Command Sheet

## All Commands for Career OS in One Place

---

## 🚀 Setup Commands

### Initial Setup
```bash
# Automated setup (recommended)
setup.bat

# Manual setup
cd services\ml-core
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Configuration
```bash
# Edit environment variables
notepad services\ml-core\.env

# Edit profile data
notepad services\ml-core\app\data\profile.json

# Edit extension config
notepad apps\extension\content\config.js
```

---

## 🏃 Running Commands

### Start Backend
```bash
# Quick start
start.bat

# Manual start
cd services\ml-core
.venv\Scripts\activate
python -m app.main

# With log output
python -m app.main 2>&1 | tee output.log
```

### Load Extension
```
1. Open Chrome
2. Go to chrome://extensions
3. Enable "Developer mode"
4. Click "Load unpacked"
5. Select: apps\extension\
```

---

## 🧪 Testing Commands

### Automated Tests
```bash
# Run all tests
test.bat

# Run Python tests only
cd services\ml-core
.venv\Scripts\activate
pytest tests\test_robustness.py -v

# Run specific test
pytest tests\test_robustness.py::test_error_classification -v

# Run with coverage
pytest --cov=app tests\test_robustness.py
```

### Manual Testing
```javascript
// In browser console

// Check extension loaded
window.COS

// Manual scan
COS.Scanner.scan()

// Check current state
COS.State.load()

// Force widget mount
COS.Widget.mount()
```

---

## 📊 Monitoring Commands

### Real-Time Monitoring
```bash
# Live monitor (auto-refresh)
monitor.bat

# One-time health check
curl http://localhost:8000/health

# One-time stats
curl http://localhost:8000/api/stats?days=1
```

### View Statistics
```bash
# Last 24 hours
curl http://localhost:8000/api/stats?days=1

# Last 7 days
curl http://localhost:8000/api/stats?days=7

# All time
curl http://localhost:8000/api/stats?days=9999

# Specific session
curl "http://localhost:8000/api/stats?session=sess-abc123"
```

### View Applications
```bash
# All applications (JSON)
curl http://localhost:8000/api/applications

# Pretty print
curl http://localhost:8000/api/applications | python -m json.tool

# Count applications
curl -s http://localhost:8000/api/applications | findstr "session_id" | find /c "session_id"
```

---

## 💾 Database Commands

### Query Database
```bash
# Open database
cd services\ml-core\app\data
sqlite3 career_os.db

# Inside SQLite:
.tables                           # List tables
.schema applications              # Show table structure
SELECT * FROM applications;       # View all applications
SELECT * FROM field_memory LIMIT 10;  # View learned answers
SELECT COUNT(*) FROM applications;    # Count apps
.quit                             # Exit
```

### Common Queries
```sql
-- Applications submitted
SELECT COUNT(*) FROM applications WHERE submitted=1;

-- Most used answers
SELECT q_raw, answer, uses 
FROM field_memory 
ORDER BY uses DESC 
LIMIT 10;

-- Applications by date
SELECT DATE(created_at) as date, COUNT(*) as count 
FROM applications 
GROUP BY DATE(created_at);

-- Success rate
SELECT 
  COUNT(*) as total,
  SUM(submitted) as submitted,
  (SUM(submitted)*100.0/COUNT(*)) as success_rate
FROM applications;
```

---

## 🔧 Maintenance Commands

### Backup & Restore
```bash
# Create backup
backup.bat

# Restore from backup
restore.bat

# Manual backup
copy services\ml-core\app\data\career_os.db backups\backup_%date%.db
```

### Clean Up
```bash
# Automated cleanup
clean.bat

# Manual cleanup
del /s /q services\ml-core\__pycache__
del services\ml-core\career_os.log
```

### Update Dependencies
```bash
cd services\ml-core
.venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

---

## 🐛 Diagnostic Commands

### System Health
```bash
# Full diagnostic
diagnose.bat

# Check Python
python --version

# Check port 8000
netstat -ano | findstr :8000

# Check disk space
dir /-c
```

### View Logs
```bash
# View all logs
type services\ml-core\career_os.log

# Last 20 lines
powershell -command "Get-Content services\ml-core\career_os.log -Tail 20"

# Search for errors
findstr "ERROR" services\ml-core\career_os.log

# Search for specific text
findstr "YOUR_SEARCH" services\ml-core\career_os.log
```

### Network Tests
```bash
# Test backend
curl http://localhost:8000/health

# Test Groq API
curl https://api.groq.com/openai/v1/models

# Check internet
ping console.groq.com
```

---

## 📤 Export Commands

### Generate Reports
```bash
# Full report
export_report.bat

# Manual CSV export
curl http://localhost:8000/api/export/csv > applications.csv

# Stats to file
curl http://localhost:8000/api/stats?days=30 > stats.json
```

---

## 🔄 Reset Commands

### Soft Reset (Keep Data)
```bash
# Restart backend
# In backend terminal: Ctrl+C
python -m app.main

# Reload extension
# chrome://extensions → Click reload icon

# Clear browser cache
# Ctrl+Shift+Delete in Chrome
```

### Hard Reset (Clear All)
```bash
# ⚠️  WARNING: Deletes all data!

# Stop backend
# Ctrl+C in terminal

# Delete database
del services\ml-core\app\data\career_os.db

# Delete logs
del services\ml-core\career_os.log

# Restart
python -m app.main
```

---

## 🎮 Browser Console Commands

### Extension Control
```javascript
// Check loaded
window.COS

// Start application
COS.Agent.start()

// Stop application
COS.State.stop()

// Get current state
await COS.State.load()

// Manual scan
await COS.Scanner.scan()

// Check config
COS.CONFIG
```

### Debugging
```javascript
// Enable debug logs
localStorage.setItem('COS_DEBUG', 'true')

// Disable debug logs
localStorage.removeItem('COS_DEBUG')

// Check widget
document.querySelector('.cos-widget')

// Find elements by type
await COS.Scanner.scan().then(els => 
  els.filter(e => e.tag === 'input')
)

// Find by text
await COS.Scanner.scan().then(els =>
  els.filter(e => e.text?.includes('email'))
)
```

---

## 🌐 API Endpoints

### Health & Status
```
GET http://localhost:8000/health
GET http://localhost:8000/
```

### Agent Operations
```
POST http://localhost:8000/api/agent/step
Body: { session_id, url, elements, history }

POST http://localhost:8000/api/agent/handoff
Body: { session_id, question, answer }
```

### Data Retrieval
```
GET http://localhost:8000/api/stats?days=7
GET http://localhost:8000/api/stats?session=sess-123
GET http://localhost:8000/api/applications
GET http://localhost:8000/api/export/csv
```

---

## 🔑 Environment Variables

### Required (.env)
```bash
GROQ_API_KEY=gsk_your_key_here
```

### Optional (.env)
```bash
GROQ_MODEL=llama-3.1-8b-instant
GROQ_TPM_BUDGET=5000
REVIEW_BEFORE_SUBMIT=true
DRY_RUN_MODE=false
```

---

## ⚙️ Config File Locations

```
Project Root
├── .env                              # Not in repo
├── services/ml-core/
│   ├── .env                          # Backend config
│   ├── app/
│   │   ├── config.py                 # Python config
│   │   └── data/
│   │       ├── profile.json          # Your profile
│   │       └── career_os.db          # Database
│   └── career_os.log                 # Backend logs
└── apps/extension/
    ├── manifest.json                 # Extension metadata
    └── content/
        └── config.js                 # Frontend config
```

---

## 📋 Common Workflows

### Daily Use
```bash
# 1. Start system
start.bat

# 2. Open Chrome, load extension (if not loaded)

# 3. Go to LinkedIn jobs

# 4. Click "Apply on this page"

# 5. Check results
curl http://localhost:8000/api/stats?days=1
```

### Weekly Maintenance
```bash
# 1. Backup database
backup.bat

# 2. Check logs
type services\ml-core\career_os.log | findstr "ERROR"

# 3. Export report
export_report.bat

# 4. Clean old files
clean.bat
```

### Before Testing
```bash
# 1. Run diagnostics
diagnose.bat

# 2. Enable dry run
# Edit config.js: DRY_RUN_MODE: true

# 3. Start monitoring
monitor.bat

# 4. Run tests
test.bat
```

---

## 🆘 Emergency Commands

### System Not Responding
```bash
# Kill all Python
taskkill /IM python.exe /F

# Kill port 8000
for /f "tokens=5" %a in ('netstat -ano ^| findstr :8000') do taskkill /F /PID %a

# Restart fresh
start.bat
```

### Database Issues
```bash
# Check database integrity
cd services\ml-core\app\data
sqlite3 career_os.db "PRAGMA integrity_check;"

# Repair database
sqlite3 career_os.db "VACUUM;"

# Rebuild from backup
copy backups\latest_backup.db career_os.db
```

---

## 📚 Documentation Commands

### View Documentation
```bash
# Main README
type README.md | more

# Quick reference
type QUICK_REFERENCE.md | more

# Testing guide
type LINKEDIN_TESTING_GUIDE.md | more

# All markdown files
dir *.md /b
```

---

**Bookmark this page for quick access to all commands!**

**Most used commands:**
- `start.bat` - Start backend
- `test.bat` - Run tests  
- `diagnose.bat` - Check health
- `backup.bat` - Backup data
- `monitor.bat` - Live monitoring

---

*Complete command reference for Career OS autonomous job application agent.*
