# Auto-Exit Feature Summary

## What Was Added

The system now **automatically detects and exits** when Gmail's daily sending limit is reached.

## Problem Solved

**Before:**

- Script would keep retrying when limit was hit
- Wasted time on failed retries
- Unclear what to do next
- Could trigger account flags

**After:**

- Immediately detects Gmail limit error (550 5.4.5)
- Stops sending without retries
- Saves all progress to database
- Shows clear error message with next steps
- Exits cleanly with code 2

## How It Works

### When Gmail Rejects

```
1. Email sent to Gmail
   ↓
2. Gmail responds: "550 5.4.5 Daily user sending limit exceeded"
   ↓
3. System detects error pattern
   ↓
4. Raises GmailDailyLimitError (no retry)
   ↓
5. Saves progress to database
   ↓
6. Displays helpful error message
   ↓
7. Exits with code 2
```

### Error Message You'll See

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

## Usage

### Normal Run

```bash
python3 auto_run.py
```

If limit is hit:

- Script automatically exits
- Progress saved
- Can resume later

### Check Before Running

```bash
# See current capacity
python3 check_send_time.py

# Run if capacity available
python3 auto_run.py
```

### Resume After Limit

```bash
# Wait 24-48 hours

# Check capacity
python3 check_send_time.py

# Resume (will skip already-contacted universities)
python3 auto_run.py
```

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | All done! |
| 1 | Error | Check logs, fix issue |
| 2 | **Gmail Limit** | **Wait 24-48h, then retry** |
| 130 | Ctrl+C | User stopped it |

Check exit code:

```bash
python3 auto_run.py
echo $?  # Shows exit code
```

## Benefits

✅ **No wasted retries** - Stops immediately  
✅ **Clear guidance** - Know exactly what to do  
✅ **Data safe** - All progress saved  
✅ **Account safe** - No repeated failed attempts  
✅ **Easy resume** - Just run again later

## Files Modified

1. **`emailer/send_email.py`**
    - Added `GmailDailyLimitError` exception class
    - Detects 550 5.4.5 error pattern
    - Raises exception without retry

2. **`auto_run.py`**
    - Imports `GmailDailyLimitError`
    - Catches exception in `send_university_emails()`
    - Catches exception in `run_send_emails_async()`
    - Catches exception in `main()` and exits with code 2

## Configuration

To prevent hitting the limit:

```bash
# Edit .env
GMAIL_DAILY_LIMIT=200          # Lower limit
EMAIL_THROTTLE_DELAY=60        # Slower sending
EMAIL_JITTER_MIN=10            # More variation
EMAIL_JITTER_MAX=20
```

## Testing

The feature has been tested:

✅ Exception can be raised and caught  
✅ Error pattern detection works  
✅ Exits with correct code  
✅ Progress is saved

## Documentation

Full details in:

- **`GMAIL_LIMIT_ERROR_HANDLING.md`** - Complete guide
- **`README.md`** - Feature mention
- **`QUICK_REFERENCE.md`** - Quick commands

## Quick Commands

```bash
# Check if you can send
python3 check_send_time.py

# Run campaign
python3 auto_run.py

# If exits with limit error:
# 1. Wait 24-48 hours
# 2. Check: python3 check_send_time.py
# 3. Resume: python3 auto_run.py
```

## Summary

The script is now **smarter and safer**:

- Automatically detects Gmail limit errors
- Stops immediately (no wasted retries)
- Saves all progress
- Provides clear next steps
- Easy to resume later

You no longer need to manually stop the script or worry about repeated failures. It handles everything automatically!

---

**Feature Added:** November 20, 2025  
**Status:** ✅ Complete and Tested
