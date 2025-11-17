"""
Fetch US universities from Hipolabs API.

Retrieves, validates, and stores university data including names, domains, and web pages.
"""

import json
from typing import List, Dict, Any

import requests

import config
from utils.logger import setup_logger
from utils.validators import is_valid_url, normalize_url

logger = setup_logger(__name__)


def fetch_universities() -> List[Dict[str, Any]]:
    """
    Fetch list of US universities from API.
    
    Returns:
        List of university dictionaries with validated data
    
    Raises:
        Exception: If API request fails
    """
    logger.info(f"Fetching universities from {config.UNIVERSITIES_API_URL}")

    try:
        response = requests.get(
            config.UNIVERSITIES_API_URL,
            timeout=30,
            headers={'User-Agent': config.USER_AGENTS[0]}
        )
        response.raise_for_status()

        universities_raw = response.json()
        logger.info(f"Fetched {len(universities_raw)} universities from API")

        # Validate and clean data
        universities_clean = []
        skipped = 0

        for uni in universities_raw:
            # Skip if missing required fields
            if not uni.get('name') or not uni.get('domains') or not uni.get('web_pages'):
                skipped += 1
                logger.debug(f"Skipping university with missing data: {uni.get('name', 'UNKNOWN')}")
                continue

            # Validate and normalize URLs
            web_pages = []
            for url in uni['web_pages']:
                if is_valid_url(url):
                    web_pages.append(normalize_url(url))

            if not web_pages:
                skipped += 1
                logger.debug(f"Skipping {uni['name']} - no valid web pages")
                continue

            # Create clean record
            clean_uni = {
                'name': uni['name'].strip(),
                'domains': [d.strip().lower() for d in uni['domains']],
                'web_pages': web_pages,
                'country': uni.get('country', 'United States'),
                'alpha_two_code': uni.get('alpha_two_code', 'US')
            }

            universities_clean.append(clean_uni)

        logger.info(f"Validated {len(universities_clean)} universities ({skipped} skipped)")

        # Save to file
        save_universities(universities_clean)

        return universities_clean

    except requests.RequestException as e:
        logger.error(f"Failed to fetch universities: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse API response: {e}")
        raise


def save_universities(universities: List[Dict[str, Any]]) -> None:
    """
    Save universities to JSON file.
    
    Args:
        universities: List of university dictionaries
    """
    try:
        with open(config.UNIVERSITIES_RAW_JSON, 'w', encoding='utf-8') as f:
            json.dump(universities, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(universities)} universities to {config.UNIVERSITIES_RAW_JSON}")
    except IOError as e:
        logger.error(f"Failed to save universities to file: {e}")
        raise


def load_universities() -> List[Dict[str, Any]]:
    """
    Load universities from JSON file.
    
    Returns:
        List of university dictionaries
    
    Raises:
        FileNotFoundError: If universities file doesn't exist
    """
    try:
        with open(config.UNIVERSITIES_RAW_JSON, 'r', encoding='utf-8') as f:
            universities = json.load(f)

        logger.info(f"Loaded {len(universities)} universities from {config.UNIVERSITIES_RAW_JSON}")
        return universities
    except FileNotFoundError:
        logger.error(f"Universities file not found: {config.UNIVERSITIES_RAW_JSON}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse universities file: {e}")
        raise
