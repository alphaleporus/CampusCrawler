"""
Email throttling and rate limiting.

Ensures natural sending patterns with delays and jitter to avoid spam detection.
"""

import asyncio
import random
from typing import List, Dict, Any, Optional

import config
from utils.logger import setup_logger
from utils.db import Database
from emailer.send_email import EmailSender

logger = setup_logger(__name__)


class ThrottledEmailSender:
    """Email sender with throttling and rate limiting."""

    def __init__(
            self,
            sender: EmailSender,
            db: Database,
            throttle_delay: float = config.EMAIL_THROTTLE_DELAY,
            jitter_min: float = config.EMAIL_JITTER_MIN,
            jitter_max: float = config.EMAIL_JITTER_MAX
    ):
        """
        Initialize throttled sender.
        
        Args:
            sender: EmailSender instance
            db: Database instance
            throttle_delay: Base delay between emails in seconds
            jitter_min: Minimum random jitter in seconds
            jitter_max: Maximum random jitter in seconds
        """
        self.sender = sender
        self.db = db
        self.throttle_delay = throttle_delay
        self.jitter_min = jitter_min
        self.jitter_max = jitter_max

    def _get_delay_with_jitter(self) -> float:
        """
        Calculate delay with random jitter.
        
        Returns:
            Total delay in seconds
        """
        jitter = random.uniform(self.jitter_min, self.jitter_max)
        return self.throttle_delay + jitter

    async def send_emails_batch(
            self,
            emails_data: List[Dict[str, Any]],
            dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Send a batch of emails with throttling.
        
        Args:
            emails_data: List of email records from database
            dry_run: If True, don't actually send emails
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'attempted': 0,
            'sent': 0,
            'failed': 0,
            'skipped': 0
        }

        total = len(emails_data)
        logger.info(f"Starting batch send of {total} emails (dry_run={dry_run})")

        for idx, email_record in enumerate(emails_data, 1):
            university = email_record['university']
            email = email_record['email']
            retry_count = email_record['retry_count']

            # Skip if retry limit exceeded
            if retry_count >= config.EMAIL_MAX_RETRIES:
                logger.warning(f"Skipping {email} - retry limit exceeded")
                stats['skipped'] += 1
                continue

            stats['attempted'] += 1

            logger.info(f"[{idx}/{total}] Processing {email} ({university})")

            if dry_run:
                logger.info(f"DRY RUN: Would send to {email}")
                success = True
                error = None
            else:
                # Update status to RETRYING if this is a retry
                if retry_count > 0:
                    self.db.update_status(email, config.STATUS_RETRYING)

                # Send email
                success, error = await self.sender.send_single_email(university, email)

            # Update database
            if success:
                self.db.update_status(email, config.STATUS_SENT, error=None)
                stats['sent'] += 1
            else:
                if retry_count + 1 >= config.EMAIL_MAX_RETRIES:
                    self.db.update_status(email, config.STATUS_FAILED, error=error)
                else:
                    self.db.update_status(
                        email,
                        config.STATUS_RETRYING,
                        error=error,
                        increment_retry=True
                    )
                stats['failed'] += 1

            # Throttle (except for last email)
            if idx < total:
                delay = self._get_delay_with_jitter()
                logger.info(f"Waiting {delay:.1f} seconds before next email...")
                await asyncio.sleep(delay)

        logger.info("Batch send complete")
        logger.info(f"Attempted: {stats['attempted']}, Sent: {stats['sent']}, "
                    f"Failed: {stats['failed']}, Skipped: {stats['skipped']}")

        return stats


async def send_all_pending_emails(
        dry_run: bool = False,
        limit: Optional[int] = None
) -> Dict[str, int]:
    """
    Send all pending emails from database with throttling.
    
    Args:
        dry_run: If True, don't actually send emails
        limit: Optional limit on number of emails to send
    
    Returns:
        Dictionary with statistics
    """
    db = Database()
    sender = EmailSender()
    throttled_sender = ThrottledEmailSender(sender, db)

    try:
        # Get pending emails
        pending_emails = db.get_pending_emails(limit=limit)

        if not pending_emails:
            logger.info("No pending emails to send")
            return {'attempted': 0, 'sent': 0, 'failed': 0, 'skipped': 0}

        # Send with throttling
        stats = await throttled_sender.send_emails_batch(pending_emails, dry_run=dry_run)

        return stats

    finally:
        db.close()
