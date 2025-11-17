"""
Fetch US universities from multiple API sources with fallback.

Retrieves, validates, and stores university data including names, domains, and web pages.
"""

import json
from typing import List, Dict, Any

import requests

import config
from utils.logger import setup_logger
from utils.validators import is_valid_url, normalize_url

logger = setup_logger(__name__)

# Multiple API sources (in order of preference)
API_SOURCES = [
    {
        'name': 'Hipolabs API',
        'url': 'https://universities.hipolabs.com/search?country=United%20States',
        'timeout': 30
    },
    {
        'name': 'GitHub Repository (all universities)',
        'url': 'https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json',
        'timeout': 60,
        'filter_country': 'United States'  # Need to filter for US only
    }
]


def fetch_from_source(source: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch universities from a single source.
    
    Args:
        source: Source configuration dictionary
    
    Returns:
        List of university dictionaries
    
    Raises:
        Exception: If fetch fails
    """
    logger.info(f"Trying source: {source['name']}")
    logger.info(f"URL: {source['url']}")

    response = requests.get(
        source['url'],
        timeout=source.get('timeout', 30),
        headers={'User-Agent': config.USER_AGENTS[0]}
    )
    response.raise_for_status()

    universities = response.json()

    # Filter by country if needed
    if source.get('filter_country'):
        country = source['filter_country']
        universities = [u for u in universities if u.get('country') == country]
        logger.info(f"Filtered to {len(universities)} universities in {country}")

    return universities


def fetch_universities() -> List[Dict[str, Any]]:
    """
    Fetch list of US universities from API with fallback sources.
    
    Returns:
        List of university dictionaries with validated data
    
    Raises:
        Exception: If all API sources fail
    """
    logger.info(f"Fetching US universities from multiple sources")

    universities_raw = None
    last_error = None

    # Try each source in order
    for source in API_SOURCES:
        try:
            universities_raw = fetch_from_source(source)
            logger.info(f"✓ Successfully fetched from {source['name']}")
            break  # Success, stop trying
        except requests.RequestException as e:
            last_error = e
            logger.warning(f"✗ Failed to fetch from {source['name']}: {e}")
            continue  # Try next source
        except json.JSONDecodeError as e:
            last_error = e
            logger.warning(f"✗ Failed to parse response from {source['name']}: {e}")
            continue  # Try next source
        except Exception as e:
            last_error = e
            logger.warning(f"✗ Unexpected error from {source['name']}: {e}")
            continue  # Try next source

    # If all sources failed
    if universities_raw is None:
        error_msg = f"Failed to fetch universities from all sources. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

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
            'alpha_two_code': uni.get('alpha_two_code', 'US'),
            'state_province': uni.get('state-province', uni.get('state_province'))
        }

        universities_clean.append(clean_uni)

    logger.info(f"Validated {len(universities_clean)} universities ({skipped} skipped)")

    # Save to file
    save_universities(universities_clean)

    return universities_clean


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
