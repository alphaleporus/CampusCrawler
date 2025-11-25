#!/usr/bin/env python3
"""
Send Live Emails - Safe Batch Sending Script

This script sends real emails with built-in safety checks.
Use with caution - this will actually send emails!
"""

import sys
import asyncio
from utils.logger import setup_logger
from utils.db import Database
from emailer.send_email import EmailSender, validate_smtp_config
from emailer.throttle import send_all_pending_emails
import config

logger = setup_logger(__name__)


def show_pending_preview(limit=10):
    """Show preview of emails that will be sent."""
    db = Database()
    try:
        pending = db.get_pending_emails(limit=limit)

        if not pending:
            print("✅ No pending emails to send!")
            return False

        print("=" * 70)
        print(f"📧 PREVIEW: Next {len(pending)} emails to be sent")
        print("=" * 70)

        for idx, email in enumerate(pending, 1):
            print(f"{idx}. {email['email']} ({email['university']})")
            if email['retry_count'] > 0:
                print(f"   ⚠️  Retry attempt {email['retry_count']}")

        print("=" * 70)
        return True

    finally:
        db.close()


def get_user_confirmation(count):
    """Get user confirmation before sending."""
    print()
    print("⚠️  WARNING: You are about to send REAL EMAILS!")
    print(f"📨 Number of emails to send: {count}")
    print(f"⏱️  Estimated time: ~{(count * 45) // 60} minutes")
    print()

    response = input("Type 'SEND' to confirm, or anything else to cancel: ").strip()
    return response == 'SEND'


def check_smtp_config():
    """Verify SMTP configuration before sending."""
    print("🔍 Checking SMTP configuration...")

    if not config.SENDER_EMAIL:
        print("❌ SENDER_EMAIL not configured!")
        print("   Update your .env file with your email")
        return False

    if not config.SENDER_PASSWORD:
        print("❌ SENDER_PASSWORD not configured!")
        print("   Update your .env file with your app password")
        return False

    print(f"✅ Email: {config.SENDER_EMAIL}")
    print(f"✅ SMTP: {config.SMTP_HOST}:{config.SMTP_PORT}")
    return True


async def send_test_email():
    """Send a test email to verify everything works."""
    print()
    print("📧 Sending test email to yourself...")

    sender = EmailSender()
    success, error = await sender.send_single_email(
        "Test University",
        config.SENDER_EMAIL  # Send to yourself
    )

    if success:
        print("✅ Test email sent successfully!")
        print(f"   Check your inbox: {config.SENDER_EMAIL}")
        return True
    else:
        print(f"❌ Test email failed: {error}")
        return False


def main():
    """Main function for safe email sending."""
    print("=" * 70)
    print("🚀 LIVE EMAIL SENDER")
    print("=" * 70)
    print()

    # Check configuration
    if not check_smtp_config():
        sys.exit(1)

    # Ask how many emails to send
    print()
    try:
        count = input("How many emails do you want to send? (1-50): ").strip()
        count = int(count)

        if count < 1 or count > 50:
            print("❌ Please enter a number between 1 and 50")
            sys.exit(1)
    except ValueError:
        print("❌ Please enter a valid number")
        sys.exit(1)

    # Show preview
    print()
    has_pending = show_pending_preview(limit=count)

    if not has_pending:
        sys.exit(0)

    # Offer test email
    print()
    test_response = input("Send test email to yourself first? (y/n): ").strip().lower()

    if test_response == 'y':
        test_success = asyncio.run(send_test_email())
        if not test_success:
            print("❌ Test failed. Fix the issue before sending to universities.")
            sys.exit(1)

        print()
        proceed = input("Test successful! Continue with university emails? (y/n): ").strip().lower()
        if proceed != 'y':
            print("Cancelled by user")
            sys.exit(0)

    # Get final confirmation
    if not get_user_confirmation(count):
        print("❌ Cancelled by user")
        sys.exit(0)

    # Send emails
    print()
    print("=" * 70)
    print("📨 SENDING EMAILS...")
    print("=" * 70)
    print()

    try:
        stats = asyncio.run(send_all_pending_emails(dry_run=False, limit=count))

        print()
        print("=" * 70)
        print("✅ BATCH COMPLETE!")
        print("=" * 70)
        print(f"Attempted: {stats['attempted']}")
        print(f"Sent: {stats['sent']}")
        print(f"Failed: {stats['failed']}")
        print(f"Skipped: {stats['skipped']}")

        success_rate = (stats['sent'] / stats['attempted'] * 100) if stats['attempted'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        print()

        # Show remaining
        db = Database()
        try:
            remaining = db.get_pending_emails(limit=1)
            if remaining:
                print(f"📊 {len(db.get_pending_emails())} emails still pending")
                print("   Run this script again to send more")
            else:
                print("🎉 All pending emails have been sent!")
        finally:
            db.close()

    except KeyboardInterrupt:
        print()
        print("⚠️  Interrupted by user")
        print("   Emails already sent are recorded in database")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
