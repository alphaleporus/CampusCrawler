# 🔐 Environment Variables Setup Guide

This guide will help you set up your `.env` file to keep your credentials secure.

## Why Use .env?

✅ **Security** - Credentials never committed to git  
✅ **Flexibility** - Easy to change without editing code  
✅ **Best Practice** - Industry standard for credential management  
✅ **Multiple Environments** - Different settings for dev/prod

## 🚀 Quick Setup (2 Minutes)

### Step 1: Create .env File

```bash
# Copy the example file
cp .env.example .env
```

### Step 2: Get Gmail App Password

1. **Enable 2-Factor Authentication** on your Google account
    - Go to: https://myaccount.google.com/security

2. **Generate App Password**
    - Go to: https://myaccount.google.com/apppasswords
    - Select: **Mail** and **Other (Custom name)**
    - Name it: "University Bot"
    - Click **Generate**
    - Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)

### Step 3: Edit .env File

Open `.env` in your text editor and update:

```bash
# Required - Add your credentials
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop

# Optional - Customize if needed
# EMAIL_THROTTLE_DELAY=40
# REQUEST_TIMEOUT=8
```

**Important**: Remove spaces from the app password!

### Step 4: Verify Setup

```bash
python test_config.py
```

You should see:

```
✓ SENDER_EMAIL: your.email@gmail.com
✓ SENDER_PASSWORD: **************** (hidden)
```

## 📝 Complete .env File Example

```bash
# ===== REQUIRED =====
SENDER_EMAIL=gaurav.sharma@gmail.com
SENDER_PASSWORD=abcdefghijklmnop

# ===== OPTIONAL OVERRIDES =====

# SMTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Email Sending (adjust for your needs)
EMAIL_THROTTLE_DELAY=45        # Seconds between emails
EMAIL_JITTER_MIN=3             # Random delay min
EMAIL_JITTER_MAX=7             # Random delay max
EMAIL_MAX_RETRIES=2            # Retry failed emails

# Web Crawling
REQUEST_TIMEOUT=10             # Seconds to wait for response
MAX_RETRIES=2                  # Retry failed requests
RATE_LIMIT_DELAY=1.5           # Seconds between page requests

# Sender Information
SENDER_NAME=Gaurav Sharma
```

## 🔒 Security Best Practices

### ✅ DO:

- ✅ Keep `.env` file in your `.gitignore`
- ✅ Use App Passwords (not regular Gmail password)
- ✅ Create separate `.env` files for testing vs production
- ✅ Back up `.env` file securely (encrypted storage)

### ❌ DON'T:

- ❌ Commit `.env` to git
- ❌ Share `.env` file publicly
- ❌ Use regular Gmail password
- ❌ Store passwords in code

## 📂 File Structure

```
university_merch_bot/
├── .env              ← Your actual credentials (NOT in git)
├── .env.example      ← Template (safe to commit)
├── .gitignore        ← Ensures .env is ignored
└── config.py         ← Loads from .env
```

## 🔍 How It Works

1. `.env` file contains your credentials
2. `python-dotenv` loads them as environment variables
3. `config.py` reads them using `os.getenv()`
4. Your code uses the config values
5. `.gitignore` prevents `.env` from being committed

## 🐛 Troubleshooting

### "SENDER_EMAIL not configured"

**Problem**: .env file not found or not loaded

**Solution**:

```bash
# Check if .env exists
ls -la .env

# If not, create it
cp .env.example .env
```

### "SMTP authentication failed"

**Problem**: Wrong password or not using App Password

**Solution**:

1. Go to https://myaccount.google.com/apppasswords
2. Generate a new App Password
3. Update `.env` file
4. Remove all spaces from password

### "No module named 'dotenv'"

**Problem**: python-dotenv not installed

**Solution**:

```bash
pip install python-dotenv
```

### Password has spaces

**Problem**: Copied password with spaces

**Solution**:

```bash
# Wrong (with spaces)
SENDER_PASSWORD=abcd efgh ijkl mnop

# Correct (no spaces)
SENDER_PASSWORD=abcdefghijklmnop
```

## 🔄 Updating Credentials

To change your credentials:

1. Edit `.env` file
2. Save the file
3. Restart the bot
4. No code changes needed!

```bash
# Edit .env
nano .env

# Test new credentials
python test_config.py

# Run bot
python main.py --crawl-limit 5
```

## 🌍 Multiple Environments

You can have different .env files for different environments:

```bash
# Development
.env.development

# Production
.env.production

# Testing
.env.test
```

Load specific environment:

```bash
# Set which .env to use
export ENV_FILE=.env.production
```

## 📋 Checklist

Before running the bot:

- [ ] `.env` file created
- [ ] Gmail App Password generated
- [ ] `SENDER_EMAIL` set in `.env`
- [ ] `SENDER_PASSWORD` set in `.env` (no spaces)
- [ ] `.env` listed in `.gitignore`
- [ ] `python test_config.py` passes
- [ ] `.env` file NOT committed to git

## 💡 Pro Tips

1. **Test credentials immediately**:
   ```bash
   python test_config.py
   ```

2. **Keep a backup** of your `.env` file in a secure location (password manager, encrypted drive)

3. **Regenerate App Password** if you suspect it's compromised

4. **Use different credentials** for testing vs production

5. **Check Gmail security**: https://myaccount.google.com/security

## 🎯 Quick Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENDER_EMAIL` | ✅ Yes | - | Your Gmail address |
| `SENDER_PASSWORD` | ✅ Yes | - | Gmail App Password |
| `SMTP_HOST` | ❌ No | smtp.gmail.com | SMTP server |
| `SMTP_PORT` | ❌ No | 587 | SMTP port |
| `EMAIL_THROTTLE_DELAY` | ❌ No | 40 | Seconds between emails |
| `REQUEST_TIMEOUT` | ❌ No | 8 | HTTP timeout |

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Test configuration
python test_config.py

# 2. Try dry run (no emails sent)
python main.py --crawl-limit 2

# 3. Send test email to yourself
python main.py --skip-fetch --skip-crawl --skip-extract --email-limit 1 --live
```

---

**You're all set!** Your credentials are now secure and won't be committed to git. 🔒
