"""
Test configuration and validate setup before running the full system.

Run this script to check if everything is configured correctly.
"""

import sys
from pathlib import Path


def test_env_file():
    """Check if .env file exists."""
    print("🔍 Testing .env file...")

    env_file = Path(".env")
    env_example = Path(".env.example")

    if not env_file.exists():
        print("  ✗ .env file not found!")
        print()
        print("  To fix this:")
        if env_example.exists():
            print("  1. Copy the example: cp .env.example .env")
        else:
            print("  1. Create .env file manually")
        print("  2. Add your credentials:")
        print("     SENDER_EMAIL=your@gmail.com")
        print("     SENDER_PASSWORD=your-app-password")
        print()
        return False

    print("  ✓ .env file exists")

    # Check if .env is in .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        with open(gitignore) as f:
            if ".env" in f.read():
                print("  ✓ .env is in .gitignore (safe from git)")
            else:
                print("  ⚠ WARNING: .env not in .gitignore!")

    print("✅ Environment file setup correct!\n")
    return True


def test_imports():
    """Test if all required packages are installed."""
    print("🔍 Testing imports...")

    try:
        import aiohttp
        print("  ✓ aiohttp")
    except ImportError:
        print("  ✗ aiohttp - Run: pip install aiohttp")
        return False

    try:
        import aiosmtplib
        print("  ✓ aiosmtplib")
    except ImportError:
        print("  ✗ aiosmtplib - Run: pip install aiosmtplib")
        return False

    try:
        from bs4 import BeautifulSoup
        print("  ✓ beautifulsoup4")
    except ImportError:
        print("  ✗ beautifulsoup4 - Run: pip install beautifulsoup4")
        return False

    try:
        import pandas
        print("  ✓ pandas")
    except ImportError:
        print("  ✗ pandas - Run: pip install pandas")
        return False

    try:
        import requests
        print("  ✓ requests")
    except ImportError:
        print("  ✗ requests - Run: pip install requests")
        return False

    try:
        import lxml
        print("  ✓ lxml")
    except ImportError:
        print("  ✗ lxml - Run: pip install lxml")
        return False

    try:
        from dotenv import load_dotenv
        print("  ✓ python-dotenv")
    except ImportError:
        print("  ✗ python-dotenv - Run: pip install python-dotenv")
        return False

    print("✅ All imports successful!\n")
    return True


def test_config():
    """Test if config is properly set up."""
    print("🔍 Testing configuration...")

    try:
        import config
        print("  ✓ config.py loaded")
    except ImportError:
        print("  ✗ config.py not found")
        return False

    # Check SMTP settings
    if not config.SENDER_EMAIL:
        print("  ✗ SENDER_EMAIL not set")
        print()
        print("  To fix this:")
        print("  1. Open .env file")
        print("  2. Add: SENDER_EMAIL=your@gmail.com")
        print()
        return False
    else:
        print(f"  ✓ SENDER_EMAIL: {config.SENDER_EMAIL}")

    if not config.SENDER_PASSWORD:
        print("  ✗ SENDER_PASSWORD not set")
        print()
        print("  To fix this:")
        print("  1. Get App Password from: https://myaccount.google.com/apppasswords")
        print("  2. Open .env file")
        print("  3. Add: SENDER_PASSWORD=your-app-password")
        print()
        return False
    else:
        print(f"  ✓ SENDER_PASSWORD: {'*' * len(config.SENDER_PASSWORD)} (hidden)")

    # Show where credentials are loaded from
    print(f"  ℹ Credentials loaded from: .env file")

    # Check paths
    if not config.DATA_DIR.exists():
        print(f"  ! Creating data directory: {config.DATA_DIR}")
        config.DATA_DIR.mkdir(exist_ok=True)
    else:
        print(f"  ✓ Data directory exists: {config.DATA_DIR}")

    print("✅ Configuration looks good!\n")
    return True


def test_database():
    """Test database initialization."""
    print("🔍 Testing database...")

    try:
        from utils.db import Database

        db = Database()
        stats = db.get_statistics()
        db.close()

        print(f"  ✓ Database initialized")
        print(f"  ✓ Current records: {stats.get('TOTAL', 0)}")

        print("✅ Database working!\n")
        return True

    except Exception as e:
        print(f"  ✗ Database error: {e}")
        return False


def test_email_template():
    """Test email template generation."""
    print("🔍 Testing email template...")

    try:
        from emailer.template import generate_email

        subject, body = generate_email(
            "Test University",
            "admissions@test.edu"
        )

        print(f"  ✓ Subject: {subject}")
        print(f"  ✓ Body length: {len(body)} characters")

        if len(body) < 50:
            print("  ✗ Email body too short!")
            return False

        print("✅ Email template working!\n")
        return True

    except Exception as e:
        print(f"  ✗ Template error: {e}")
        return False


def test_validators():
    """Test validation functions."""
    print("🔍 Testing validators...")

    try:
        from utils.validators import (
            is_valid_email,
            is_university_email,
            is_priority_email
        )

        # Test valid email
        if not is_valid_email("test@example.com"):
            print("  ✗ Email validation failed")
            return False
        print("  ✓ Email validation")

        # Test university email
        if not is_university_email("info@university.edu"):
            print("  ✗ University email validation failed")
            return False
        print("  ✓ University email validation")

        # Test priority email
        if not is_priority_email("admissions@university.edu"):
            print("  ✗ Priority email detection failed")
            return False
        print("  ✓ Priority email detection")

        print("✅ Validators working!\n")
        return True

    except Exception as e:
        print(f"  ✗ Validator error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("UNIVERSITY MERCH BOT - CONFIGURATION TEST")
    print("=" * 60)
    print()

    all_passed = True

    # Run tests in order
    all_passed &= test_env_file()
    all_passed &= test_imports()
    all_passed &= test_config()
    all_passed &= test_database()
    all_passed &= test_email_template()
    all_passed &= test_validators()

    # Final result
    print("=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("🎉 Your configuration is perfect!")
        print()
        print("Next steps:")
        print("  1. Dry run: python main.py --crawl-limit 5")
        print("  2. View docs: cat QUICKSTART.md")
        print()
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 60)
        print()
        print("Please fix the issues above before running the bot.")
        print()
        print("Need help?")
        print("  • Read SETUP_ENV.md for .env setup guide")
        print("  • Check QUICKSTART.md for quick start")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
