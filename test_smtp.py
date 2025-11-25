#!/usr/bin/env python3
"""Quick SMTP connection test"""

import asyncio
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import config


async def test_smtp():
    """Test SMTP connection and send test email."""
    print("=" * 60)
    print("SMTP Connection Test")
    print("=" * 60)
    print()
    print(f"Email: {config.SENDER_EMAIL}")
    print(f"Password: {'*' * len(config.SENDER_PASSWORD)} ({len(config.SENDER_PASSWORD)} chars)")
    print(f"Host: {config.SMTP_HOST}")
    print(f"Port: {config.SMTP_PORT}")
    print()

    try:
        print("🔌 Connecting to SMTP server...")

        async with asyncio.timeout(30):
            async with aiosmtplib.SMTP(
                    hostname=config.SMTP_HOST,
                    port=config.SMTP_PORT,
                    start_tls=True,  # Use start_tls instead of manual starttls
                    timeout=15
            ) as smtp:
                print("✓ Connected")
                print("✓ TLS started")

                print("🔑 Logging in...")
                await smtp.login(config.SENDER_EMAIL, config.SENDER_PASSWORD)
                print("✓ Login successful")

                # Create test message
                message = MIMEMultipart()
                message['Subject'] = "Test Email from University Bot"
                message['From'] = formataddr((config.SENDER_NAME, config.SENDER_EMAIL))
                message['To'] = config.SENDER_EMAIL

                body = "This is a test email to verify SMTP is working."
                message.attach(MIMEText(body, 'plain'))

                print(f"📧 Sending test email to {config.SENDER_EMAIL}...")
                await smtp.send_message(message)
                print("✓ Email sent!")

        print()
        print("=" * 60)
        print("✅ SMTP TEST PASSED!")
        print("=" * 60)
        print()
        print(f"Check your inbox: {config.SENDER_EMAIL}")
        return True

    except asyncio.TimeoutError:
        print()
        print("❌ TIMEOUT - Connection took too long")
        print()
        print("Possible issues:")
        print("1. Firewall blocking SMTP")
        print("2. VPN interfering")
        print("3. Gmail app password expired")
        return False

    except aiosmtplib.SMTPAuthenticationError as e:
        print()
        print(f"❌ AUTHENTICATION FAILED: {e}")
        print()
        print("Possible issues:")
        print("1. Wrong app password")
        print("2. Spaces in password")
        print("3. 2FA not enabled")
        print()
        print("Fix:")
        print("1. Go to: https://myaccount.google.com/apppasswords")
        print("2. Generate new app password")
        print("3. Update .env file with new password (remove spaces)")
        return False

    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print()
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_smtp())
    exit(0 if result else 1)
