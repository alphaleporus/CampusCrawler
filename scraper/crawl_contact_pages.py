"""
Asynchronous crawling of university contact pages.

Attempts multiple common contact page paths with proper rate limiting and error handling.
"""

import asyncio
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup

import config
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ContactPageCrawler:
    """Asynchronous crawler for university contact pages."""

    def __init__(self):
        """Initialize crawler with settings from config."""
        self.timeout = aiohttp.ClientTimeout(total=config.REQUEST_TIMEOUT)
        self.max_retries = config.MAX_RETRIES
        self.rate_limit_delay = config.RATE_LIMIT_DELAY
        self.user_agents = config.USER_AGENTS

    def _get_random_user_agent(self) -> str:
        """
        Get a random user agent string.
        
        Returns:
            User agent string
        """
        return random.choice(self.user_agents)

    async def fetch_page(
            self,
            session: aiohttp.ClientSession,
            url: str,
            retry_count: int = 0
    ) -> Optional[str]:
        """
        Fetch a single page with retry logic.
        
        Args:
            session: aiohttp session
            url: URL to fetch
            retry_count: Current retry attempt
        
        Returns:
            Page HTML content or None if failed
        """
        try:
            headers = {'User-Agent': self._get_random_user_agent()}

            async with session.get(url, headers=headers, timeout=self.timeout) as response:
                if response.status < 400:
                    content = await response.text()
                    logger.debug(f"Successfully fetched {url} (status: {response.status})")
                    return content
                else:
                    logger.debug(f"Failed to fetch {url} (status: {response.status})")
                    return None

        except asyncio.TimeoutError:
            logger.debug(f"Timeout fetching {url}")
            if retry_count < self.max_retries:
                logger.debug(f"Retrying {url} (attempt {retry_count + 1})")
                await asyncio.sleep(1)
                return await self.fetch_page(session, url, retry_count + 1)
            return None

        except aiohttp.ClientError as e:
            logger.debug(f"Client error fetching {url}: {e}")
            if retry_count < self.max_retries:
                logger.debug(f"Retrying {url} (attempt {retry_count + 1})")
                await asyncio.sleep(1)
                return await self.fetch_page(session, url, retry_count + 1)
            return None

        except Exception as e:
            logger.debug(f"Unexpected error fetching {url}: {e}")
            return None

    async def crawl_university(
            self,
            session: aiohttp.ClientSession,
            university: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crawl all potential contact pages for a university.
        
        Args:
            session: aiohttp session
            university: University data dictionary
        
        Returns:
            Dictionary with university info and crawled pages
        """
        name = university['name']
        base_url = university['web_pages'][0]

        logger.debug(f"Crawling {name} at {base_url}")

        pages_found = []

        for path in config.CONTACT_PAGE_PATHS:
            url = urljoin(base_url, path)

            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)

            content = await self.fetch_page(session, url)

            if content:
                pages_found.append({
                    'url': url,
                    'path': path,
                    'content': content
                })

        result = {
            'name': name,
            'base_url': base_url,
            'domains': university['domains'],
            'pages': pages_found,
            'pages_found_count': len(pages_found)
        }

        if pages_found:
            logger.info(f"✓ {name}: Found {len(pages_found)} contact pages")
        else:
            logger.warning(f"✗ {name}: No contact pages found")

        return result

    async def crawl_universities(
            self,
            universities: List[Dict[str, Any]],
            limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple universities asynchronously.
        
        Args:
            universities: List of university dictionaries
            limit: Optional limit on number of universities to crawl
        
        Returns:
            List of crawl results
        """
        if limit:
            universities = universities[:limit]

        logger.info(f"Starting crawl of {len(universities)} universities")

        async with aiohttp.ClientSession() as session:
            tasks = [
                self.crawl_university(session, uni)
                for uni in universities
            ]

            results = await asyncio.gather(*tasks)

        # Statistics
        total_pages = sum(r['pages_found_count'] for r in results)
        universities_with_pages = sum(1 for r in results if r['pages_found_count'] > 0)

        logger.info(
            f"Crawl complete: {total_pages} pages from {universities_with_pages}/{len(universities)} universities")

        return results


def crawl_all_universities(
        universities: List[Dict[str, Any]],
        limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Synchronous wrapper for async crawling.
    
    Args:
        universities: List of university dictionaries
        limit: Optional limit on number to crawl
    
    Returns:
        List of crawl results
    """
    crawler = ContactPageCrawler()
    return asyncio.run(crawler.crawl_universities(universities, limit))
