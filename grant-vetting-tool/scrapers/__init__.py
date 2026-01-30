"""
Scrapers module for the Grant Applicant Vetting Tool.

This module provides scrapers for various social media platforms:
- Nostr: Direct relay access (fully automatic)
- Twitter/X: Via Apify integration
- Instagram: Via Apify integration
- Web/Blogs: Built-in web scraper
- LinkedIn: Via Apify integration (use with caution)
"""

from .base import BaseScraper, ScraperResult
from .nostr import NostrScraper
from .twitter import TwitterScraper
from .web import WebScraper
from .instagram import InstagramScraper

__all__ = [
    'BaseScraper',
    'ScraperResult',
    'NostrScraper',
    'TwitterScraper',
    'WebScraper',
    'InstagramScraper',
]
