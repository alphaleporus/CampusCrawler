# Quick Reference - Daily Limit Features

## 🚀 Quick Commands

### Check Current Status

```bash
python3 test_daily_limit.py
```

Shows: Daily limit status, emails sent today, universities remaining

### Run Email Campaign

```bash
python3 auto_run.py
```

Automatically sends emails respecting daily limit and skipping already-contacted universities

### View Database Stats

```bash
python3 view_stats.py
```

### Check Emails Sent Today (SQL)

```bash
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM email_campaigns WHERE status='SENT' AND DATE(sent_at) = DATE('now');"
```

## ⚙️ Configuration

### Set Daily Limit

**In `.env` file:**

```bash
GMAIL_DAILY_LIMIT=450
```

**Recommended Values:**

- Free Gmail: `450` (safe)
- Google Workspace: `1900` (safe)
- Testing: `10`

## 📊 Key Numbers

| Account Type | Official Limit | Recommended Setting |
|-------------|---------------|---------------------|
| Free Gmail | 500/day | 450/day |
| Google Workspace | 2000/day | 1900/day |

## 🔍 Status Checks

### Current Database State

```python
from utils.db import Database

db = Database()

# Emails sent today
today_count = db.get_emails_sent_today()
print(f"Sent today: {today_count}")

# Universities remaining
remaining = db.get_universities_without_sent_emails()
print(f"Universities remaining: {len(remaining)}")

# Overall stats
stats = db.get_statistics()
print(f"Stats: {stats}")

db.close()
```

### Quick SQL Queries

**Universities already contacted:**

```bash
sqlite3 data/db.sqlite3 "SELECT DISTINCT university FROM email_campaigns WHERE status='SENT' ORDER BY university;"
```

**Universities not yet contacted:**

```bash
sqlite3 data/db.sqlite3 "SELECT DISTINCT university FROM email_campaigns WHERE university NOT IN (SELECT DISTINCT university FROM email_campaigns WHERE status='SENT') ORDER BY university;"
```

**Emails sent today:**

```bash
sqlite3 data/db.sqlite3 "SELECT university, email, sent_at FROM email_campaigns WHERE status='SENT' AND DATE(sent_at) = DATE('now');"
```

## 🎯 Common Workflows

### Daily Campaign Run

```bash
# Morning: Check status
python3 test_daily_limit.py

# If capacity available: Run campaign
python3 auto_run.py

# Monitor logs
tail -f *.log
```

### Reset for Testing

```bash
# Backup first!
cp data/db.sqlite3 data/db_backup.sqlite3

# Reset sent status (CAREFUL!)
sqlite3 data/db.sqlite3 "UPDATE email_campaigns SET status='PENDING', sent_at=NULL WHERE status='SENT';"
```

### Check Progress Mid-Run

```bash
# In another terminal while auto_run.py is running
watch -n 5 'python3 test_daily_limit.py'
```

## 🛡️ Safety Features

✅ **Automatic Stopping** - Stops at daily limit  
✅ **Duplicate Prevention** - Never contacts same university twice  
✅ **Resume Capability** - Can run multiple times safely  
✅ **Database Tracking** - All actions logged

## ⚠️ Important Notes

1. **Daily limit resets at midnight** (system time)
2. **Universities are skipped if ANY email was sent** (Primary, Secondary, or Tertiary)
3. **Running auto_run.py multiple times same day is safe** (will skip if limit reached)
4. **Database must not be deleted** between runs (contains state)

## 🔧 Troubleshooting

### Problem: "Daily limit reached" but I want to continue

**Solution:**

```bash
# Option 1: Increase limit (if you have Workspace)
echo "GMAIL_DAILY_LIMIT=1900" >> .env

# Option 2: Wait until tomorrow
```

### Problem: Want to re-send to a university

**Solution:**

```bash
# Find the university emails
sqlite3 data/db.sqlite3 "SELECT * FROM email_campaigns WHERE university='University Name';"

# Change status back to PENDING (CAREFUL!)
sqlite3 data/db.sqlite3 "UPDATE email_campaigns SET status='PENDING', sent_at=NULL WHERE university='University Name';"
```

### Problem: Script seems to skip too many universities

**Solution:**

```bash
# Check how many universities have been contacted
python3 -c "from utils.db import Database; db = Database(); print(f'Already contacted: {len([u for u in db.get_statistics()])}'); db.close()"
```

## 📈 Monitoring Dashboard (Terminal)

Create a simple monitoring script:

```python
#!/usr/bin/env python3
# monitor.py
import time
from utils.db import Database
import config

while True:
    db = Database()
    today = db.get_emails_sent_today()
    limit = config.GMAIL_DAILY_LIMIT
    remaining_unis = len(db.get_universities_without_sent_emails())
    
    print(f"\r📧 Sent: {today}/{limit} | 🎓 Remaining Unis: {remaining_unis}", end='', flush=True)
    
    db.close()
    time.sleep(5)
```

Usage:

```bash
python3 monitor.py
```

## 📝 Log Files

All operations are logged. Check logs:

```bash
# View recent logs
tail -f logs/*.log

# Search for errors
grep -i error logs/*.log

# Count successes
grep -i "successfully sent" logs/*.log | wc -l
```

## 🎯 Best Practices

1. ✅ **Run test_daily_limit.py before auto_run.py**
2. ✅ **Backup database regularly:** `cp data/db.sqlite3 backups/db_$(date +%Y%m%d).sqlite3`
3. ✅ **Monitor Gmail account for bounces**
4. ✅ **Keep limit below official cap** (use 450 for Gmail free)
5. ✅ **Run at consistent times** (e.g., 9 AM daily)

## 🔗 Related Files

- `DAILY_LIMIT_GUIDE.md` - Comprehensive documentation
- `CHANGELOG_DAILY_LIMIT.md` - Technical changes
- `README.md` - Main project README
- `config.py` - Configuration settings
- `test_daily_limit.py` - Status checking script

## 💡 Pro Tips

- Use `watch -n 10 python3 test_daily_limit.py` for live monitoring
- Set up cron job: `0 9 * * * cd /path && ./venv/bin/python3 auto_run.py`
- Keep `.env` file backed up (contains credentials)
- Export stats regularly: `python3 view_stats.py > stats_$(date +%Y%m%d).txt`

---

**Last Updated:** November 18, 2025  
**Version:** 1.0
