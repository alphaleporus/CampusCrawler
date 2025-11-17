"""
University Merch Bot - Main Entry Point

Complete automation system for scraping university contact info and sending
personalized outreach emails.

Author: Gaurav Sharma
"""

import asyncio
import sys
from typing import Optional

import config
from utils.logger import setup_logger, log_statistics
from utils.db import Database
from scraper.fetch_universities import fetch_universities, load_universities
from scraper.crawl_contact_pages import crawl_all_universities
from scraper.extract_emails import extract_all_emails, save_emails_to_csv, load_emails_from_csv
from emailer.send_email import validate_smtp_config
from emailer.throttle import send_all_pending_emails

logger = setup_logger(__name__)


def step_1_fetch_universities(force_refresh: bool = False) -> list:
    """
    Step 1: Fetch list of US universities from API.
    
    Args:
        force_refresh: If True, re-fetch even if file exists
    
    Returns:
        List of university dictionaries
    """
    logger.info("=" * 80)
    logger.info("STEP 1: Fetching US Universities")
    logger.info("=" * 80)

    # Check if we already have the data
    if not force_refresh and config.UNIVERSITIES_RAW_JSON.exists():
        logger.info("Universities file already exists. Loading from file...")
        universities = load_universities()
    else:
        universities = fetch_universities()

    logger.info(f"Loaded {len(universities)} universities")
    return universities


def step_2_crawl_contact_pages(
        universities: list,
        limit: Optional[int] = None
) -> list:
    """
    Step 2: Crawl contact pages from university websites.
    
    Args:
        universities: List of university dictionaries
        limit: Optional limit on number to crawl
    
    Returns:
        List of crawl results
    """
    logger.info("=" * 80)
    logger.info("STEP 2: Crawling Contact Pages")
    logger.info("=" * 80)

    if limit:
        logger.info(f"Limiting crawl to {limit} universities")

    crawl_results = crawl_all_universities(universities, limit=limit)

    # Statistics
    total_pages = sum(r['pages_found_count'] for r in crawl_results)
    unis_with_pages = sum(1 for r in crawl_results if r['pages_found_count'] > 0)

    stats = {
        'Universities Crawled': len(crawl_results),
        'Universities with Contact Pages': unis_with_pages,
        'Total Pages Found': total_pages
    }
    log_statistics(logger, stats)

    return crawl_results


def step_3_extract_emails(crawl_results: list) -> list:
    """
    Step 3: Extract and validate email addresses.
    
    Args:
        crawl_results: List of crawl results
    
    Returns:
        List of extraction results
    """
    logger.info("=" * 80)
    logger.info("STEP 3: Extracting & Validating Emails")
    logger.info("=" * 80)

    extraction_results = extract_all_emails(crawl_results)

    # Save to CSV
    save_emails_to_csv(extraction_results)

    # Statistics
    total_emails = sum(len(r['emails']) for r in extraction_results)
    total_discarded = sum(len(r['discarded']) for r in extraction_results)
    unis_with_emails = sum(1 for r in extraction_results if len(r['emails']) > 0)

    stats = {
        'Universities Processed': len(extraction_results),
        'Universities with Valid Emails': unis_with_emails,
        'Valid Emails Extracted': total_emails,
        'Emails Discarded': total_discarded
    }
    log_statistics(logger, stats)

    return extraction_results


def step_4_populate_database(extraction_results: list) -> None:
    """
    Step 4: Populate database with extracted emails.
    
    Args:
        extraction_results: List of extraction results
    """
    logger.info("=" * 80)
    logger.info("STEP 4: Populating Database")
    logger.info("=" * 80)

    db = Database()

    try:
        inserted = 0
        duplicates = 0

        for result in extraction_results:
            university = result['name']

            for email in result['emails']:
                record_id = db.insert_email(university, email)

                if record_id:
                    inserted += 1
                else:
                    duplicates += 1

        stats = {
            'New Records Inserted': inserted,
            'Duplicates Skipped': duplicates,
            'Total Records': inserted + duplicates
        }
        log_statistics(logger, stats)

    finally:
        db.close()


