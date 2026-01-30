"""
Profile Discovery Engine for the Grant Applicant Vetting Tool.

This module attempts to discover additional social media profiles and online
presence based on provided information (name, known profiles, etc.).

Discovery methods:
1. Username correlation - Try the same username on different platforms
2. Profile bio links - Extract links from known profile bios
3. Search engine queries - Search for name + platform
4. Cross-platform linking - Look for linked accounts in profile data
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    requests = None
    BeautifulSoup = None

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredProfile:
    """Represents a discovered social media profile."""
    platform: str
    username: Optional[str]
    url: str
    confidence: str  # 'high', 'medium', 'low'
    discovery_method: str
    source: Optional[str] = None  # Where it was discovered from


class ProfileDiscoveryEngine:
    """
    Engine for discovering additional social media profiles for an applicant.
    """

    # Platform URL patterns for building profile URLs
    PLATFORM_URL_PATTERNS = {
        'twitter': 'https://x.com/{username}',
        'instagram': 'https://www.instagram.com/{username}/',
        'linkedin': 'https://www.linkedin.com/in/{username}/',
        'facebook': 'https://www.facebook.com/{username}',
        'github': 'https://github.com/{username}',
        'youtube': 'https://www.youtube.com/@{username}',
        'tiktok': 'https://www.tiktok.com/@{username}',
        'mastodon': None,  # Requires instance
        'nostr': None,  # Uses pubkeys
    }

    # Patterns to extract social links from text/bios
    SOCIAL_LINK_PATTERNS = {
        'twitter': [
            r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)',
            r'@([a-zA-Z0-9_]+)\s*(?:on\s+)?(?:twitter|X)',
        ],
        'instagram': [
            r'instagram\.com/([a-zA-Z0-9_.]+)',
            r'@([a-zA-Z0-9_.]+)\s*(?:on\s+)?instagram',
        ],
        'linkedin': [
            r'linkedin\.com/in/([a-zA-Z0-9_-]+)',
        ],
        'github': [
            r'github\.com/([a-zA-Z0-9_-]+)',
        ],
        'nostr': [
            r'(npub1[a-z0-9]{58})',
            r'(nprofile1[a-z0-9]+)',
        ],
        'youtube': [
            r'youtube\.com/(?:@|channel/|user/)([a-zA-Z0-9_-]+)',
        ],
        'facebook': [
            r'facebook\.com/([a-zA-Z0-9.]+)',
        ],
        'substack': [
            r'([a-zA-Z0-9_-]+)\.substack\.com',
        ],
        'medium': [
            r'medium\.com/@([a-zA-Z0-9_-]+)',
            r'([a-zA-Z0-9_-]+)\.medium\.com',
        ],
    }

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({'User-Agent': self.USER_AGENT})

    def discover_profiles(
        self,
        name: str,
        known_profiles: List[Dict],
        email: Optional[str] = None
    ) -> List[DiscoveredProfile]:
        """
        Discover additional social media profiles for an applicant.

        Args:
            name: The applicant's name
            known_profiles: List of already known profiles with 'platform', 'username', 'url'
            email: Optional email address

        Returns:
            List of DiscoveredProfile objects
        """
        discovered = []
        seen = set()

        # Track known profiles to avoid duplicates
        for profile in known_profiles:
            key = f"{profile.get('platform')}:{profile.get('username', '').lower()}"
            seen.add(key)

        # Method 1: Username correlation
        usernames = self._extract_usernames(known_profiles)
        for username in usernames:
            profiles = self._try_username_on_platforms(username, known_profiles)
            for profile in profiles:
                key = f"{profile.platform}:{profile.username.lower() if profile.username else ''}"
                if key not in seen:
                    seen.add(key)
                    discovered.append(profile)

        # Method 2: Extract links from known profile bios
        for profile in known_profiles:
            bio_links = self._discover_from_bio(profile)
            for link_profile in bio_links:
                key = f"{link_profile.platform}:{link_profile.username.lower() if link_profile.username else ''}"
                if key not in seen:
                    seen.add(key)
                    discovered.append(link_profile)

        # Method 3: Check profile pages for linked accounts
        for profile in known_profiles:
            linked = self._discover_linked_accounts(profile)
            for link_profile in linked:
                key = f"{link_profile.platform}:{link_profile.username.lower() if link_profile.username else ''}"
                if key not in seen:
                    seen.add(key)
                    discovered.append(link_profile)

        # Method 4: Email-based discovery (if email provided)
        if email:
            email_profiles = self._discover_from_email(email)
            for profile in email_profiles:
                key = f"{profile.platform}:{profile.username.lower() if profile.username else ''}"
                if key not in seen:
                    seen.add(key)
                    discovered.append(profile)

        return discovered

    def _extract_usernames(self, profiles: List[Dict]) -> List[str]:
        """Extract unique usernames from known profiles."""
        usernames = set()
        for profile in profiles:
            username = profile.get('username')
            if username:
                # Normalize username
                username = username.strip().lstrip('@')
                if username and len(username) > 2:
                    usernames.add(username)
        return list(usernames)

    def _try_username_on_platforms(
        self,
        username: str,
        known_profiles: List[Dict]
    ) -> List[DiscoveredProfile]:
        """Try a username on platforms where we don't have a profile yet."""
        discovered = []
        known_platforms = {p.get('platform') for p in known_profiles}

        for platform, url_pattern in self.PLATFORM_URL_PATTERNS.items():
            if platform in known_platforms or not url_pattern:
                continue

            url = url_pattern.format(username=username)

            # Check if the profile exists
            if self._check_profile_exists(url, platform):
                discovered.append(DiscoveredProfile(
                    platform=platform,
                    username=username,
                    url=url,
                    confidence='medium',
                    discovery_method='username_correlation',
                    source=f"Correlated from known username: {username}"
                ))

        return discovered

    def _check_profile_exists(self, url: str, platform: str) -> bool:
        """Check if a profile URL returns a valid profile page."""
        if not self.session:
            return False

        try:
            response = self.session.head(url, timeout=10, allow_redirects=True)

            # Most platforms return 200 for existing profiles
            if response.status_code == 200:
                return True

            # Some platforms redirect non-existent profiles
            if response.status_code in [301, 302]:
                # Check if redirect is to a "not found" or "login" page
                redirect_url = response.headers.get('Location', '')
                if 'login' in redirect_url or 'error' in redirect_url:
                    return False
                return True

            return False

        except Exception as e:
            self.logger.debug(f"Error checking {url}: {e}")
            return False

    def _discover_from_bio(self, profile: Dict) -> List[DiscoveredProfile]:
        """Extract social links from a profile's bio text."""
        discovered = []

        bio = profile.get('bio') or ''
        website = profile.get('website') or ''
        text_to_search = f"{bio} {website}"

        for platform, patterns in self.SOCIAL_LINK_PATTERNS.items():
            if platform == profile.get('platform'):
                continue  # Skip the same platform

            for pattern in patterns:
                matches = re.findall(pattern, text_to_search, re.IGNORECASE)
                for match in matches:
                    username = match
                    url_pattern = self.PLATFORM_URL_PATTERNS.get(platform)

                    if platform == 'nostr':
                        url = None  # Nostr doesn't have a single URL
                    elif url_pattern:
                        url = url_pattern.format(username=username)
                    else:
                        url = None

                    discovered.append(DiscoveredProfile(
                        platform=platform,
                        username=username,
                        url=url or f"https://{platform}.com/{username}",
                        confidence='high',
                        discovery_method='bio_extraction',
                        source=f"Found in {profile.get('platform')} bio"
                    ))

        return discovered

    def _discover_linked_accounts(self, profile: Dict) -> List[DiscoveredProfile]:
        """Fetch a profile page and look for linked accounts."""
        discovered = []
        url = profile.get('url')

        if not url or not self.session or not BeautifulSoup:
            return discovered

        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return discovered

            soup = BeautifulSoup(response.text, 'lxml')

            # Look for social links in the page
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')

                for platform, patterns in self.SOCIAL_LINK_PATTERNS.items():
                    if platform == profile.get('platform'):
                        continue

                    for pattern in patterns:
                        match = re.search(pattern, href, re.IGNORECASE)
                        if match:
                            username = match.group(1)
                            discovered.append(DiscoveredProfile(
                                platform=platform,
                                username=username,
                                url=href if href.startswith('http') else None,
                                confidence='high',
                                discovery_method='linked_account',
                                source=f"Linked from {profile.get('platform')} profile page"
                            ))
                            break

        except Exception as e:
            self.logger.debug(f"Error fetching {url}: {e}")

        return discovered

    def _discover_from_email(self, email: str) -> List[DiscoveredProfile]:
        """
        Attempt to find profiles based on email.
        This is limited without API access, but can check Gravatar.
        """
        discovered = []

        # Extract potential username from email
        username_part = email.split('@')[0]

        # Clean up common patterns
        username = re.sub(r'[._+-]\d+$', '', username_part)  # Remove trailing numbers
        username = re.sub(r'[._+-]', '', username)  # Remove separators

        if len(username) >= 3:
            # Try this username on platforms
            for platform, url_pattern in self.PLATFORM_URL_PATTERNS.items():
                if not url_pattern:
                    continue

                url = url_pattern.format(username=username)
                if self._check_profile_exists(url, platform):
                    discovered.append(DiscoveredProfile(
                        platform=platform,
                        username=username,
                        url=url,
                        confidence='low',
                        discovery_method='email_correlation',
                        source=f"Derived from email prefix"
                    ))

        return discovered

    def extract_social_links_from_text(self, text: str) -> List[DiscoveredProfile]:
        """
        Extract any social media links from arbitrary text.

        Useful for scanning content for self-mentions or profile links.
        """
        discovered = []

        for platform, patterns in self.SOCIAL_LINK_PATTERNS.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    username = match
                    url_pattern = self.PLATFORM_URL_PATTERNS.get(platform)

                    if url_pattern:
                        url = url_pattern.format(username=username)
                    else:
                        url = None

                    discovered.append(DiscoveredProfile(
                        platform=platform,
                        username=username,
                        url=url,
                        confidence='medium',
                        discovery_method='text_extraction',
                        source='Extracted from content'
                    ))

        return discovered

    def discover_nostr_from_nip05(self, nip05: str) -> Optional[DiscoveredProfile]:
        """
        Discover Nostr pubkey from NIP-05 identifier.

        NIP-05 format: username@domain.com
        """
        if not nip05 or '@' not in nip05:
            return None

        try:
            username, domain = nip05.split('@', 1)
            url = f"https://{domain}/.well-known/nostr.json?name={username}"

            if not self.session:
                return None

            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                pubkey = data.get('names', {}).get(username)
                if pubkey:
                    return DiscoveredProfile(
                        platform='nostr',
                        username=nip05,
                        url=None,
                        confidence='high',
                        discovery_method='nip05_verification',
                        source=f"Verified NIP-05: {nip05}"
                    )
        except Exception as e:
            self.logger.debug(f"Error verifying NIP-05 {nip05}: {e}")

        return None
