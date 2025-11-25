# Gmail Limit Error Handling

## Overview

The system now automatically detects when Gmail's daily sending limit is exceeded and **gracefully exits** instead of
continuing to retry.

## What Happens When Limit is Reached

### 1. **Error Detection**

When Gmail rejects an email with error code `550 5.4.5` (Daily user sending limit exceeded), the system:

- ✅ Immediately stops sending
- ✅ Saves all progress to database
- ✅ Displays a clear error message
- ✅ Provides actionable next steps
- ✅ Exits with code 2 (distinct from other errors)

### 2. **Error Message**

You'll see:

```
🛑 GMAIL DAILY LIMIT EXCEEDED
================================================================================
Gmail has rejected further emails: Gmail daily sending limit exceeded
Emails sent in this run: 42
Total sent (24h): 503/450

IMPORTANT NOTES:
  • Gmail enforces a rolling 24-hour limit
  • Your account may have been flagged for bulk sending
  • All progress has been saved to the database

RECOMMENDED ACTIONS:
  1. Wait 24-48 hours before trying again
  2. Reduce GMAIL_DAILY_LIMIT in .env (try 200 instead of 450)
  3. Increase EMAIL_THROTTLE_DELAY in .env (try 60+ seconds)
  4. Check your Gmail Sent folder for other email activity

To check when you can send again:
  python3 check_send_time.py
================================================================================
```

### 3. **No Data Loss**

- All successfully sent emails are marked as `SENT` in database
- Universities already contacted won't be contacted again
- Failed email is marked as `FAILED` with error message
- You can safely resume later

## Why This Happens

### Common Causes

1. **Exceeded Gmail's Official Limit**
    - Free Gmail: 500 emails/day
    - Google Workspace: 2,000 emails/day

2. **Rolling 24-Hour Window**
    - Gmail counts emails sent in the LAST 24 hours
    - Not calendar day (midnight to midnight)
    - Emails from yesterday still count if within 24 hours

3. **Burst Sending Detection**
    - Sending too many emails too quickly
    - Gmail may flag as automated/bulk sending
    - Account reputation matters

4. **Other Email Activity**
    - Manual emails from Gmail web interface
    - Emails sent from mobile app
    - Other scripts using same account

## How to Prevent

### 1. Lower Your Daily Limit

Edit `.env`:

```bash
# Conservative limit (recommended)
GMAIL_DAILY_LIMIT=200

# Very conservative (if account flagged)
GMAIL_DAILY_LIMIT=100
```

### 2. Increase Throttling

Edit `.env`:

```bash
# Slower sending = better reputation
EMAIL_THROTTLE_DELAY=60
EMAIL_JITTER_MIN=10
EMAIL_JITTER_MAX=20
```

### 3. Monitor Before Running

Always check status first:

```bash
# Check current capacity
python3 check_send_time.py

# Check database status
python3 test_daily_limit.py

# Then run
python3 auto_run.py
```

### 4. Gradual Increase

Start with small limits and increase gradually:

- Day 1-3: GMAIL_DAILY_LIMIT=100
- Day 4-7: GMAIL_DAILY_LIMIT=200
- Day 8+: GMAIL_DAILY_LIMIT=300-400

## What To Do When It Happens

### Step 1: Don't Panic

- This is normal for bulk sending
- Your account is not banned
- All progress is saved
- Just need to wait

### Step 2: Check Status

```bash
python3 check_send_time.py
```

This shows:

- Emails sent in last 24 hours
- When capacity will be available
- How long to wait

### Step 3: Wait

Gmail's limit is a rolling 24-hour window. Wait at least:

- **Minimum**: Until oldest emails are 24+ hours old
- **Recommended**: 24-48 hours
- **If flagged**: 48-72 hours

### Step 4: Adjust Settings

Before resuming, lower your limits:

```bash
# Edit .env
GMAIL_DAILY_LIMIT=200
EMAIL_THROTTLE_DELAY=60
```

### Step 5: Resume

