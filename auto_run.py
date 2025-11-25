#!/usr/bin/env python3
"""
University Outreach Automation - Complete Pipeline Runner

This script executes the full production workflow:
1. Fetch all US universities from API
2. Crawl all university websites for contact pages
3. Extract and rank emails (top 3 per university)
4. Send personalized emails to Primary, Secondary, and Tertiary contacts
5. Generate final statistics report

NO FLAGS. NO DRY RUN. NO TESTING.
Pure production execution in one command: python3 auto_run.py

Author: Gaurav Sharma
"""

import sys
import os
import asyncio
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Auto-detect project root and add to path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Import project modules
import config
from utils.logger import setup_logger, log_statistics
from utils.db import Database
from scraper.fetch_universities import fetch_universities
from scraper.crawl_contact_pages import crawl_all_universities
from scraper.extract_emails import extract_all_emails
from emailer.send_email import EmailSender, GmailDailyLimitError
from emailer.template import generate_email

# Setup logging
logger = setup_logger(__name__)


class PipelineStats:
    """Track statistics across the entire pipeline."""

    def __init__(self):
        self.start_time = datetime.now()
        self.universities_fetched = 0
        self.universities_crawled = 0
        self.pages_found = 0
        self.emails_extracted = 0
        self.emails_ranked = 0
        self.emails_sent = 0
        self.emails_failed = 0
        self.universities_processed = 0

    def get_duration(self) -> str:
        """Get total duration as formatted string."""
        delta = datetime.now() - self.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"


def run_fetch() -> List[Dict[str, Any]]:
    """
    Step 1: Fetch all US universities from API.
    
    Uses multi-source fallback (Hipolabs API → GitHub repository).
    Stores results in data/universities_raw.json.
    
    Returns:
        List of university dictionaries
    """
    logger.info("=" * 80)
    logger.info("STEP 1: FETCHING US UNIVERSITIES")
    logger.info("=" * 80)

    try:
        universities = fetch_universities()
        logger.info(f"✓ Successfully fetched {len(universities)} universities")
        return universities

    except Exception as e:
        logger.error(f"✗ Failed to fetch universities: {e}")
        raise


