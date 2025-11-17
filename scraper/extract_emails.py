"""
Extract and validate email addresses from crawled pages.

Uses regex patterns and comprehensive validation to ensure high-quality contact emails.
"""

import re
import csv
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict

from bs4 import BeautifulSoup

import config
from utils.logger import setup_logger
from utils.validators import (
    is_valid_email,
    is_university_email,
    is_invalid_email_prefix,
    is_priority_email,
    email_matches_domain,
    validate_email_comprehensive
)

logger = setup_logger(__name__)


class EmailExtractor:
    """Extract and validate emails from HTML content."""

    def __init__(self):
        """Initialize email extractor."""
        self.email_pattern = re.compile(config.VALID_EMAIL_PATTERN, re.IGNORECASE)

    def extract_emails_from_html(self, html: str) -> Set[str]:
        """
        Extract all email addresses from HTML content.
        
        Args:
            html: HTML content as string
        
        Returns:
            Set of unique email addresses found
        """
        emails = set()

        # Extract from text content
        text_emails = self.email_pattern.findall(html)
        emails.update(text_emails)

        # Extract from mailto links
        try:
            soup = BeautifulSoup(html, 'lxml')
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))

            for link in mailto_links:
                href = link.get('href', '')
                # Remove 'mailto:' prefix and any parameters
                email = href.replace('mailto:', '').split('?')[0].strip()
                if email:
                    emails.add(email)
        except Exception as e:
            logger.debug(f"Error parsing HTML for mailto links: {e}")

        return emails

    def validate_and_filter_emails(
            self,
            emails: Set[str],
            university_domain: str
    ) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Validate emails and filter out invalid ones.
        
        Args:
            emails: Set of email addresses
            university_domain: University domain for validation
        
        Returns:
            Tuple of (valid_emails, discarded_emails_with_reasons)
        """
        valid_emails = []
        discarded = []

        for email in emails:
            email = email.lower().strip()

            is_valid, reason = validate_email_comprehensive(email, university_domain)

            if is_valid:
                valid_emails.append(email)
            else:
                discarded.append((email, reason))
                logger.debug(f"Discarded {email}: {reason}")

        return valid_emails, discarded

    def prioritize_emails(self, emails: List[str]) -> List[str]:
        """
        Sort emails by priority (admissions@, info@, etc. first).
        
        Args:
            emails: List of email addresses
        
        Returns:
            Sorted list with priority emails first
        """
        priority = []
        regular = []

        for email in emails:
            if is_priority_email(email):
                priority.append(email)
            else:
                regular.append(email)

        return priority + regular

    def extract_from_university(
            self,
            crawl_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract emails from all pages of a university.
        
        Args:
            crawl_result: Result from crawling a university
        
        Returns:
            Dictionary with university info and extracted emails
        """
        name = crawl_result['name']
        domains = crawl_result['domains']
        pages = crawl_result['pages']

        if not pages:
            logger.debug(f"{name}: No pages to extract from")
            return {
                'name': name,
                'domains': domains,
                'emails': [],
                'discarded': [],
                'pages_processed': 0
            }

        # Extract emails from all pages
        all_emails = set()

        for page in pages:
            page_emails = self.extract_emails_from_html(page['content'])
            all_emails.update(page_emails)

        # Use primary domain for validation
        primary_domain = domains[0] if domains else ''

        # Validate and filter
        valid_emails, discarded = self.validate_and_filter_emails(
            all_emails,
            primary_domain
        )

        # Remove duplicates and prioritize
        valid_emails = list(set(valid_emails))
        valid_emails = self.prioritize_emails(valid_emails)

        logger.info(f"{name}: Extracted {len(valid_emails)} valid emails ({len(discarded)} discarded)")

        return {
            'name': name,
            'domains': domains,
            'emails': valid_emails,
            'discarded': discarded,
            'pages_processed': len(pages)
        }


def extract_all_emails(
        crawl_results: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Extract emails from all crawled universities.
    
    Args:
        crawl_results: List of crawl results
    
    Returns:
        List of extraction results
    """
    logger.info(f"Extracting emails from {len(crawl_results)} universities")

    extractor = EmailExtractor()
    results = []

    total_emails = 0
    total_discarded = 0
    universities_with_emails = 0

    for crawl_result in crawl_results:
        result = extractor.extract_from_university(crawl_result)
        results.append(result)

        email_count = len(result['emails'])
        total_emails += email_count
        total_discarded += len(result['discarded'])

        if email_count > 0:
            universities_with_emails += 1

    logger.info(f"Extraction complete: {total_emails} valid emails from {universities_with_emails} universities")
    logger.info(f"Discarded {total_discarded} invalid emails")

    return results


def save_emails_to_csv(extraction_results: List[Dict[str, Any]]) -> None:
    """
    Save extracted emails to CSV file.
    
    Args:
        extraction_results: List of extraction results
    """
    rows = []

    for result in extraction_results:
        university_name = result['name']
        domains = ', '.join(result['domains'])

        for email in result['emails']:
            rows.append({
                'university': university_name,
                'domains': domains,
                'email': email,
                'is_priority': is_priority_email(email)
            })

    if rows:
        # Remove duplicates based on university + email
        unique_rows = []
        seen = set()
        for row in rows:
            key = (row['university'], row['email'])
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)

        # Sort by priority, then university
        unique_rows.sort(key=lambda x: (not x['is_priority'], x['university']))

        # Write to CSV
        with open(config.EMAILS_EXTRACTED_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['university', 'domains', 'email', 'is_priority'])
            writer.writeheader()
            writer.writerows(unique_rows)

        logger.info(f"Saved {len(unique_rows)} unique emails to {config.EMAILS_EXTRACTED_CSV}")
    else:
        logger.warning("No emails to save to CSV")


def load_emails_from_csv() -> List[Dict[str, Any]]:
    """
    Load emails from CSV file.
    
    Returns:
        List of email dictionaries
    
    Raises:
        FileNotFoundError: If CSV file doesn't exist
    """
    try:
        with open(config.EMAILS_EXTRACTED_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            emails = list(reader)

        logger.info(f"Loaded {len(emails)} emails from {config.EMAILS_EXTRACTED_CSV}")
        return emails
    except FileNotFoundError:
        logger.error(f"Emails CSV not found: {config.EMAILS_EXTRACTED_CSV}")
        raise
