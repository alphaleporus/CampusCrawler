# Quick Start Guide 🚀

Get your University Merch Bot running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Gmail SMTP

### Get Gmail App Password

1. Go to your Google Account: https://myaccount.google.com
2. Enable **2-Factor Authentication** (if not already enabled)
3. Go to: https://myaccount.google.com/apppasswords
4. Select:
    - App: "Mail"
    - Device: "Other" (enter "University Bot")
5. Click **Generate**
6. Copy the 16-character password (no spaces)

### Create .env File

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop
```

**Important**: Remove spaces from the app password!

**Note**: The `.env` file is already in `.gitignore` so it won't be committed to git.

## Step 3: Test Run (DRY RUN - No Emails Sent)

```bash
python main.py --crawl-limit 5
```

This will:

- ✅ Fetch 5 universities from API
- ✅ Crawl their contact pages
- ✅ Extract email addresses
- ✅ Save to database
- ❌ **NOT send any emails** (dry run mode)

## Step 4: Review Results

Check the files created:

```bash
# View extracted emails
cat data/emails_extracted.csv

# Check database stats
sqlite3 data/db.sqlite3 "SELECT status, COUNT(*) FROM email_campaigns GROUP BY status;"
```

## Step 5: Send Test Emails (LIVE)

Start with just 2-3 emails to test:

```bash
python main.py --skip-fetch --skip-crawl --skip-extract --email-limit 3 --live
```

**⚠️ WARNING**: This will ACTUALLY SEND EMAILS!

## Common Commands

### Full Test Run (10 Universities, No Emails)

```bash
python main.py --crawl-limit 10
```

### Send Pending Emails (Live)

```bash
python main.py --skip-fetch --skip-crawl --skip-extract --email-limit 10 --live
```

### Resume from Existing Data

```bash
python main.py --skip-fetch --email-limit 5 --live
```

## Safety Tips

1. **Always test with `--crawl-limit` first**
2. **Use dry-run (default) before `--live`**
3. **Start with `--email-limit 3` for live tests**
4. **Wait 24 hours between large batches**
5. **Monitor your Gmail "Sent" folder**

## Troubleshooting

### "SMTP authentication failed"

- Make sure you're using an **App Password**, not your regular Gmail password
- Remove spaces from the app password in `.env`
- Ensure 2FA is enabled on your Google account

### "No module named 'aiohttp'"

```bash
pip install -r requirements.txt
```

### "SENDER_EMAIL not configured"

- Make sure you created the `.env` file: `cp .env.example .env`
- Add your credentials to `.env` file

## Next Steps

Once everything works:

1. Review the full README.md for detailed documentation
2. Adjust throttling settings in `.env` if needed
3. Customize the email template in `emailer/template.py`
4. Run larger batches (50-100 universities at a time)

---

**Remember**: This is for respectful academic outreach. Always be polite and honor opt-out requests!
