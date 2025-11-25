# Daily Limit & Duplicate Prevention Guide

## Overview

The `auto_run.py` script now includes intelligent features to:

1. **Respect Gmail's daily sending limits** - Prevents hitting Gmail's 500 emails/day cap
2. **Avoid duplicate emails** - Skips universities that have already been contacted
3. **Resume where it left off** - Can be run multiple times to continue sending

## Features

### 1. Gmail Daily Limit Protection

Gmail has strict daily sending limits:

- **Free Gmail accounts**: 500 emails/day
- **Google Workspace**: 2,000 emails/day

The system is configured with a safe default of **450 emails/day** to avoid hitting the cap.

#### How it works:

- Tracks all emails sent **today** (resets at midnight)
- Before sending, checks how many emails can still be sent
- Stops automatically when the limit is reached
- Remaining universities are saved for the next run

### 2. Duplicate Prevention

The system ensures each university is only contacted once:

- **Checks before sending**: Skips universities that already have sent emails
- **Database tracking**: Uses the `email_campaigns` table to track status
- **Persistent state**: Works across multiple runs

### 3. Resume Capability

You can safely run `auto_run.py` multiple times:

- First run: Sends emails until daily limit is reached
- Second run (next day): Continues with remaining universities
- Subsequent runs: Only processes universities not yet contacted

## Configuration

### Setting Your Daily Limit

Edit your `.env` file or `config.py`:

```bash
# .env file
GMAIL_DAILY_LIMIT=450
```

Or in `config.py`:

```python
GMAIL_DAILY_LIMIT = int(os.getenv("GMAIL_DAILY_LIMIT", "450"))
```

**Recommended values:**

- Free Gmail: `450` (safe buffer below 500)
- Google Workspace: `1900` (safe buffer below 2000)

### Checking Your Current Status

Run the test script to see your current status:

```bash
python3 test_daily_limit.py
```

This shows:

- Emails sent today
- Remaining capacity
- Universities not yet contacted
- Database statistics

## Usage Examples

### Example 1: First Run (Fresh Start)

```bash
python3 auto_run.py
```

Output:

```
📊 DAILY LIMIT STATUS
================================================================================
Gmail Daily Limit:       450 emails/day
Emails Sent Today:       0
Remaining Today:         450
================================================================================

📨 Universities to contact: 150
⏭️  Universities skipped (already contacted): 0
📧 Total emails queued: 450
📧 Emails we can send today: 450
```

Result: Sends 450 emails, then stops

### Example 2: Second Run (Same Day)

```bash
python3 auto_run.py
```

Output:

```
📊 DAILY LIMIT STATUS
================================================================================
Gmail Daily Limit:       450 emails/day
Emails Sent Today:       450
Remaining Today:         0
================================================================================

⚠️  Daily email limit reached! No emails will be sent.
   Wait until tomorrow or increase GMAIL_DAILY_LIMIT in config.py
```

Result: No emails sent (limit reached)

### Example 3: Next Day Run

```bash
python3 auto_run.py
```

Output:

```
📊 DAILY LIMIT STATUS
================================================================================
Gmail Daily Limit:       450 emails/day
Emails Sent Today:       0
Remaining Today:         450
================================================================================

📨 Universities to contact: 100
⏭️  Universities skipped (already contacted): 150
📧 Total emails queued: 300
📧 Emails we can send today: 300
```

Result: Sends remaining 300 emails

## Monitoring & Statistics

### Check Current Status

```bash
python3 test_daily_limit.py
```

### View Database Statistics

```bash
python3 view_stats.py
```

### Check Today's Sent Count

```bash
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM email_campaigns WHERE status='SENT' AND DATE(sent_at) = DATE('now');"
```

### List Universities Not Yet Contacted

```python
from utils.db import Database

db = Database()
remaining = db.get_universities_without_sent_emails()
print(f"Universities remaining: {len(remaining)}")
for uni in remaining:
    print(f"  - {uni}")
db.close()
```

## How It Works Internally

### Database Schema

The `email_campaigns` table tracks all email operations:

```sql
CREATE TABLE email_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    sent_at DATETIME,              -- Timestamp when email was sent
    response_at DATETIME,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(university, email)
)
```

### Key Functions

#### `db.get_emails_sent_today()`

Counts emails with `status='SENT'` and `sent_at >= today's midnight`

#### `db.university_has_sent_emails(university)`

Returns `True` if any email to this university has `status='SENT'`

#### `db.get_universities_without_sent_emails()`

Returns list of universities with no sent emails

### Workflow

```
1. Start auto_run.py
   ↓
2. Check emails sent today
   ↓
3. Calculate remaining capacity
   ↓
4. If remaining > 0:
   ↓
5. For each university:
   - Check if already contacted
   - If not contacted and limit not reached:
     - Send emails
     - Update database
     - Increment counter
   ↓
6. Stop when limit reached or all done
```

## Best Practices

### 1. Run Daily at a Set Time

Set up a cron job or scheduled task:

```bash
# Run every day at 9 AM
0 9 * * * cd /path/to/project && ./venv/bin/python3 auto_run.py
```

### 2. Monitor Your Gmail Account

- Check Gmail's "Sent" folder regularly
- Watch for bounce-backs or errors
- Ensure you're not marked as spam

### 3. Adjust Throttling

If you're getting rate limited, increase delays in `config.py`:

```python
EMAIL_THROTTLE_DELAY = 60  # Increase to 60 seconds
```

### 4. Test Before Full Run

Use the test script first:

```bash
python3 test_daily_limit.py
```

### 5. Keep Backups

Backup your database regularly:

```bash
cp data/db.sqlite3 data/db_backup_$(date +%Y%m%d).sqlite3
```

## Troubleshooting

### Issue: "Daily limit reached" but I want to send more

**Solution**: Increase the limit in `.env`:

```bash
GMAIL_DAILY_LIMIT=500  # Or higher if you have Workspace
```

### Issue: Universities being contacted multiple times

**Solution**: Check if database is being cleared. The system only skips universities with `status='SENT'`. If emails are
failing, they won't be counted as sent.

### Issue: Script stops mid-run

**Solution**: The script automatically saves progress to the database. Just run it again - it will skip already-sent
emails.

### Issue: Want to reset and start over

**Solution**: Clear the database or set all statuses back to PENDING:

```bash
# Reset all to pending (careful!)
sqlite3 data/db.sqlite3 "UPDATE email_campaigns SET status='PENDING', sent_at=NULL WHERE status='SENT';"
```

## Summary

The enhanced `auto_run.py` now provides:

✅ **Automatic daily limit enforcement**  
✅ **Duplicate prevention across runs**  
✅ **Resume capability**  
✅ **Real-time progress tracking**  
✅ **Detailed logging and statistics**

You can now safely run the script multiple times without worrying about:

- Exceeding Gmail limits
- Sending duplicate emails
- Losing progress

Just run `python3 auto_run.py` whenever you want to continue the campaign!
