# University Merch Bot 🎓

A complete, production-grade automation system that scrapes official US university websites, extracts validated contact
emails, and sends personalized outreach emails requesting brochures, stickers, and prospectuses for educational
purposes.

## 🎯 Purpose

This system is designed for respectful academic outreach to universities worldwide. It helps students learn about
different institutions by collecting informational materials and establishing cultural exchange.

**This is NOT a spam bot.** All emails are:

- Polite and personalized
- Sent with proper throttling (40+ seconds between emails)
- Targeted at appropriate university contacts (admissions, info, international offices)
- Fully logged and tracked in a database

## 🏗️ Architecture

```
university_merch_bot/
│
├── main.py                      # Main orchestration script
├── config.py                    # All configuration settings
├── requirements.txt             # Python dependencies
│
├── data/                        # Data storage
│   ├── universities_raw.json   # University list from API
│   ├── emails_extracted.csv    # Extracted email addresses
│   └── db.sqlite3              # SQLite database
│
├── scraper/                     # Web scraping modules
│   ├── __init__.py
│   ├── fetch_universities.py   # Fetch university list
│   ├── crawl_contact_pages.py  # Async crawling
│   └── extract_emails.py       # Email extraction & validation
│
├── emailer/                     # Email sending modules
│   ├── __init__.py
│   ├── template.py             # Email templates
│   ├── send_email.py           # SMTP sending
│   └── throttle.py             # Rate limiting
│
├── utils/                       # Utility modules
│   ├── __init__.py
│   ├── validators.py           # Email & URL validation
│   ├── logger.py               # Logging utilities
│   └── db.py                   # Database operations
│
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or navigate to the project directory
cd university_merch_bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure SMTP (Gmail)

#### Option A: Gmail SMTP (Recommended)

1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
    - Go to: https://myaccount.google.com/apppasswords
    - Select "Mail" and "Other (Custom name)"
    - Generate password
    - Copy the 16-character password

3. **Update config.py**:
   ```python
   SENDER_EMAIL = "your.email@gmail.com"
   SENDER_PASSWORD = "your-16-char-app-password"
   ```

#### Option B: Gmail API (More Secure)

For Gmail API setup, follow: https://developers.google.com/gmail/api/quickstart/python

### 3. Test Configuration

```bash
# Test with dry-run (no emails sent)
python main.py --crawl-limit 5 --dry-run

# Test sending to your own email
# (Modify code or use --email-limit 1 --live)
```

### 4. Run Full Pipeline

```bash
# Dry run (recommended first)
python main.py --crawl-limit 10

# Live run (actually sends emails)
python main.py --crawl-limit 10 --live
```

## 🆕 New Features: Daily Limit & Duplicate Prevention

The `auto_run.py` script now includes intelligent features to respect Gmail's sending limits and prevent duplicate
emails:

### Key Features

✅ **Automatic Daily Limit Enforcement** - Respects Gmail's 500 emails/day limit (configurable)  
✅ **Duplicate Prevention** - Skips universities that have already been contacted  
✅ **Resume Capability** - Can be run multiple times to continue where it left off  
✅ **Real-time Progress Tracking** - Shows emails sent today and remaining capacity  
✅ **Auto-Exit on Limit** - Automatically stops and exits when Gmail rejects due to daily limit

### Quick Check Status

```bash
# Check current status (emails sent today, universities remaining)
python3 test_daily_limit.py

# Check when you can send again
python3 check_send_time.py
```

### Configuration

Set your daily limit in `.env` or `config.py`:

```bash
# Free Gmail: 450 (safe buffer below 500)
# Google Workspace: 1900 (safe buffer below 2000)
GMAIL_DAILY_LIMIT=450
```

### Usage Pattern

```bash
# Day 1: Sends up to 450 emails, then stops
python3 auto_run.py

# Same day again: Skips (daily limit reached)
python3 auto_run.py

# Day 2: Sends next batch, skips already-contacted universities
python3 auto_run.py
```

**📖 For detailed documentation, see [DAILY_LIMIT_GUIDE.md](DAILY_LIMIT_GUIDE.md)**

## Usage Guide

### Auto Run

The simplest way to run the complete pipeline is by using the `auto_run.py` script. This script executes the complete
pipeline end-to-end with no flags, no testing, just pure automation.

**To use the auto_run.py script:**

```bash
# 1. Configure your credentials in .env
cp .env.example .env
nano .env  # Add your Gmail credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run everything with ONE command
python3 auto_run.py
```

This will automatically:

- Fetch 2,349 US universities
- Crawl all websites for contact pages
- Extract and rank top 3 emails per university (using AI scoring)
- Send personalized emails to Primary, Secondary, and Tertiary contacts
- Log everything to database with full tracking

**NO FLAGS. NO DRY-RUN. Pure production mode.**

⚠️ **Warning**: This sends REAL emails! Make sure your Gmail credentials are correct.

### Command Line Arguments

```bash
python main.py [OPTIONS]

Options:
  --skip-fetch          Skip fetching universities (use existing data)
  --skip-crawl          Skip crawling contact pages
  --skip-extract        Skip email extraction
  --skip-email          Skip sending emails
  --crawl-limit N       Limit number of universities to crawl
  --email-limit N       Limit number of emails to send
  --live                Actually send emails (default is dry-run)