```bash
# Check capacity
python3 check_send_time.py

# If shows capacity, resume
python3 auto_run.py
```

## Technical Details

### Exception Flow

```
1. Gmail rejects email with 550 5.4.5 error
   ↓
2. EmailSender detects error pattern
   ↓
3. Raises GmailDailyLimitError (no retry)
   ↓
4. send_university_emails catches and breaks loop
   ↓
5. run_send_emails_async catches and displays message
   ↓
6. main() catches and exits with code 2
```

### Exit Codes

- **0**: Success - all emails sent
- **1**: General error (network, config, etc.)
- **2**: Gmail daily limit reached
- **130**: User interrupted (Ctrl+C)

### Database Status

When limit error occurs:

- Last attempted email: `STATUS='FAILED'`
- Error message: Contains "Gmail daily limit"
- All previous emails: `STATUS='SENT'` (if successful)
- University: Will be skipped on next run if any email sent

## Monitoring

### Real-time Monitoring

In one terminal:

```bash
python3 auto_run.py
```

In another terminal:

```bash
watch -n 30 python3 check_send_time.py
```

### Check Logs

```bash
# Search for limit errors
grep -i "daily limit" logs/*.log

# Count successful sends
grep -i "successfully sent" logs/*.log | wc -l

# Check recent errors
tail -50 logs/latest.log | grep ERROR
```

### Database Queries

```bash
# Count by status
sqlite3 data/db.sqlite3 "SELECT status, COUNT(*) FROM email_campaigns GROUP BY status;"

# Recent failures
sqlite3 data/db.sqlite3 "SELECT university, email, error FROM email_campaigns WHERE status='FAILED' ORDER BY updated_at DESC LIMIT 10;"

# Emails sent today
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM email_campaigns WHERE status='SENT' AND DATE(sent_at) = DATE('now');"
```

## Best Practices

### Daily Routine

```bash
# Morning: Check status
python3 check_send_time.py

# If capacity available: Run campaign
python3 auto_run.py

# If limit reached: Will auto-exit, try tomorrow
```

### Multi-Day Campaigns

```bash
# Day 1
GMAIL_DAILY_LIMIT=200 python3 auto_run.py

# Day 2
python3 check_send_time.py  # Verify capacity
python3 auto_run.py          # Resume automatically

# Day 3
python3 auto_run.py          # Continue until all done
```

### Safety Settings

```bash
# .env for safe operation
GMAIL_DAILY_LIMIT=200
EMAIL_THROTTLE_DELAY=60
EMAIL_JITTER_MIN=10
EMAIL_JITTER_MAX=20
EMAIL_MAX_RETRIES=1
```

## Troubleshooting

### Issue: Script exits immediately

**Check:**

```bash
python3 check_send_time.py
```

**Solution:**

- Wait until capacity available
- Or lower GMAIL_DAILY_LIMIT

### Issue: Always hitting limit at same count

**Cause:** Other email activity not tracked by script

**Solution:**

```bash
# Lower limit to account for other activity
GMAIL_DAILY_LIMIT=150
```

### Issue: Account seems restricted

**Symptoms:**

- Limit hit well below 500
- Consistent rejections
- Takes days to resolve

**Solution:**

1. Stop all sending for 72 hours
2. Reduce to GMAIL_DAILY_LIMIT=50
3. Gradually increase over 2 weeks

### Issue: Want to force continue (not recommended)

**Don't do this** - it can get your account suspended.

But if you really need to:

1. Use different Gmail account
2. Split email list across accounts
3. Use Google Workspace account (2000/day limit)

## Summary

✅ **Automatic Detection** - No manual intervention needed  
✅ **Graceful Exit** - Saves all progress  
✅ **Clear Messaging** - Know exactly what to do  
✅ **Resume Capability** - Pick up where you left off  
✅ **No Data Loss** - Everything tracked in database

The system is designed to protect your Gmail account while maximizing throughput. When the limit is hit, it's better to
stop and resume later than to risk account suspension.

---

**Last Updated:** November 20, 2025  
**Version:** 2.0
