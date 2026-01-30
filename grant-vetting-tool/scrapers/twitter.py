"""
Twitter/X scraper for the Grant Applicant Vetting Tool.

This scraper uses Apify's Twitter scraper actors to fetch user profiles and tweets.
Apify provides a reliable way to scrape Twitter without direct API access.

Required: Apify API token in config or environment variable APIFY_API_TOKEN
"""

import os
import re
import time
from datetime import datetime
from typing import Optional
import logging

try:
    from apify_client import ApifyClient
except ImportError:
    ApifyClient = None

import requests

from .base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)


class TwitterScraper(BaseScraper):
    """Scraper for Twitter/X using Apify integration."""

    PLATFORM_NAME = "twitter"

    # Apify actor IDs for Twitter scraping
    # These are popular community actors - you may need to adjust based on availability
    PROFILE_ACTOR = "apidojo/twitter-user-scraper"
    TWEETS_ACTOR = "apidojo/tweet-scraper"

    # Alternative actors (in case primary ones are unavailable)
    ALT_PROFILE_ACTOR = "quacker/twitter-scraper"
    ALT_TWEETS_ACTOR = "quacker/twitter-scraper"

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
            # Handle twitter.com/username and x.com/username
            match = re.search(r'(?:twitter\.com|x\.com)/([^/?#]+)', identifier)
            if match:
                username = match.group(1)
                # Filter out Twitter special paths
                if username not in ['home', 'explore', 'notifications', 'messages', 'i', 'settings']:
                    return username

        return identifier

    def _run_actor(self, actor_id: str, run_input: dict, timeout_secs: int = 300) -> Optional[list]:
        """Run an Apify actor and wait for results."""
        if not self.client:
            self.logger.error("Apify client not initialized. Set APIFY_API_TOKEN.")
            return None

        try:
            self.logger.info(f"Running Apify actor: {actor_id}")

            # Start the actor run
            run = self.client.actor(actor_id).call(
                run_input=run_input,
                timeout_secs=timeout_secs
            )

            # Get results from the dataset
            items = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            self.logger.info(f"Retrieved {len(items)} items from actor")

            return items

        except Exception as e:
            self.logger.error(f"Error running Apify actor {actor_id}: {e}")
            return None

    def scrape_profile(self, identifier: str) -> ScraperResult:
        """Scrape a Twitter user's profile."""
        username = self._normalize_username(identifier)

        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured. Set APIFY_API_TOKEN environment variable."
            )

        self.logger.info(f"Fetching Twitter profile for: @{username}")

        # Try primary actor
        run_input = {
            "usernames": [username],
            "maxItems": 1,
            "includeUserInfo": True
        }

        items = self._run_actor(self.PROFILE_ACTOR, run_input)

        # If primary fails, try alternative
        if not items:
            self.logger.info("Primary actor failed, trying alternative...")
            run_input = {
                "handles": [username],
                "tweetsDesired": 0,
                "profilesDesired": 1
            }
            items = self._run_actor(self.ALT_PROFILE_ACTOR, run_input)

        if not items:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch profile for @{username}"
            )

        # Parse profile data (format may vary by actor)
        raw_profile = items[0]
        profile_data = self._parse_profile(raw_profile, username)

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            profile_data=profile_data,
            raw_data=raw_profile
        )

    def _parse_profile(self, raw: dict, username: str) -> dict:
        """Parse profile data from various actor output formats."""
        # Handle different actor output formats
        user_data = raw.get('user', raw)

        return {
            'username': user_data.get('screen_name') or user_data.get('username') or username,
            'display_name': user_data.get('name') or user_data.get('displayName'),
            'bio': user_data.get('description') or user_data.get('bio'),
            'location': user_data.get('location'),
            'website': user_data.get('url') or user_data.get('website'),
            'profile_image_url': user_data.get('profile_image_url_https') or user_data.get('profileImageUrl'),
            'banner_url': user_data.get('profile_banner_url') or user_data.get('bannerUrl'),
            'followers_count': user_data.get('followers_count') or user_data.get('followersCount'),
            'following_count': user_data.get('friends_count') or user_data.get('followingCount'),
            'posts_count': user_data.get('statuses_count') or user_data.get('tweetsCount'),
            'likes_count': user_data.get('favourites_count') or user_data.get('likesCount'),
            'verified': user_data.get('verified', False),
            'created_at': user_data.get('created_at') or user_data.get('createdAt'),
            'platform_id': str(user_data.get('id') or user_data.get('userId', ''))
        }

    def scrape_content(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """Scrape a Twitter user's tweets."""
        username = self._normalize_username(identifier)
        limit = limit or 100

        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured. Set APIFY_API_TOKEN environment variable."
            )

        self.logger.info(f"Fetching tweets for @{username}, limit: {limit}")

        # Build search query for user's tweets
        search_query = f"from:{username}"

        if since:
            search_query += f" since:{since.strftime('%Y-%m-%d')}"
        if until:
            search_query += f" until:{until.strftime('%Y-%m-%d')}"

        run_input = {
            "searchTerms": [search_query],
            "maxItems": limit,
            "sort": "Latest",
            "includeUserInfo": False
        }

        items = self._run_actor(self.TWEETS_ACTOR, run_input)

        # Try alternative actor if primary fails
        if not items:
            self.logger.info("Primary tweets actor failed, trying alternative...")
            run_input = {
                "handles": [username],
                "tweetsDesired": limit,
                "profilesDesired": 0
            }
            items = self._run_actor(self.ALT_TWEETS_ACTOR, run_input)

        if items is None:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Could not fetch tweets for @{username}"
            )

        # Parse tweets
        content_items = []
        for raw_tweet in items:
            parsed = self._parse_tweet(raw_tweet)
            if parsed:
                content_items.append(parsed)

        # Sort by date (newest first)
        content_items.sort(
            key=lambda x: x.get('published_at') or '',
            reverse=True
        )

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items[:limit],
            raw_data=items
        )

    def _parse_tweet(self, raw: dict) -> Optional[dict]:
        """Parse a tweet from various actor output formats."""
        try:
            # Handle different formats
            tweet_data = raw.get('tweet', raw)

            # Get text content
            text = (
                tweet_data.get('full_text') or
                tweet_data.get('text') or
                tweet_data.get('content') or
                ''
            )

            # Get timestamp
            created_at = tweet_data.get('created_at') or tweet_data.get('createdAt')
            published_at = None
            if created_at:
                try:
                    if isinstance(created_at, str):
                        # Try Twitter's format: "Wed Oct 10 20:19:24 +0000 2018"
                        try:
                            published_at = datetime.strptime(
                                created_at, "%a %b %d %H:%M:%S %z %Y"
                            )
                        except ValueError:
                            # Try ISO format
                            published_at = datetime.fromisoformat(
                                created_at.replace('Z', '+00:00')
                            )
                    elif isinstance(created_at, (int, float)):
                        published_at = datetime.fromtimestamp(created_at / 1000)
                except Exception:
                    pass

            # Get media URLs
            media_urls = []
            media = tweet_data.get('extended_entities', {}).get('media', [])
            if not media:
                media = tweet_data.get('media', [])
            for m in media:
                url = m.get('media_url_https') or m.get('url')
                if url:
                    media_urls.append(url)

            # Determine content type
            content_type = 'tweet'
            if tweet_data.get('in_reply_to_status_id') or tweet_data.get('isReply'):
                content_type = 'reply'
            if tweet_data.get('is_quote_status') or tweet_data.get('isQuote'):
                content_type = 'quote'
            if tweet_data.get('retweeted_status') or tweet_data.get('isRetweet'):
                content_type = 'retweet'

            # Build URL
            tweet_id = tweet_data.get('id_str') or tweet_data.get('id') or tweet_data.get('tweetId')
            author = (
                tweet_data.get('user', {}).get('screen_name') or
                tweet_data.get('author', {}).get('username') or
                tweet_data.get('username')
            )
            url = None
            if tweet_id and author:
                url = f"https://x.com/{author}/status/{tweet_id}"

            return {
                'platform': self.PLATFORM_NAME,
                'content_type': content_type,
                'platform_content_id': str(tweet_id) if tweet_id else None,
                'url': url,
                'text_content': text,
                'published_at': published_at.isoformat() if published_at else None,
                'likes_count': tweet_data.get('favorite_count') or tweet_data.get('likesCount'),
                'reposts_count': tweet_data.get('retweet_count') or tweet_data.get('retweetsCount'),
                'replies_count': tweet_data.get('reply_count') or tweet_data.get('repliesCount'),
                'media_urls': media_urls,
                'raw_content': raw
            }
        except Exception as e:
            self.logger.error(f"Error parsing tweet: {e}")
            return None

    def search_tweets(
        self,
        query: str,
        limit: int = 100,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """Search for tweets matching a query."""
        if not self.client:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message="Apify client not configured."
            )

        self.logger.info(f"Searching tweets: {query}, limit: {limit}")

        search_query = query
        if since:
            search_query += f" since:{since.strftime('%Y-%m-%d')}"
        if until:
            search_query += f" until:{until.strftime('%Y-%m-%d')}"

        run_input = {
            "searchTerms": [search_query],
            "maxItems": limit,
            "sort": "Latest"
        }

        items = self._run_actor(self.TWEETS_ACTOR, run_input)

        if items is None:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Search failed for: {query}"
            )

        content_items = []
        for raw_tweet in items:
            parsed = self._parse_tweet(raw_tweet)
            if parsed:
                content_items.append(parsed)

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items
        )
