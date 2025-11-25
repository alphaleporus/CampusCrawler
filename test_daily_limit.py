#!/usr/bin/env python3
"""
Test script to verify daily limit and duplicate prevention functionality.

This script tests:
1. Checking emails sent today
2. Checking if universities have been contacted
3. Daily limit enforcement
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils.db import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)


def test_daily_limit_tracking():
    """Test tracking of emails sent today."""
    logger.info("=" * 80)
    logger.info("TEST: Daily Limit Tracking")
    logger.info("=" * 80)

    db = Database()

    # Get emails sent today and in last 24h
    emails_sent_today = db.get_emails_sent_today()
    emails_sent_last_24h = db.get_emails_sent_last_24h()
    daily_limit = config.GMAIL_DAILY_LIMIT
    remaining = daily_limit - emails_sent_last_24h

    logger.info(f"✓ Gmail Daily Limit:     {daily_limit}")
    logger.info(f"✓ Sent Today (midnight): {emails_sent_today}")
    logger.info(f"✓ Sent (24h rolling):    {emails_sent_last_24h}")
    logger.info(f"✓ Remaining Capacity:    {remaining}")
    logger.info("")
    logger.info("ℹ️  Gmail enforces ROLLING 24-hour limits (not calendar day)")
    logger.info("")

    if remaining > 0:
        logger.info(f"✓ Status: Can send {remaining} more emails")
    else:
        logger.warning("⚠️  Status: Daily limit reached!")
        logger.warning("   Wait a few hours for the rolling window to open up")

    logger.info("")

    db.close()
    return emails_sent_last_24h, remaining


def test_university_sent_status():
    """Test checking if universities have been contacted."""
    logger.info("=" * 80)
    logger.info("TEST: University Contact Status")
    logger.info("=" * 80)

    db = Database()

    # Get all universities from database
    cursor = db.conn.cursor()
    cursor.execute("SELECT DISTINCT university FROM email_campaigns ORDER BY university LIMIT 10")
    universities = [row['university'] for row in cursor.fetchall()]

    logger.info(f"Checking status for {len(universities)} sample universities...\n")

    contacted = 0
    not_contacted = 0

    for uni in universities:
        has_sent = db.university_has_sent_emails(uni)
        status = "✓ CONTACTED" if has_sent else "⏳ NOT CONTACTED"
        logger.info(f"{status}: {uni}")

        if has_sent:
            contacted += 1
        else:
            not_contacted += 1

    logger.info("")
    logger.info(f"Summary: {contacted} contacted, {not_contacted} not contacted")
    logger.info("")

    db.close()
    return contacted, not_contacted


def test_universities_remaining():
    """Test getting list of universities that haven't been contacted."""
    logger.info("=" * 80)
    logger.info("TEST: Universities Remaining")
    logger.info("=" * 80)

    db = Database()

    universities_remaining = db.get_universities_without_sent_emails()

    logger.info(f"✓ Universities not yet contacted: {len(universities_remaining)}")

    if len(universities_remaining) > 0:
        logger.info(f"\nShowing first 10 universities to contact:")
        for uni in universities_remaining[:10]:
            logger.info(f"   - {uni}")

        if len(universities_remaining) > 10:
            logger.info(f"   ... and {len(universities_remaining) - 10} more")
    else:
        logger.info("✅ All universities have been contacted!")

    logger.info("")

    db.close()
    return len(universities_remaining)


def test_database_statistics():
    """Test getting database statistics."""
    logger.info("=" * 80)
    logger.info("TEST: Database Statistics")
    logger.info("=" * 80)

    db = Database()

    stats = db.get_statistics()

    logger.info("Database Status:")
    for status, count in stats.items():
        logger.info(f"   {status:20s}: {count}")

    logger.info("")

    db.close()
    return stats


def main():
    """Run all tests."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("🧪 TESTING DAILY LIMIT & DUPLICATE PREVENTION")
    logger.info("=" * 80)
    logger.info("")

    try:
        # Test 1: Daily limit tracking
        emails_today, remaining = test_daily_limit_tracking()

        # Test 2: University sent status
        contacted, not_contacted = test_university_sent_status()

        # Test 3: Universities remaining
        remaining_count = test_universities_remaining()

        # Test 4: Database statistics
        stats = test_database_statistics()

        # Summary
        logger.info("=" * 80)
        logger.info("✅ ALL TESTS COMPLETE")
        logger.info("=" * 80)
        logger.info("")
        logger.info("Summary:")
        logger.info(f"   • Can send {remaining} more emails")
        logger.info(f"   • {remaining_count} universities remaining to contact")
        logger.info(f"   • {stats.get('SENT', 0)} emails successfully sent so far")
        logger.info(f"   • {stats.get('PENDING', 0)} emails pending")
        logger.info("")

        if remaining_count > 0 and remaining > 0:
            logger.info("💡 You can run auto_run.py to continue sending emails")
        elif remaining_count > 0 and remaining <= 0:
            logger.info("⏰ Daily limit reached. Run auto_run.py tomorrow to continue")
        else:
            logger.info("🎉 All universities have been contacted!")

        logger.info("")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
