#!/usr/bin/env python3
"""
Check when you can send emails again based on Gmail's rolling 24-hour limit.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

import config
from utils.db import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    logger.info("=" * 80)
    logger.info("📅 GMAIL SENDING WINDOW CHECKER")
    logger.info("=" * 80)
    logger.info("")

    db = Database()

    # Get current status
    emails_sent_last_24h = db.get_emails_sent_last_24h()
    daily_limit = config.GMAIL_DAILY_LIMIT
    remaining = daily_limit - emails_sent_last_24h

    logger.info(f"Gmail Daily Limit:       {daily_limit}")
    logger.info(f"Emails Sent (24h):       {emails_sent_last_24h}")
    logger.info(f"Remaining Capacity:      {remaining}")
    logger.info("")

    if remaining > 0:
        logger.info(f"✅ You can send {remaining} more emails RIGHT NOW!")
        db.close()
        return

    # Get the oldest emails in the last 24 hours
    cursor = db.conn.cursor()
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)

    cursor.execute("""
        SELECT sent_at, COUNT(*) OVER (ORDER BY sent_at) as cumulative_count
        FROM email_campaigns
        WHERE status = ? AND sent_at >= ?
        ORDER BY sent_at ASC
        LIMIT 50
    """, (config.STATUS_SENT, twenty_four_hours_ago))

    results = cursor.fetchall()

    if not results:
        logger.info("✅ No emails in the last 24 hours - you can send now!")
        db.close()
        return

    # Find when we'll have capacity
    logger.info("⏰ SENDING WINDOW FORECAST:")
    logger.info("")

    now = datetime.now()
    shown_times = 0

    for row in results:
        sent_time = datetime.fromisoformat(row['sent_at'])
        available_time = sent_time + timedelta(hours=24)

        if available_time > now:
            time_until = available_time - now
            hours = int(time_until.total_seconds() // 3600)
            minutes = int((time_until.total_seconds() % 3600) // 60)

            logger.info(f"   {available_time.strftime('%Y-%m-%d %I:%M %p')} - "
                        f"1 more email slot opens (in {hours}h {minutes}m)")

            shown_times += 1
            if shown_times >= 10:
                break

    logger.info("")
    logger.info("💡 TIP: The window opens gradually as old emails age out")
    logger.info("💡 Check again in an hour with: python3 check_send_time.py")
    logger.info("")

    db.close()


if __name__ == "__main__":
    main()
