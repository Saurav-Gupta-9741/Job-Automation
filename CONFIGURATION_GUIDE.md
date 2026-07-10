# Career OS - Configuration Guide

Complete reference for all configuration options.

---

## Backend Configuration (.env)

Location: `services/ml-core/.env`

### Required Settings

```bash
# Groq API Key (REQUIRED)
GROQ_API_KEY=gsk_your_key_here

# Get your key at: https://console.groq.com/keys
```

### Optional LLM Settings

```bash
# Model to use (default: llama-3.1-8b-instant)
GROQ_MODEL=llama-3.1-8b-instant
# Other options: llama-3.1-70b-versatile, mixtral-8x7b-32768

# Tokens per minute budget (default: 5000)
GROQ_TPM_BUDGET=5000
# Groq free tier: 6000 TPM, keep below to avoid rate limits

# LLM failure threshold before circuit breaker opens (default: 3)
LLM_FAILURE_THRESHOLD=3
```

### Optional Resume Settings

```bash
# Path to your resume PDF (optional, for upload actions)
RESUME_PDF_PATH=/path/to/resume.pdf
```

### Optional Notification Settings

```bash
# Telegram notifications when agent needs help (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Behavior Flags

```bash
# Review before submit (default: false)
# Set to "true" to manually review each application before submission
REVIEW_BEFORE_SUBMIT=false

# CORS allowed origins (default: *)
ALLOWED_ORIGINS=*
```

---

## Frontend Configuration (config.js)

Location: `apps/extension/content/config.js`

### Timing & Pacing

```javascript
// Human-like delays between actions (milliseconds)
MIN_ACTION_DELAY_MS: 700,  // Minimum delay
MAX_ACTION_DELAY_MS: 1600, // Maximum delay
// Actual delay is random between min and max

// Delay after DOM mutations before re-scanning (milliseconds)
SETTLE_MS: 900,

// Idle polling interval (milliseconds)
IDLE_MS: 1500,
```

**Tuning Tips:**
- **Faster execution:** Lower MIN/MAX delays to 400-800ms
- **More human-like:** Increase to 1000-2000ms
- **LinkedIn rate limits:** Increase all delays by 50-100%

### Scanning Limits

```javascript
// Maximum elements to scan per step
MAX_ELEMENTS: 80,

// Maximum text characters per element
MAX_TEXT: 60,
```

**Tuning Tips:**
- **Complex pages:** Increase MAX_ELEMENTS to 120
- **Token optimization:** Decrease MAX_TEXT to 40
- **Full forms:** Increase both for comprehensive scanning

### Feature Flags

```javascript
// Automatically move to next job after completion
BULK_APPLY_ENABLED: true,

// Dry run mode: log actions without executing
DRY_RUN_MODE: false,
```

**Usage:**
- **Testing:** Set `DRY_RUN_MODE: true`
- **Manual applications:** Set `BULK_APPLY_ENABLED: false`
- **Mass applications:** Set `BULK_APPLY_ENABLED: true`

---

## Profile Configuration (profile.json)

Location: `services/ml-core/app/data/profile.json`

### Basic Information

```json
{
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "location": "San Francisco, CA",
  "city": "San Francisco",
  "country": "United States"
}
```

### Professional Links

```json
{
  "linkedin": "https://linkedin.com/in/johndoe",
  "github": "https://github.com/johndoe",
  "website": "https://johndoe.com"
}
```

### Work Information

```json
{
  "current_company": "TechCorp",
  "current_title": "Senior Software Engineer",
  "years_experience": "5",
  "desired_salary": "150000",
  "notice_period": "2 weeks"
}
```

### Work Authorization

```json
{
  "work_authorization": "Authorized to work in the United States",
  "requires_sponsorship": "No",
  "willing_to_relocate": "Yes"
}
```

### Diversity (Optional)

```json
{
  "gender": "Prefer not to say",
  "ethnicity": "Prefer not to say",
  "veteran_status": "Not a veteran",
  "disability_status": "No disability"
}
```

### Skills & Summary

```json
{
  "skills": [
    "Python", "JavaScript", "React", "Node.js",
    "AWS", "Docker", "PostgreSQL", "Git"
  ],
  "summary": "Experienced software engineer with 5 years in web development...",
  "raw_text": "Full resume text for LLM context..."
}
```

**Tips:**
- Keep `summary` under 500 characters
- Include top 10-20 skills only
- `raw_text` can be full resume for context

---

## Database Configuration

Location: `services/ml-core/app/data/career_os.db`

### Automatic Initialization

The database auto-initializes on first run. No configuration needed.

### Manual Reset

```bash
cd services/ml-core/app/data
rm career_os.db
# Restart backend to recreate
```

### Backup

```bash
cd services/ml-core/app/data
cp career_os.db career_os_backup_$(date +%Y%m%d).db
```

---

## Advanced Configuration

### Custom Field Synonyms

Edit: `services/ml-core/app/resume/profile.py`

Add custom mappings in `_FIELD_SYNONYMS`:

```python
_FIELD_SYNONYMS = [
    # Your custom mappings
    (["preferred name", "nickname"], "first_name"),
    (["mobile number"], "phone"),
    # ... existing mappings
]
```

### Custom Adapter for New ATS

Create: `services/ml-core/app/adapters/myats.py`

```python
from .base import Adapter
from ..schemas import Action, ActionType

