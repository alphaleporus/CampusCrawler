#!/usr/bin/env python3
"""
View statistics from the database.

Quick script to check campaign progress.
"""

import sys
from pathlib import Path

try:
    from utils.db import Database
    from utils.logger import setup_logger, log_statistics
    import config
except ImportError:
    print("❌ Error: Could not import required modules.")
    print("Make sure you're running this from the project directory.")
    sys.exit(1)


def main():
    """Display database statistics."""
    print("=" * 60)
    print("UNIVERSITY MERCH BOT - STATISTICS")
    print("=" * 60)
    print()

    # Check if database exists
    if not config.DB_PATH.exists():
        print("❌ Database not found!")
        print(f"Expected location: {config.DB_PATH}")
        print()
        print("Run the bot first to create the database:")
        print("  python main.py --crawl-limit 5")
        return 1

    db = Database()

    try:
        # Get statistics
        stats = db.get_statistics()

        # Calculate additional metrics
        total = stats.get('TOTAL', 0)
        sent = stats.get(config.STATUS_SENT, 0)
        failed = stats.get(config.STATUS_FAILED, 0)
        pending = stats.get(config.STATUS_PENDING, 0)
        retrying = stats.get(config.STATUS_RETRYING, 0)

        success_rate = (sent / total * 100) if total > 0 else 0
        failure_rate = (failed / total * 100) if total > 0 else 0

        # Display statistics
        print(f"📊 Total Emails in Database: {total}")
        print()
        print("Status Breakdown:")
        print(f"  ✅ Sent:       {sent:>6} ({success_rate:.1f}%)")
        print(f"  ❌ Failed:     {failed:>6} ({failure_rate:.1f}%)")
        print(f"  ⏳ Pending:    {pending:>6}")
        print(f"  🔄 Retrying:   {retrying:>6}")
        print()

        # Get sample of pending emails
        if pending > 0 or retrying > 0:
            print("📧 Next emails to send:")
            pending_emails = db.get_pending_emails(limit=5)

            for idx, email_rec in enumerate(pending_emails, 1):
                print(f"  {idx}. {email_rec['email']} ({email_rec['university']})")

            if len(pending_emails) >= 5 and (pending + retrying) > 5:
                print(f"  ... and {pending + retrying - 5} more")
            print()

        # Show recent failures if any
        if failed > 0:
            print("❌ Recent failures:")
            cursor = db.conn.cursor()
            cursor.execute("""
                SELECT university, email, error
                FROM email_campaigns
                WHERE status = ?
                ORDER BY updated_at DESC
                LIMIT 3
            """, (config.STATUS_FAILED,))

            for row in cursor.fetchall():
                print(f"  • {row['email']} ({row['university']})")
                if row['error']:
                    print(f"    Error: {row['error'][:60]}...")
            print()

        print("=" * 60)

        # Suggestions
        if pending > 0 or retrying > 0:
            print()
            print("💡 To send pending emails:")
            print("  python main.py --skip-fetch --skip-crawl --skip-extract --email-limit 10 --live")

        if total == 0:
            print()
            print("💡 To start crawling:")
            print("  python main.py --crawl-limit 10")

        return 0

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
