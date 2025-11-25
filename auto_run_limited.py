#!/usr/bin/env python3
"""
University Outreach Automation - LIMITED TEST RUN

Same as auto_run.py but only processes first 10 universities for testing.
"""

import sys
import os
from pathlib import Path

# Auto-detect project root
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Import the main auto_run module
from auto_run import (
    run_fetch, run_crawl, run_extract_and_rank,
    run_send_emails, print_final_summary,
    PipelineStats, logger
)
from utils.db import Database
import config


def main():
    """Run the pipeline on only 10 universities for testing."""
    stats = PipelineStats()
    db = None

    try:
        logger.info("=" * 80)
        logger.info("🧪 AUTO RUN - LIMITED TEST (10 Universities)")
        logger.info("=" * 80)
        logger.info("")

        # Initialize database
        db = Database()

        # Step 1: Fetch universities
        universities = run_fetch()

        # LIMIT TO 10
        universities = universities[:10]
        logger.info(f"🎯 LIMITED TO: {len(universities)} universities for testing")
        logger.info("")

        stats.universities_fetched = len(universities)

        # Step 2: Crawl
        crawl_results = run_crawl(universities)
        stats.universities_crawled = len(crawl_results)
        stats.pages_found = sum(r['pages_found_count'] for r in crawl_results)

        # Step 3: Extract and rank
        extraction_results = run_extract_and_rank(crawl_results, db)
        stats.emails_extracted = sum(len(r['emails']) for r in extraction_results)
        stats.emails_ranked = stats.emails_extracted

        # Step 4: Send emails
        run_send_emails(extraction_results, db, stats)

        # Step 5: Summary
        print_final_summary(stats, db)

        logger.info("🎊 Test run completed!")

    except KeyboardInterrupt:
        logger.warning("⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if db:
            db.close()


if __name__ == "__main__":
    main()