class MyATSAdapter(Adapter):
    name = "myats"
    
    def matches(self, url: str) -> bool:
        return "myats.com" in url
    
    def plan(self, req, profile):
        # Your custom logic
        return None  # Fall through to generic
```

Register in `services/ml-core/app/planner/router.py`:

```python
from ..adapters.myats import MyATSAdapter

_FINGERPRINTS = [
    (["myats.com"], MyATSAdapter()),
    # ... existing adapters
]
```

---

## Performance Tuning

### For Speed

```bash
# .env
GROQ_MODEL=llama-3.1-8b-instant  # Fastest model
GROQ_TPM_BUDGET=5000

# config.js
MIN_ACTION_DELAY_MS: 400
MAX_ACTION_DELAY_MS: 800
SETTLE_MS: 600
```

### For Accuracy

```bash
# .env
GROQ_MODEL=llama-3.1-70b-versatile  # More accurate
REVIEW_BEFORE_SUBMIT=true  # Manual review

# config.js
MIN_ACTION_DELAY_MS: 1000
MAX_ACTION_DELAY_MS: 2000
SETTLE_MS: 1200
```

### For Stealth

```bash
# config.js
MIN_ACTION_DELAY_MS: 1200
MAX_ACTION_DELAY_MS: 2500
SETTLE_MS: 1500
BULK_APPLY_ENABLED: false  # Slower application rate
```

---

## Troubleshooting Configurations

### Issue: Too Many Rate Limits

**Solution:**
```javascript
// Increase delays significantly
MIN_ACTION_DELAY_MS: 2000
MAX_ACTION_DELAY_MS: 4000
SETTLE_MS: 2000
BULK_APPLY_ENABLED: false
```

### Issue: Missing Fields

**Solution:**
```javascript
// Scan more elements
MAX_ELEMENTS: 120
MAX_TEXT: 80

// Wait longer for DOM
SETTLE_MS: 1500
```

### Issue: LLM Errors

**Solution:**
```bash
# Check budget
GROQ_TPM_BUDGET=4500  # Lower to avoid spikes

# Increase threshold
LLM_FAILURE_THRESHOLD=5
```

### Issue: Wrong Field Values

**Solution:**
1. Check `profile.json` has correct values
2. Add custom synonyms in `profile.py`
3. Enable `REVIEW_BEFORE_SUBMIT=true`

---

## Environment-Specific Configs

### Development

```bash
# .env
REVIEW_BEFORE_SUBMIT=true
GROQ_TPM_BUDGET=3000  # Conservative

# config.js
DRY_RUN_MODE: true  # Test without actions
BULK_APPLY_ENABLED: false
```

### Testing

```bash
# .env
REVIEW_BEFORE_SUBMIT=true
GROQ_TPM_BUDGET=5000

# config.js
DRY_RUN_MODE: false
BULK_APPLY_ENABLED: false
MIN_ACTION_DELAY_MS: 500
```

### Production

```bash
# .env
REVIEW_BEFORE_SUBMIT=false  # Fully autonomous
GROQ_TPM_BUDGET=5000

# config.js
DRY_RUN_MODE: false
BULK_APPLY_ENABLED: true
MIN_ACTION_DELAY_MS: 800
MAX_ACTION_DELAY_MS: 1600
```

---

## Configuration Validation

### Check Backend Config

```bash
cd services/ml-core
curl http://127.0.0.1:8000/health
```

Expected output includes your current configuration:
```json
{
  "ok": true,
  "tokens_spent_60s": 0,
  "tpm_budget": 5000,
  "circuit_open": false
}
```

### Check Frontend Config

Open browser console on any page:
```javascript
console.log(window.COS.CONFIG);
```

### Verify Profile Loaded

```bash
curl http://127.0.0.1:8000/api/profile
```

---

## Best Practices

### 1. Start Conservative
- Enable `REVIEW_BEFORE_SUBMIT`
- Use `DRY_RUN_MODE` for first tests
- Lower `GROQ_TPM_BUDGET` initially

### 2. Monitor & Adjust
- Check `/api/stats` regularly
- Adjust delays based on rate limits
- Increase budget if often waiting

### 3. Profile Completeness
- Fill all profile fields accurately
- Add common variations to synonyms
- Keep skills list updated

### 4. Regular Backups
- Backup database weekly
- Export applications to CSV monthly
- Save profile.json to version control

---

## Configuration Checklist

Before going live:

- [ ] `GROQ_API_KEY` set and valid
- [ ] `profile.json` complete and accurate
- [ ] `REVIEW_BEFORE_SUBMIT` configured as desired
- [ ] Delays tuned for your needs
- [ ] `BULK_APPLY_ENABLED` set appropriately
- [ ] Resume PDF staged (if using uploads)
- [ ] Backend health check passes
- [ ] Extension loads without errors
- [ ] Test on 1-2 jobs first
- [ ] Monitor telemetry for issues

---

**Configuration complete!** Start with conservative settings and tune based on real-world results.
