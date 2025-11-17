"""
Email sending functionality with SMTP support.

Handles email delivery with retry logic, error handling, and proper logging.
"""

import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
from typing import Optional, Tuple
import traceback

import aiosmtplib

import config
from utils.logger import setup_logger
from emailer.template import generate_email

logger = setup_logger(__name__)


class EmailSender:
    """Asynchronous email sender using SMTP."""

    def __init__(
            self,
            smtp_host: str = config.SMTP_HOST,
            smtp_port: int = config.SMTP_PORT,
            sender_email: str = config.SENDER_EMAIL,
            sender_password: str = config.SENDER_PASSWORD,
            sender_name: str = config.SENDER_NAME
    ):
        """
        Initialize email sender.
        
        Args:
            smtp_host: SMTP server host
            smtp_port: SMTP server port
            sender_email: Sender's email address
            sender_password: Sender's email password (app password for Gmail)
            sender_name: Sender's display name
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.sender_name = sender_name

        if not self.sender_email or not self.sender_password:
            logger.warning("SMTP credentials not configured. Emails will not be sent.")

    def _create_message(
            self,
            recipient_email: str,
            subject: str,
            body: str
    ) -> MIMEMultipart:
        """
        Create email message with proper headers.
        
        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            body: Email body text
        
        Returns:
            MIME message object
        """
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = formataddr((self.sender_name, self.sender_email))
        message['To'] = recipient_email
        message['Message-ID'] = make_msgid()

        # Add text part
        text_part = MIMEText(body, 'plain', 'utf-8')
        message.attach(text_part)

        return message

    async def send_single_email(
            self,
            university_name: str,
            recipient_email: str,
            retry_count: int = 0
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a single email with retry logic.
        
        Args:
            university_name: Name of the university
            recipient_email: Recipient's email address
            retry_count: Current retry attempt
        
        Returns:
            Tuple of (success, error_message)
        """
        if not self.sender_email or not self.sender_password:
            error = "SMTP credentials not configured"
            logger.error(error)
            return False, error

        try:
            # Generate email content
            subject, body = generate_email(university_name, recipient_email)

            # Create message
            message = self._create_message(recipient_email, subject, body)

            # Send via SMTP
            logger.info(f"Sending email to {recipient_email} ({university_name})...")

            async with aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    use_tls=False
            ) as smtp:
                await smtp.connect()
                await smtp.starttls()
                await smtp.login(self.sender_email, self.sender_password)
                await smtp.send_message(message)

            logger.info(f"✓ Successfully sent email to {recipient_email}")
            return True, None

        except aiosmtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(f"✗ Failed to send to {recipient_email}: {error_msg}")
            logger.debug(traceback.format_exc())

            # Retry logic
            if retry_count < config.EMAIL_MAX_RETRIES:
                logger.info(f"Retrying {recipient_email} (attempt {retry_count + 1})...")
                await asyncio.sleep(5)
                return await self.send_single_email(university_name, recipient_email, retry_count + 1)

            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"✗ Failed to send to {recipient_email}: {error_msg}")
            logger.debug(traceback.format_exc())

            # Retry logic
            if retry_count < config.EMAIL_MAX_RETRIES:
                logger.info(f"Retrying {recipient_email} (attempt {retry_count + 1})...")
                await asyncio.sleep(5)
                return await self.send_single_email(university_name, recipient_email, retry_count + 1)

            return False, error_msg

    async def send_test_email(self, test_recipient: str) -> bool:
        """
        Send a test email to verify SMTP configuration.
        
        Args:
            test_recipient: Email address to send test to
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Sending test email to {test_recipient}")

        success, error = await self.send_single_email(
            "Test University",
            test_recipient
        )

        if success:
            logger.info("✓ Test email sent successfully")
        else:
            logger.error(f"✗ Test email failed: {error}")

        return success


def validate_smtp_config() -> bool:
    """
    Validate SMTP configuration.
    
    Returns:
        True if valid, False otherwise
    """
    if not config.SENDER_EMAIL:
        logger.error("SENDER_EMAIL not configured in config.py")
        return False

    if not config.SENDER_PASSWORD:
        logger.error("SENDER_PASSWORD not configured in config.py")
        return False

    if '@' not in config.SENDER_EMAIL:
        logger.error("SENDER_EMAIL is not a valid email address")
        return False

    logger.info("SMTP configuration validated")
    return True
