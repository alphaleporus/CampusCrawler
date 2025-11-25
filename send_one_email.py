#!/usr/bin/env python3
"""Send ONE email to ONE university - for testing"""

import asyncio
from utils.db import Database
from emailer.send_email import EmailSender
import config


async def main():
    print("=" * 70)
    print("SEND ONE EMAIL - TESTING SCRIPT")
    print("=" * 70)
    print()

    # Get first pending email
    db = Database()
    pending = db.get_pending_emails(limit=1)

    if not pending:
        print("❌ No pending emails!")
        db.close()
        return

    email_record = pending[0]
    university = email_record['university']
    recipient = email_record['email']

    print(f"📧 Will send email to:")
    print(f"   University: {university}")
    print(f"   Email: {recipient}")
    print()
    print(f"📨 From: {config.SENDER_EMAIL}")
    print()

    confirm = input("Type 'YES' to send this email: ").strip()

    if confirm != 'YES':
        print("❌ Cancelled")
        db.close()
        return

    print()
    print("📬 Sending...")

    sender = EmailSender()
    success, error = await sender.send_single_email(university, recipient)

    if success:
        print(f"✅ SUCCESS! Email sent to {recipient}")
        print()
        print(f"🔍 Check if it went to:")
        print(f"   Your email: {config.SENDER_EMAIL} (WRONG)")
        print(f"   University: {recipient} (CORRECT)")
        print()
        print("Now check your 'Sent' folder in Gmail to verify!")

        # Update database
        db.update_status(recipient, config.STATUS_SENT)
    else:
        print(f"❌ FAILED: {error}")

    db.close()


if __name__ == "__main__":
    asyncio.run(main())
