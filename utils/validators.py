"""
Validation utilities for emails, URLs, and domains.

Ensures data quality and prevents invalid entries from entering the system.
"""

import re
from typing import Optional
from urllib.parse import urlparse

import config


def is_valid_url(url: str) -> bool:
    """
    Validate if a URL is well-formed.
    
    Args:
        url: URL string to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def normalize_url(url: str) -> str:
    """
    Normalize a URL by removing trailing slashes and ensuring https.
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL string
    """
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url.rstrip('/')


def is_valid_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    pattern = config.VALID_EMAIL_PATTERN
    return bool(re.match(pattern, email))


def is_university_email(email: str) -> bool:
    """
    Check if email matches university domain patterns (.edu or university.org).
    
    Args:
        email: Email address to check
    
    Returns:
        True if matches university pattern, False otherwise
    """
    pattern = config.VALID_DOMAIN_SUFFIX_PATTERN
    return bool(re.match(pattern, email, re.IGNORECASE))


def is_invalid_email_prefix(email: str) -> bool:
    """
    Check if email has an invalid prefix (careers@, jobs@, etc.).
    
    Args:
        email: Email address to check
    
    Returns:
        True if email should be discarded, False if it's acceptable
    """
    email_lower = email.lower()
    return any(email_lower.startswith(prefix) for prefix in config.INVALID_EMAIL_PREFIXES)


def is_priority_email(email: str) -> bool:
    """
    Check if email has a priority prefix (admissions@, info@, etc.).
    
    Args:
        email: Email address to check
    
    Returns:
        True if email is high priority, False otherwise
    """
    email_lower = email.lower()
    return any(email_lower.startswith(prefix) for prefix in config.PRIORITY_EMAIL_PREFIXES)


def email_matches_domain(email: str, domain: str) -> bool:
    """
    Verify that email domain is a substring of university domain.
    
    Args:
        email: Email address to check
        domain: University domain
    
    Returns:
        True if email domain matches, False otherwise
    """
    try:
        email_domain = email.split('@')[1].lower()
        domain_clean = domain.lower().replace('www.', '')

        # Check if email domain is part of university domain
        return email_domain in domain_clean or domain_clean in email_domain
    except (IndexError, AttributeError):
        return False


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract domain from
    
    Returns:
        Domain string or None if extraction fails
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.replace('www.', '')
    except Exception:
        return None


def validate_email_comprehensive(email: str, university_domain: str) -> tuple[bool, str]:
    """
    Comprehensive email validation with reason.
    
    Args:
        email: Email to validate
        university_domain: University domain to match against
    
    Returns:
        Tuple of (is_valid, reason)
    """
    if not is_valid_email(email):
        return False, "Invalid email format"

    if not is_university_email(email):
        return False, "Not a university email domain"

    if is_invalid_email_prefix(email):
        return False, "Invalid email prefix (careers, hr, etc.)"

    if not email_matches_domain(email, university_domain):
        return False, "Email domain doesn't match university domain"

    return True, "Valid"
