"""
Instagram scraper for the Grant Applicant Vetting Tool.

This scraper uses Apify's Instagram scraper actors to fetch user profiles and posts.
Instagram has strong anti-scraping measures, so Apify provides a more reliable solution.

Required: Apify API token in config or environment variable APIFY_API_TOKEN
"""

import os
import re
from datetime import datetime
from typing import Optional
import logging

try:
    from apify_client import ApifyClient
except ImportError:
    ApifyClient = None

from .base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)


class InstagramScraper(BaseScraper):
    """Scraper for Instagram using Apify integration."""

    PLATFORM_NAME = "instagram"

    # Apify actor IDs for Instagram scraping
    PROFILE_ACTOR = "apify/instagram-profile-scraper"
    POSTS_ACTOR = "apify/instagram-post-scraper"
    SCRAPER_ACTOR = "apify/instagram-scraper"  # Combined actor

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.api_token = self.config.get('apify_api_token') or os.getenv('APIFY_API_TOKEN')
        self.client = None

        if self.api_token and ApifyClient:
            self.client = ApifyClient(self.api_token)
        elif not ApifyClient:
            self.logger.warning("apify-client not installed. Install with: pip install apify-client")

    def _normalize_username(self, identifier: str) -> str:
        """Extract username from various input formats."""
        identifier = identifier.strip()

        # Remove @ prefix
        if identifier.startswith('@'):
            return identifier[1:]

        # Extract from URL
        if '/' in identifier:
            match = re.search(r'instagram\.com/([^/?#]+)', identifier)
            if match:
                username = match.group(1)
                # Filter out Instagram special paths
                if username not in ['p', 'reel', 'stories', 'explore', 'direct', 'accounts']:
                    return username

        return identifier

    def _run_actor(self, actor_id: str, run_input: dict, timeout_secs: int = 300) -> Optional[list]:
        """Run an Apify actor and wait for results."""
        if not self.client:
            self.logger.error("Apify client not initialized. Set APIFY_API_TOKEN.")
            return None

        try:
            self.logger.info(f"Running Apify actor: {actor_id}")

            run = self.client.actor(actor_id).call(
                run_input=run_input,
                timeout_secs=timeout_secs
            )

            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            self.logger.info(f"Retrieved {len(items)} items from actor")

            return items

        except Exception as e:
            self.logger.error(f"Error running Apify actor {actor_id}: {e}")
            return None

    def scrape_profile(self, identifier: str) -> ScraperResult:
        """Scrape an Instagram user's profile."""
        username = self._normalize_username(identifier)

        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured. Set APIFY_API_TOKEN environment variable."
            )

        self.logger.info(f"Fetching Instagram profile for: @{username}")

        run_input = {
            "usernames": [username],
            "resultsLimit": 1
        }

        items = self._run_actor(self.PROFILE_ACTOR, run_input)

        # Try combined scraper if profile scraper fails
        if not items:
            self.logger.info("Profile actor failed, trying combined scraper...")
            run_input = {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": "details",
                "resultsLimit": 1
            }
            items = self._run_actor(self.SCRAPER_ACTOR, run_input)

        if not items:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch profile for @{username}"
            )

        raw_profile = items[0]
        profile_data = self._parse_profile(raw_profile, username)

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            profile_data=profile_data,
            raw_data=raw_profile
        )

    def _parse_profile(self, raw: dict, username: str) -> dict:
        """Parse profile data from Apify output."""
        return {
            'username': raw.get('username') or username,
            'display_name': raw.get('fullName') or raw.get('full_name'),
            'bio': raw.get('biography') or raw.get('bio'),
            'website': raw.get('externalUrl') or raw.get('external_url'),
            'profile_image_url': raw.get('profilePicUrl') or raw.get('profile_pic_url'),
            'followers_count': raw.get('followersCount') or raw.get('followers'),
            'following_count': raw.get('followsCount') or raw.get('following'),
            'posts_count': raw.get('postsCount') or raw.get('media_count'),
            'verified': raw.get('verified', False),
            'is_private': raw.get('private') or raw.get('is_private', False),
            'is_business': raw.get('isBusinessAccount') or raw.get('is_business_account', False),
            'category': raw.get('businessCategoryName') or raw.get('category'),
            'platform_id': str(raw.get('id') or raw.get('pk', ''))
        }

    def scrape_content(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """Scrape an Instagram user's posts."""
        username = self._normalize_username(identifier)
        limit = limit or 50

        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured. Set APIFY_API_TOKEN environment variable."
            )

        self.logger.info(f"Fetching Instagram posts for @{username}, limit: {limit}")

        run_input = {
            "directUrls": [f"https://www.instagram.com/{username}/"],
            "resultsType": "posts",
            "resultsLimit": limit
        }

        items = self._run_actor(self.SCRAPER_ACTOR, run_input)

        if items is None:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch posts for @{username}"
            )

        content_items = []
        for raw_post in items:
            parsed = self._parse_post(raw_post)
            if parsed:
                # Apply date filters
                pub_date_str = parsed.get('published_at')
                if pub_date_str:
                    try:
                        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
                        if since and pub_date < since:
                            continue
                        if until and pub_date > until:
                            continue
                    except ValueError:
                        pass
                content_items.append(parsed)

        # Sort by date (newest first)
        content_items.sort(
            key=lambda x: x.get('published_at') or '',
            reverse=True
        )

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items[:limit]
        )

    def _parse_post(self, raw: dict) -> Optional[dict]:
        """Parse a post from Apify output."""
        try:
            # Get text content (caption)
            caption = raw.get('caption') or ''
            if isinstance(caption, dict):
                caption = caption.get('text', '')

            # Get timestamp
            timestamp = raw.get('timestamp') or raw.get('taken_at')
            published_at = None
            if timestamp:
                try:
                    if isinstance(timestamp, str):
                        published_at = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    elif isinstance(timestamp, (int, float)):
                        published_at = datetime.fromtimestamp(timestamp)
                except Exception:
                    pass

            # Get media URLs
            media_urls = []
            if raw.get('displayUrl'):
                media_urls.append(raw['displayUrl'])
            if raw.get('images'):
                media_urls.extend(raw['images'])
            if raw.get('videoUrl'):
                media_urls.append(raw['videoUrl'])

            # Determine content type
            content_type = 'post'
            if raw.get('type') == 'Video' or raw.get('is_video'):
                content_type = 'video'
            elif raw.get('type') == 'Sidecar' or raw.get('mediaCount', 1) > 1:
                content_type = 'carousel'

            # Get URL
            shortcode = raw.get('shortCode') or raw.get('code')
            url = f"https://www.instagram.com/p/{shortcode}/" if shortcode else raw.get('url')

            return {
                'platform': self.PLATFORM_NAME,
                'content_type': content_type,
                'platform_content_id': raw.get('id') or shortcode,
                'url': url,
                'text_content': caption,
                'published_at': published_at.isoformat() if published_at else None,
                'likes_count': raw.get('likesCount') or raw.get('likes'),
                'comments_count': raw.get('commentsCount') or raw.get('comments'),
                'media_urls': media_urls,
                'location': raw.get('locationName'),
                'hashtags': raw.get('hashtags', []),
                'mentions': raw.get('mentions', []),
                'raw_content': raw
            }
        except Exception as e:
            self.logger.error(f"Error parsing Instagram post: {e}")
            return None

    def scrape_hashtag(self, hashtag: str, limit: int = 50) -> ScraperResult:
        """Scrape posts from a hashtag."""
        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured."
            )

        # Remove # if present
        hashtag = hashtag.lstrip('#')

        self.logger.info(f"Fetching Instagram posts for #{hashtag}, limit: {limit}")

        run_input = {
            "directUrls": [f"https://www.instagram.com/explore/tags/{hashtag}/"],
            "resultsType": "posts",
            "resultsLimit": limit
        }

        items = self._run_actor(self.SCRAPER_ACTOR, run_input)

        if items is None:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch posts for #{hashtag}"
            )

        content_items = []
        for raw_post in items:
            parsed = self._parse_post(raw_post)
            if parsed:
                content_items.append(parsed)

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items
        )