def run_crawl(universities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Step 2: Crawl all university websites for contact pages.
    
    Hits all standard paths: /contact, /admissions, /international, etc.
    Uses async crawling with proper throttling and error handling.
    
    Args:
        universities: List of university data
    
    Returns:
        List of crawl results with page content
    """
    logger.info("=" * 80)
    logger.info("STEP 2: CRAWLING UNIVERSITY WEBSITES")
    logger.info("=" * 80)
    logger.info(f"Will crawl {len(universities)} universities...")

    try:
        crawl_results = crawl_all_universities(universities)

        total_pages = sum(r['pages_found_count'] for r in crawl_results)
        unis_with_pages = sum(1 for r in crawl_results if r['pages_found_count'] > 0)

        logger.info(f"✓ Crawled {len(crawl_results)} universities")
        logger.info(f"✓ Found {total_pages} contact pages from {unis_with_pages} universities")

        return crawl_results

    except Exception as e:
        logger.error(f"✗ Crawling failed: {e}")
        raise


def run_extract_and_rank(
        crawl_results: List[Dict[str, Any]],
        db: Database
) -> List[Dict[str, Any]]:
    """
    Step 3: Extract emails and rank contacts using the 3-tier system.
    
    For each university:
    - Extracts all emails from crawled pages
    - Scores and ranks using contact_ranker
    - Selects top 3 (Primary, Secondary, Tertiary)
    - Saves to database
    
    Args:
        crawl_results: List of crawl results
        db: Database instance
    
    Returns:
        List of extraction results with ranked contacts
    """
    logger.info("=" * 80)
    logger.info("STEP 3: EXTRACTING & RANKING CONTACT EMAILS")
    logger.info("=" * 80)

    try:
        extraction_results = extract_all_emails(crawl_results)

        # Save top 3 emails to database
        inserted = 0
        for result in extraction_results:
            university = result['name']

            # Insert each of the top 3 emails
            for email in result['emails']:
                record_id = db.insert_email(university, email, config.STATUS_PENDING)
                if record_id:
                    inserted += 1

        total_emails = sum(len(r['emails']) for r in extraction_results)
        unis_with_emails = sum(1 for r in extraction_results if len(r['emails']) > 0)

        logger.info(f"✓ Extracted emails from {len(extraction_results)} universities")
        logger.info(f"✓ Selected {total_emails} top-ranked contacts from {unis_with_emails} universities")
        logger.info(f"✓ Inserted {inserted} emails into database")

        return extraction_results

    except Exception as e:
        logger.error(f"✗ Extraction failed: {e}")
        raise


async def send_university_emails(
        university_name: str,
        emails: List[str],
        sender: EmailSender,
        db: Database,
        stats: PipelineStats,
        limit: int
) -> Tuple[int, int]:
    """
    Send emails to a single university's contacts.
    
    Sends in order: Primary → Secondary → Tertiary
    With throttling between each send.
    
    Args:
        university_name: Name of university
        emails: List of up to 3 ranked emails
        sender: EmailSender instance
        db: Database instance
        stats: Pipeline statistics
        limit: Remaining email limit
    
    Returns:
        Tuple of (sent_count, failed_count)
    """
    sent = 0
    failed = 0

    contact_labels = ['PRIMARY', 'SECONDARY', 'TERTIARY']

    for idx, email in enumerate(emails):
        if sent >= limit:
            logger.warning("⚠️  Daily limit reached! Stopping email sending.")
            break

        label = contact_labels[idx] if idx < len(contact_labels) else 'EXTRA'

        try:
            logger.info(f"📧 Sending to {label}: {email} ({university_name})")

            # Send email
            success, error = await sender.send_single_email(university_name, email)

            if success:
                db.update_status(email, config.STATUS_SENT, error=None)
                sent += 1
                stats.emails_sent += 1
                logger.info(f"   ✓ Sent successfully")
            else:
                db.update_status(email, config.STATUS_FAILED, error=error)
                failed += 1
                stats.emails_failed += 1
                logger.error(f"   ✗ Failed: {error}")

            # Throttle between emails (except last one for this university)
            if idx < len(emails) - 1:
                delay = config.EMAIL_THROTTLE_DELAY + random.uniform(
                    config.EMAIL_JITTER_MIN,
                    config.EMAIL_JITTER_MAX
                )
                logger.info(f"   ⏱️  Waiting {delay:.1f} seconds...")
                await asyncio.sleep(delay)

        except GmailDailyLimitError as e:
            logger.error(f"   ✗ Gmail daily limit reached: {e}")
            db.update_status(email, config.STATUS_FAILED, error=str(e))
            failed += 1
            stats.emails_failed += 1
            break

        except Exception as e:
            logger.error(f"   ✗ Exception sending to {email}: {e}")
            db.update_status(email, config.STATUS_FAILED, error=str(e))
            failed += 1
            stats.emails_failed += 1

    return sent, failed


async def run_send_emails_async(
        extraction_results: List[Dict[str, Any]],
        db: Database,
        stats: PipelineStats
) -> None:
    """
    Step 4: Send emails to all universities (async implementation).
    
    For each university with ranked contacts:
    - Check if university already has sent emails (skip if yes)
    - Check daily email limit (stop if reached)
    - Send to Primary contact
    - Send to Secondary contact (if exists)
    - Send to Tertiary contact (if exists)
    - Update database status
    - Throttle between sends
    
    Args:
        extraction_results: List of extraction results
        db: Database instance
        stats: Pipeline statistics
    """
    logger.info("=" * 80)
    logger.info("STEP 4: SENDING PERSONALIZED EMAILS")
    logger.info("=" * 80)
    logger.info("⚠️  LIVE MODE - Real emails will be sent!")

    # Validate SMTP config
    if not config.SENDER_EMAIL or not config.SENDER_PASSWORD:
        logger.error("✗ SMTP credentials not configured!")
        logger.error("  Update .env file with SENDER_EMAIL and SENDER_PASSWORD")
        raise ValueError("SMTP credentials missing")

    logger.info(f"✓ Sending from: {config.SENDER_EMAIL}")

    # Check how many emails have been sent today
    emails_sent_today = db.get_emails_sent_today()
    emails_sent_last_24h = db.get_emails_sent_last_24h()
    daily_limit = config.GMAIL_DAILY_LIMIT

    # Use the rolling 24-hour window for limit enforcement (Gmail's actual behavior)
    emails_sent_for_limit = emails_sent_last_24h
    remaining_today = daily_limit - emails_sent_for_limit

    logger.info("=" * 80)
    logger.info("📊 DAILY LIMIT STATUS")
    logger.info("=" * 80)
    logger.info(f"Gmail Daily Limit:       {daily_limit} emails/day")
    logger.info(f"Emails Sent Today:       {emails_sent_today} (since midnight)")
    logger.info(f"Emails Sent (24h):       {emails_sent_last_24h} (rolling 24h window)")
    logger.info(f"Remaining Capacity:      {remaining_today}")
    logger.info("")
    logger.info("ℹ️  Gmail enforces a ROLLING 24-hour limit, not calendar day")
    logger.info("=" * 80)
    logger.info("")

    if remaining_today <= 0:
        logger.warning("⚠️  Daily email limit reached! No emails will be sent.")
        logger.warning("   Gmail uses a rolling 24-hour window.")
        logger.warning("   Wait a few hours and try again, or increase GMAIL_DAILY_LIMIT in config.py")
        return

    sender = EmailSender()

    # Filter to only universities with emails AND that haven't been contacted yet
    universities_to_email = []
    skipped_already_sent = 0

    for result in extraction_results:
        if not result['emails']:
            continue

        university_name = result['name']

        # Skip if this university already has sent emails
        if db.university_has_sent_emails(university_name):
            logger.debug(f"Skipping {university_name} - already contacted")
            skipped_already_sent += 1
            continue

        universities_to_email.append(result)

    logger.info(f"📨 Universities to contact: {len(universities_to_email)}")
    logger.info(f"⏭️  Universities skipped (already contacted): {skipped_already_sent}")

    # Calculate how many emails we can send
    total_emails_to_send = sum(len(r['emails']) for r in universities_to_email)
    emails_we_can_send = min(total_emails_to_send, remaining_today)

    logger.info(f"📧 Total emails queued: {total_emails_to_send}")
    logger.info(f"📧 Emails we can send today: {emails_we_can_send}")

    if total_emails_to_send > remaining_today:
        logger.warning(f"⚠️  Warning: {total_emails_to_send - remaining_today} emails will be deferred to next run")

    logger.info(f"⏱️  Estimated time: ~{emails_we_can_send * 0.75:.0f} minutes")
    logger.info("")

    if len(universities_to_email) == 0:
        logger.info("✓ No universities to contact (all already contacted)")
        return

    emails_sent_this_run = 0

    try:
        for idx, result in enumerate(universities_to_email, 1):
            # Check if we've hit the daily limit
            if emails_sent_for_limit + emails_sent_this_run >= daily_limit:
                logger.warning("")
                logger.warning("=" * 80)
                logger.warning("⚠️  DAILY LIMIT REACHED")
                logger.warning("=" * 80)
                logger.warning(f"Sent {emails_sent_this_run} emails in this run")
                logger.warning(f"Total sent (24h): {emails_sent_for_limit + emails_sent_this_run}/{daily_limit}")
                logger.warning(f"Remaining universities: {len(universities_to_email) - idx + 1}")
                logger.warning("These will be processed in the next run.")
                logger.warning("=" * 80)
                break

            university_name = result['name']
            emails = result['emails']

            logger.info(f"[{idx}/{len(universities_to_email)}] Processing: {university_name}")
            logger.info(f"   Contacts: {len(emails)} email(s)")

            # Send emails but respect the daily limit
            sent, failed = await send_university_emails(
                university_name,
                emails,
                sender,
                db,
                stats,
                daily_limit - (emails_sent_for_limit + emails_sent_this_run)
            )

            emails_sent_this_run += sent
            stats.universities_processed += 1

            logger.info(f"   ✓ University complete: {sent} sent, {failed} failed")
            logger.info(f"   📊 Progress: {emails_sent_this_run}/{emails_we_can_send} emails sent this run")

            # Check if we've reached the limit after sending
            if emails_sent_for_limit + emails_sent_this_run >= daily_limit:
                logger.warning("")
                logger.warning("⚠️  Daily limit reached after processing this university")
                break

            # Throttle between universities (except last one)
            if idx < len(universities_to_email):
                delay = random.uniform(5, 10)  # Extra delay between universities
                logger.info(f"   ⏸️  Pausing {delay:.1f} seconds before next university...")
                logger.info("")
                await asyncio.sleep(delay)

    except GmailDailyLimitError as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("🛑 GMAIL DAILY LIMIT EXCEEDED")
        logger.error("=" * 80)
        logger.error(f"Gmail has rejected further emails: {e}")
        logger.error(f"Emails sent in this run: {emails_sent_this_run}")
        logger.error(f"Total sent (24h): {emails_sent_for_limit + emails_sent_this_run}/{daily_limit}")
        logger.error("")
        logger.error("IMPORTANT NOTES:")
        logger.error("  • Gmail enforces a rolling 24-hour limit")
        logger.error("  • Your account may have been flagged for bulk sending")
        logger.error("  • All progress has been saved to the database")
        logger.error("")
        logger.error("RECOMMENDED ACTIONS:")
        logger.error("  1. Wait 24-48 hours before trying again")
        logger.error("  2. Reduce GMAIL_DAILY_LIMIT in .env (try 200 instead of 450)")
        logger.error("  3. Increase EMAIL_THROTTLE_DELAY in .env (try 60+ seconds)")
        logger.error("  4. Check your Gmail Sent folder for other email activity")
        logger.error("")
        logger.error("To check when you can send again:")
        logger.error("  python3 check_send_time.py")
        logger.error("=" * 80)
        logger.error("")

        # Re-raise to stop the entire pipeline
        raise

    logger.info("=" * 80)
    logger.info("✓ Email sending complete!")
    logger.info(f"📊 Sent {emails_sent_this_run} emails in this run")
    logger.info(f"📊 Total sent (24h): {emails_sent_for_limit + emails_sent_this_run}/{daily_limit}")
    logger.info("=" * 80)


def run_send_emails(
        extraction_results: List[Dict[str, Any]],
        db: Database,
        stats: PipelineStats
) -> None:
    """
    Synchronous wrapper for async email sending.
    
    Args:
        extraction_results: List of extraction results
        db: Database instance
        stats: Pipeline statistics
    """
    asyncio.run(run_send_emails_async(extraction_results, db, stats))


def print_final_summary(stats: PipelineStats, db: Database) -> None:
    """
    Print comprehensive final summary.
    
    Args:
        stats: Pipeline statistics
        db: Database instance
    """
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 PIPELINE COMPLETE - FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info("")

    # Pipeline stats
    logger.info("📊 PIPELINE STATISTICS:")
    logger.info(f"   Universities Fetched:    {stats.universities_fetched}")
    logger.info(f"   Universities Crawled:    {stats.universities_crawled}")
    logger.info(f"   Contact Pages Found:     {stats.pages_found}")
    logger.info(f"   Emails Extracted:        {stats.emails_extracted}")
    logger.info(f"   Universities Processed:  {stats.universities_processed}")
    logger.info("")

    # Email sending stats
    logger.info("📧 EMAIL STATISTICS:")
    logger.info(f"   Total Sent:              {stats.emails_sent}")
    logger.info(f"   Total Failed:            {stats.emails_failed}")

    success_rate = (stats.emails_sent / (stats.emails_sent + stats.emails_failed) * 100) if (
                                                                                                        stats.emails_sent + stats.emails_failed) > 0 else 0
    logger.info(f"   Success Rate:            {success_rate:.1f}%")
    logger.info("")

    # Daily limit status
    emails_sent_today = db.get_emails_sent_today()
    emails_sent_last_24h = db.get_emails_sent_last_24h()
    daily_limit = config.GMAIL_DAILY_LIMIT
    remaining_today = daily_limit - emails_sent_last_24h

    logger.info("📊 DAILY LIMIT STATUS:")
    logger.info(f"   Gmail Daily Limit:       {daily_limit} emails/day")
    logger.info(f"   Sent Today (midnight):   {emails_sent_today}")
    logger.info(f"   Sent (24h rolling):      {emails_sent_last_24h}")
    logger.info(f"   Remaining Capacity:      {remaining_today}")
    logger.info("")
    logger.info("   ℹ️  Gmail enforces ROLLING 24-hour limits")

    if remaining_today > 0:
        logger.info(f"   Status:                  ✓ Can send {remaining_today} more emails")
    else:
        logger.info(f"   Status:                  ⚠️  Daily limit reached")
        logger.info(f"   Note:                    Wait a few hours for the rolling window to open up")
    logger.info("")

    # Database stats
    db_stats = db.get_statistics()
    logger.info("💾 DATABASE STATUS:")
    for status, count in db_stats.items():
        logger.info(f"   {status:20s}: {count}")

    # Universities without sent emails
    universities_remaining = db.get_universities_without_sent_emails()
    if universities_remaining:
        logger.info("")
        logger.info(f"📋 REMAINING WORK:")
        logger.info(f"   Universities not yet contacted: {len(universities_remaining)}")
        logger.info(f"   Run auto_run.py again to continue")
    else:
        logger.info("")
        logger.info("✅ ALL UNIVERSITIES CONTACTED")
    logger.info("")

    # Timing
    logger.info("⏱️  EXECUTION TIME:")
    logger.info(f"   Total Duration:          {stats.get_duration()}")
    logger.info("")

    # Files
    logger.info("📁 OUTPUT FILES:")
    logger.info(f"   Universities:            {config.UNIVERSITIES_RAW_JSON}")
    logger.info(f"   Database:                {config.DB_PATH}")
    logger.info(f"   Emails CSV:              {config.EMAILS_EXTRACTED_CSV}")
    logger.info("")

    logger.info("=" * 80)
    logger.info("✅ AUTO-RUN COMPLETE")
    logger.info("=" * 80)


def main() -> None:
    """
    Main execution function.
    
    Orchestrates the complete pipeline:
    1. Fetch universities
    2. Crawl websites
    3. Extract and rank emails
    4. Send personalized emails
    5. Generate summary
    
    No flags, no arguments - just runs the full production workflow.
    """
    stats = PipelineStats()
    db = None

    try:
        logger.info("=" * 80)
        logger.info("🚀 UNIVERSITY OUTREACH AUTOMATION - AUTO RUN")
        logger.info("=" * 80)
        logger.info(f"Started at: {stats.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Project root: {PROJECT_ROOT}")
        logger.info("")

        # Initialize database
        db = Database()

        # Step 1: Fetch universities
        universities = run_fetch()
        stats.universities_fetched = len(universities)

        # Step 2: Crawl websites
        crawl_results = run_crawl(universities)
        stats.universities_crawled = len(crawl_results)
        stats.pages_found = sum(r['pages_found_count'] for r in crawl_results)

        # Step 3: Extract and rank emails
        extraction_results = run_extract_and_rank(crawl_results, db)
        stats.emails_extracted = sum(len(r['emails']) for r in extraction_results)
        stats.emails_ranked = stats.emails_extracted  # All extracted are ranked

        # Step 4: Send emails
        run_send_emails(extraction_results, db, stats)

        # Step 5: Final summary
        print_final_summary(stats, db)

        logger.info("🎊 All operations completed successfully!")

    except GmailDailyLimitError as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ PIPELINE STOPPED: Gmail Daily Limit Reached")
        logger.error("=" * 80)
        logger.error("")
        logger.error("The script has been automatically stopped because Gmail rejected")
        logger.error("further emails due to daily sending limit.")
        logger.error("")
        logger.error("✓ All progress has been saved to the database")
        logger.error("✓ No data was lost")
        logger.error("✓ You can safely resume later")
        logger.error("")
        logger.error("Next steps:")
        logger.error("  1. Wait 24-48 hours")
        logger.error("  2. Run: python3 check_send_time.py")
        logger.error("  3. When ready: python3 auto_run.py")
        logger.error("")
        logger.error("To prevent this in the future:")
        logger.error("  • Lower GMAIL_DAILY_LIMIT in .env to 200")
        logger.error("  • Increase EMAIL_THROTTLE_DELAY to 60+ seconds")
        logger.error("=" * 80)

        sys.exit(2)  # Exit code 2 for daily limit reached

    except KeyboardInterrupt:
        logger.warning("")
        logger.warning("⚠️  Pipeline interrupted by user (Ctrl+C)")
        logger.warning("Partial progress has been saved to database")
        sys.exit(1)

    except Exception as e:
        logger.error("")
        logger.error("=" * 80)
        logger.error("❌ PIPELINE FAILED")
        logger.error("=" * 80)
        logger.error(f"Error: {e}")
        logger.error("")

        import traceback
        logger.error("Full traceback:")
        logger.error(traceback.format_exc())

        sys.exit(1)

    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()