```

### Example Workflows

#### Test Run (5 Universities, No Emails Sent)

```bash
python main.py --crawl-limit 5
```

#### Resume Sending (Skip Scraping, Send Pending Emails)

```bash
python main.py --skip-fetch --skip-crawl --skip-extract --live
```

#### Full Production Run (Limited)

```bash
python main.py --crawl-limit 50 --email-limit 20 --live
```

#### Send Only 10 Emails

```bash
python main.py --skip-fetch --skip-crawl --skip-extract --email-limit 10 --live
```

## 🔧 Configuration

All settings are in `config.py`. Key configurations:

### Paths

```python
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "db.sqlite3"
```

### Crawling Settings

```python
REQUEST_TIMEOUT = 8                # seconds
MAX_RETRIES = 2
RATE_LIMIT_DELAY = 1.0            # seconds between requests
```

### Email Settings

```python
EMAIL_THROTTLE_DELAY = 40         # seconds between emails
EMAIL_JITTER_MIN = 3              # random jitter min
EMAIL_JITTER_MAX = 7              # random jitter max
EMAIL_MAX_RETRIES = 2
```

### SMTP Settings

```python
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = ""                 # YOUR EMAIL HERE
SENDER_PASSWORD = ""              # YOUR APP PASSWORD HERE
```

## 📊 Database Schema

SQLite database (`data/db.sqlite3`) with table:

```sql
CREATE TABLE email_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    university TEXT NOT NULL,
    email TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING',
    sent_at DATETIME,
    response_at DATETIME,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(university, email)
);
```

### Status Values

- `PENDING` - Not yet sent
- `SENT` - Successfully sent
- `FAILED` - Failed after all retries
- `RETRYING` - Currently retrying
- `COMPLETE` - Email sent and potentially replied to

## 🔍 Features

### Email Validation

- ✅ Must match university domain (.edu or university.org)
- ✅ Priority emails: admissions@, info@, international@, contact@, etc.
- ❌ Filtered out: careers@, jobs@, hr@, press@, webmaster@, etc.
- ✅ Domain cross-validation with university domain
- ✅ Deduplication

### Crawling Features

- 🚀 Asynchronous (fast)
- 🔄 Automatic retries
- 🎭 User-agent rotation
- ⏱️ Rate limiting (1 req/sec)
- 📝 Comprehensive logging

### Email Features

- 📧 Personalized greetings based on email address
- 🎯 Polite, professional template
- 🔁 Automatic retry on failure
- ⏰ Throttling with random jitter (40+ seconds between emails)
- 📊 Full database tracking

## 🛡️ Safety & Ethics

### Important Notes

1. **This is not spam**: All emails are legitimate academic outreach
2. **Respect rate limits**: Built-in throttling prevents server overload
3. **No mass mailing**: Sends max 1 email per 40+ seconds
4. **Respectful targeting**: Only contact appropriate university offices
5. **Full transparency**: All actions logged in database

### Legal & Ethical Considerations

- ✅ Only scrapes publicly available information
- ✅ Respects robots.txt (implement if needed)
- ✅ Uses appropriate user-agents
- ✅ Implements reasonable rate limiting
- ✅ Provides accurate sender information
### Best Practices

1. **Start small**: Test with `--crawl-limit 5` first
2. **Use dry-run**: Always test with dry-run before live sending
3. **Monitor logs**: Check logs for errors and issues
4. **Respect responses**: If a university asks to stop, honor it
5. **Don't abuse**: This is for legitimate academic purposes only

## 📈 Monitoring

### Check Database Statistics

```python
from utils.db import Database

db = Database()
stats = db.get_statistics()
print(stats)
db.close()
```

### View Logs

All actions are logged to console with timestamps. Redirect to file:

```bash
python main.py --crawl-limit 10 2>&1 | tee output.log
```

### Export Results

Emails are saved to `data/emails_extracted.csv` for easy review:

```bash
# View in terminal
cat data/emails_extracted.csv

# Open in Excel/LibreOffice
open data/emails_extracted.csv
```

## 🐛 Troubleshooting

### SMTP Authentication Failed

```
Error: SMTP authentication failed
```

**Solution**: Ensure you're using an App Password, not your regular Gmail password.

### No Emails Extracted

```
Warning: No contact pages found
```

**Solution**: Some universities block automated crawling. Try increasing timeout or check manually.

### Rate Limiting Errors

```
Error: 429 Too Many Requests
```

**Solution**: Increase `RATE_LIMIT_DELAY` in config.py

### SSL/TLS Errors

```
Error: SSL certificate verification failed
```

**Solution**: Update certifi: `pip install --upgrade certifi`

## 🔄 Workflow Steps

The system executes in 6 steps:

1. **Fetch Universities** - Downloads list from Hipolabs API
2. **Crawl Contact Pages** - Visits /contact, /admissions, etc.
3. **Extract Emails** - Uses regex + BeautifulSoup to find emails
4. **Populate Database** - Stores validated emails in SQLite
5. **Send Emails** - Sends personalized emails with throttling
6. **Show Summary** - Displays statistics and success rate

## 📦 Dependencies

- `aiohttp` - Async HTTP client for crawling
- `aiosmtplib` - Async SMTP for email sending
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation and CSV export
- `requests` - HTTP client for API calls
- `lxml` - Fast HTML parsing
- `email-validator` - Email validation
- `python-dotenv` - Environment variable management

## 📄 License

This project is for educational purposes. Use responsibly and ethically.

## 🤝 Contributing

This is a personal academic project. However, suggestions and improvements are welcome.

## ⚠️ Disclaimer

**Use this tool responsibly.** The author is not responsible for misuse. This tool is designed for legitimate academic
outreach only. Always respect recipient preferences and local regulations regarding automated emails.

---

**Author**: Gaurav Sharma  
**Purpose**: Academic Outreach & Cultural Exchange  
**Institution**: BVDU(COEP), Pune, India

*"Consistency Compounds."* - Naval Ravikant

