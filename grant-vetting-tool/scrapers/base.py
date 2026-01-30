"""
Base scraper interface for the Grant Applicant Vetting Tool.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScraperResult:
    """Represents the result of a scraping operation."""

    success: bool
    platform: str
    profile_data: Optional[dict] = None
    content_items: list = field(default_factory=list)
    error_message: Optional[str] = None
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    raw_data: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            'success': self.success,
            'platform': self.platform,
            'profile_data': self.profile_data,
            'content_items_count': len(self.content_items),
            'error_message': self.error_message,
            'scraped_at': self.scraped_at.isoformat()
        }


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""

    PLATFORM_NAME = "base"

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize the scraper.

        Args:
            config: Optional configuration dictionary with API keys and settings.
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.PLATFORM_NAME}")

    @abstractmethod
    def scrape_profile(self, identifier: str) -> ScraperResult:
        """
        Scrape a user's profile information.

        Args:
            identifier: The username, URL, or platform-specific ID.

        Returns:
            ScraperResult with profile_data populated.
        """
        pass

    @abstractmethod
    def scrape_content(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """
        Scrape a user's content (posts, tweets, etc.).

        Args:
            identifier: The username, URL, or platform-specific ID.
            limit: Maximum number of items to retrieve.
            since: Only retrieve content after this date.
            until: Only retrieve content before this date.

        Returns:
            ScraperResult with content_items populated.
        """
        pass

    def scrape_all(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """
        Scrape both profile and content.

        Args:
            identifier: The username, URL, or platform-specific ID.
            limit: Maximum number of content items to retrieve.
            since: Only retrieve content after this date.
            until: Only retrieve content before this date.

        Returns:
            Combined ScraperResult with both profile_data and content_items.
        """
        self.logger.info(f"Scraping all data for {identifier}")

        # First get profile
        profile_result = self.scrape_profile(identifier)
        if not profile_result.success:
            return profile_result

        # Then get content
        content_result = self.scrape_content(identifier, limit, since, until)

        # Combine results
        return ScraperResult(
            success=content_result.success,
            platform=self.PLATFORM_NAME,
            profile_data=profile_result.profile_data,
            content_items=content_result.content_items,
            error_message=content_result.error_message,
            raw_data={
                'profile': profile_result.raw_data,
                'content': content_result.raw_data
            }
        )

    @staticmethod
    def extract_username_from_url(url: str, platform: str) -> Optional[str]:
        """
        Extract username from a profile URL.

        Args:
            url: The profile URL.
            platform: The platform name.

        Returns:
            Extracted username or None if unable to parse.
        """
        import re
        from urllib.parse import urlparse

        parsed = urlparse(url)
        path = parsed.path.strip('/')

        if platform == 'twitter':
            # https://twitter.com/username or https://x.com/username
            match = re.match(r'^([^/]+)/?', path)
            if match:
                return match.group(1)

        elif platform == 'instagram':
            # https://instagram.com/username
            match = re.match(r'^([^/]+)/?', path)
            if match:
                return match.group(1)

        elif platform == 'linkedin':
            # https://linkedin.com/in/username
            match = re.match(r'^in/([^/]+)/?', path)
            if match:
                return match.group(1)

        elif platform == 'nostr':
            # Could be npub or nprofile in URL
            # Or a direct pubkey
            if 'npub' in url or 'nprofile' in url:
                match = re.search(r'(npub[a-z0-9]+|nprofile[a-z0-9]+)', url)
                if match:
                    return match.group(1)

        return path.split('/')[0] if path else None

    def validate_identifier(self, identifier: str) -> bool:
        """
        Validate that the identifier is in a valid format.

        Args:
            identifier: The identifier to validate.

        Returns:
            True if valid, False otherwise.
        """
        return bool(identifier and isinstance(identifier, str) and len(identifier) > 0)