def step_5_send_emails(dry_run: bool = False, limit: Optional[int] = None) -> dict:
    """
    Step 5: Send personalized emails with throttling.
    
    Args:
        dry_run: If True, don't actually send emails
        limit: Optional limit on number to send
    
    Returns:
        Dictionary with sending statistics
    """
    logger.info("=" * 80)
    logger.info("STEP 5: Sending Personalized Emails")
    logger.info("=" * 80)

    if dry_run:
        logger.warning("DRY RUN MODE: No emails will actually be sent")

    # Validate SMTP config
    if not dry_run and not validate_smtp_config():
        logger.error("SMTP configuration invalid. Please update config.py")
        logger.error("Set SENDER_EMAIL and SENDER_PASSWORD")
        return {'attempted': 0, 'sent': 0, 'failed': 0, 'skipped': 0}

    # Send emails
    stats = asyncio.run(send_all_pending_emails(dry_run=dry_run, limit=limit))

    log_statistics(logger, stats)

    return stats


def step_6_show_summary() -> None:
    """Step 6: Show final summary and statistics."""
    logger.info("=" * 80)
    logger.info("STEP 6: Final Summary")
    logger.info("=" * 80)

    db = Database()

    try:
        stats = db.get_statistics()

        # Calculate success rate
        total = stats.get('TOTAL', 0)
        sent = stats.get(config.STATUS_SENT, 0)
        complete = stats.get(config.STATUS_COMPLETE, 0)
        failed = stats.get(config.STATUS_FAILED, 0)

        success_rate = (sent / total * 100) if total > 0 else 0

        summary = {
            'Total Emails in Database': total,
            'Successfully Sent': sent,
            'Failed': failed,
            'Pending': stats.get(config.STATUS_PENDING, 0),
            'Retrying': stats.get(config.STATUS_RETRYING, 0),
            'Success Rate': f"{success_rate:.1f}%"
        }

        log_statistics(logger, summary)

    finally:
        db.close()


def main(
        skip_fetch: bool = False,
        skip_crawl: bool = False,
        skip_extract: bool = False,
        skip_email: bool = False,
        crawl_limit: Optional[int] = None,
        email_limit: Optional[int] = None,
        dry_run: bool = True
) -> None:
    """
    Main orchestration function.
    
    Args:
        skip_fetch: Skip fetching universities
        skip_crawl: Skip crawling contact pages
        skip_extract: Skip email extraction
        skip_email: Skip sending emails
        crawl_limit: Limit number of universities to crawl
        email_limit: Limit number of emails to send
        dry_run: If True, don't actually send emails
    """
    logger.info("=" * 80)
    logger.info("UNIVERSITY MERCH BOT - STARTING")
    logger.info("=" * 80)

    try:
        # Step 1: Fetch universities
        if not skip_fetch:
            universities = step_1_fetch_universities()
        else:
            logger.info("Skipping Step 1 (fetch universities)")
            universities = load_universities()

        # Step 2: Crawl contact pages
        if not skip_crawl:
            crawl_results = step_2_crawl_contact_pages(universities, limit=crawl_limit)
        else:
            logger.info("Skipping Step 2 (crawl contact pages)")
            crawl_results = []

        # Step 3: Extract emails
        if not skip_extract and crawl_results:
            extraction_results = step_3_extract_emails(crawl_results)

            # Step 4: Populate database
            step_4_populate_database(extraction_results)
        else:
            if skip_extract:
                logger.info("Skipping Step 3 (extract emails)")
            else:
                logger.info("No crawl results to extract from")

        # Step 5: Send emails
        if not skip_email:
            step_5_send_emails(dry_run=dry_run, limit=email_limit)
        else:
            logger.info("Skipping Step 5 (send emails)")

        # Step 6: Final summary
        step_6_show_summary()

        logger.info("=" * 80)
        logger.info("UNIVERSITY MERCH BOT - COMPLETED")
        logger.info("=" * 80)

    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="University Merch Bot - Automated University Outreach System"
    )

    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip fetching universities (use existing data)"
    )

    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip crawling contact pages"
    )

    parser.add_argument(
        "--skip-extract",
        action="store_true",
        help="Skip email extraction"
    )

    parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Skip sending emails"
    )

    parser.add_argument(
        "--crawl-limit",
        type=int,
        help="Limit number of universities to crawl"
    )

    parser.add_argument(
        "--email-limit",
        type=int,
        help="Limit number of emails to send"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually send emails (default is dry-run)"
    )

    args = parser.parse_args()

    # Run main pipeline
    main(
        skip_fetch=args.skip_fetch,
        skip_crawl=args.skip_crawl,
        skip_extract=args.skip_extract,
        skip_email=args.skip_email,
        crawl_limit=args.crawl_limit,
        email_limit=args.email_limit,
        dry_run=not args.live
    )
