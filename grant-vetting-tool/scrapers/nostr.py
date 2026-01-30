"""
Nostr scraper for the Grant Applicant Vetting Tool.

Nostr is a decentralized protocol, so we can access it directly through public relays
without API restrictions. This scraper connects to multiple relays to fetch user
profiles and notes (posts).
"""

import json
import time
import hashlib
from datetime import datetime
from typing import Optional
import logging

try:
    import websocket
except ImportError:
    websocket = None

from .base import BaseScraper, ScraperResult

logger = logging.getLogger(__name__)

# Default public Nostr relays
DEFAULT_RELAYS = [
    "wss://relay.damus.io",
    "wss://relay.nostr.band",
    "wss://nos.lol",
    "wss://relay.snort.social",
    "wss://relay.primal.net",
    "wss://nostr.wine",
    "wss://relay.nostr.info",
    "wss://nostr-pub.wellorder.net",
]


class NostrScraper(BaseScraper):
    """Scraper for Nostr decentralized social network."""

    PLATFORM_NAME = "nostr"

    # Nostr event kinds
    KIND_METADATA = 0  # Profile metadata
    KIND_TEXT_NOTE = 1  # Regular posts
    KIND_RECOMMEND_RELAY = 2
    KIND_CONTACTS = 3  # Following list
    KIND_REPOST = 6
    KIND_REACTION = 7
    KIND_LONG_FORM = 30023  # Long-form content

    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.relays = self.config.get('relays', DEFAULT_RELAYS)
        self.timeout = self.config.get('timeout', 10)
        self.max_events = self.config.get('max_events', 500)

    def _bech32_decode(self, bech32_str: str) -> Optional[bytes]:
        """Decode a bech32-encoded string (npub, nsec, etc.)."""
        try:
            # Simple bech32 decoding for npub
            CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"

            if not bech32_str.startswith(('npub1', 'nprofile1', 'note1', 'nevent1')):
                return None

            # Find the separator
            pos = bech32_str.rfind('1')
            if pos < 1:
                return None

            hrp = bech32_str[:pos]
            data_part = bech32_str[pos + 1:]

            # Decode data
            data = []
            for char in data_part:
                if char not in CHARSET:
                    return None
                data.append(CHARSET.index(char))

            # Convert from 5-bit to 8-bit
            acc = 0
            bits = 0
            result = []
            for value in data[:-6]:  # Exclude checksum
                acc = (acc << 5) | value
                bits += 5
                while bits >= 8:
                    bits -= 8
                    result.append((acc >> bits) & 0xff)

            if hrp == 'npub':
                return bytes(result)
            elif hrp == 'nprofile':
                # nprofile is TLV encoded, first 32 bytes are usually the pubkey
                return bytes(result[:32]) if len(result) >= 32 else None

            return bytes(result)
        except Exception as e:
            self.logger.error(f"Error decoding bech32: {e}")
            return None

    def _normalize_identifier(self, identifier: str) -> Optional[str]:
        """
        Convert any Nostr identifier to a hex pubkey.

        Accepts:
        - npub (bech32 encoded pubkey)
        - nprofile (bech32 encoded profile)
        - hex pubkey
        """
        identifier = identifier.strip()

        # Already a hex pubkey
        if len(identifier) == 64 and all(c in '0123456789abcdef' for c in identifier.lower()):
            return identifier.lower()

        # bech32 encoded
        if identifier.startswith(('npub1', 'nprofile1')):
            decoded = self._bech32_decode(identifier)
            if decoded:
                return decoded.hex()

        # Try to extract from URL
        if '/' in identifier or '.' in identifier:
            import re
            match = re.search(r'(npub1[a-z0-9]+|nprofile1[a-z0-9]+)', identifier)
            if match:
                decoded = self._bech32_decode(match.group(1))
                if decoded:
                    return decoded.hex()

        return None

    def _connect_and_query(self, relay_url: str, filters: list, timeout: int = 10) -> list:
        """Connect to a relay and execute a query."""
        if websocket is None:
            self.logger.error("websocket-client not installed")
            return []

        events = []
        try:
            ws = websocket.create_connection(relay_url, timeout=timeout)

            # Generate subscription ID
            sub_id = hashlib.sha256(f"{time.time()}".encode()).hexdigest()[:16]

            # Send REQ message
            req = json.dumps(["REQ", sub_id, *filters])
            ws.send(req)

            # Collect events until EOSE (End of Stored Events)
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    ws.settimeout(2)
                    msg = ws.recv()
                    data = json.loads(msg)

                    if data[0] == "EVENT" and data[1] == sub_id:
                        events.append(data[2])
                        if len(events) >= self.max_events:
                            break
                    elif data[0] == "EOSE":
                        break
                    elif data[0] == "NOTICE":
                        self.logger.warning(f"Relay notice: {data[1]}")
                except websocket.WebSocketTimeoutException:
                    continue
                except Exception as e:
                    self.logger.debug(f"Error receiving: {e}")
                    break

            # Close subscription
            ws.send(json.dumps(["CLOSE", sub_id]))
            ws.close()

        except Exception as e:
            self.logger.error(f"Error connecting to {relay_url}: {e}")

        return events

    def _query_relays(self, filters: list) -> list:
        """Query multiple relays and deduplicate results."""
        all_events = {}

        for relay in self.relays[:5]:  # Query up to 5 relays
            self.logger.info(f"Querying relay: {relay}")
            try:
                events = self._connect_and_query(relay, filters, self.timeout)
                for event in events:
                    event_id = event.get('id')
                    if event_id and event_id not in all_events:
                        all_events[event_id] = event
            except Exception as e:
                self.logger.error(f"Error querying {relay}: {e}")
                continue

            # If we have enough events, stop
            if len(all_events) >= self.max_events:
                break

        return list(all_events.values())

    def scrape_profile(self, identifier: str) -> ScraperResult:
        """Scrape a Nostr user's profile metadata."""
        pubkey = self._normalize_identifier(identifier)
        if not pubkey:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Invalid Nostr identifier: {identifier}"
            )

        self.logger.info(f"Fetching profile for pubkey: {pubkey}")

        # Query for metadata events
        filters = [{"kinds": [self.KIND_METADATA], "authors": [pubkey], "limit": 1}]
        events = self._query_relays(filters)

        if not events:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"No profile found for pubkey: {pubkey}"
            )

        # Get the most recent metadata event
        metadata_event = max(events, key=lambda e: e.get('created_at', 0))

        try:
            content = json.loads(metadata_event.get('content', '{}'))
        except json.JSONDecodeError:
            content = {}

        profile_data = {
            'pubkey': pubkey,
            'npub': identifier if identifier.startswith('npub') else None,
            'display_name': content.get('display_name') or content.get('displayName') or content.get('name'),
            'username': content.get('name') or content.get('username'),
            'bio': content.get('about'),
            'profile_image_url': content.get('picture'),
            'banner_url': content.get('banner'),
            'website': content.get('website'),
            'nip05': content.get('nip05'),  # Nostr verification
            'lud16': content.get('lud16'),  # Lightning address
            'metadata_updated_at': datetime.fromtimestamp(
                metadata_event.get('created_at', 0)
            ).isoformat() if metadata_event.get('created_at') else None
        }

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            profile_data=profile_data,
            raw_data=metadata_event
        )

    def scrape_content(
        self,
        identifier: str,
        limit: Optional[int] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> ScraperResult:
        """Scrape a Nostr user's notes (posts)."""
        pubkey = self._normalize_identifier(identifier)
        if not pubkey:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Invalid Nostr identifier: {identifier}"
            )

        limit = limit or self.max_events
        self.logger.info(f"Fetching notes for pubkey: {pubkey}, limit: {limit}")

        # Build filter
        filter_obj = {
            "kinds": [self.KIND_TEXT_NOTE, self.KIND_LONG_FORM],
            "authors": [pubkey],
            "limit": min(limit, 500)
        }

        if since:
            filter_obj["since"] = int(since.timestamp())
        if until:
            filter_obj["until"] = int(until.timestamp())

        events = self._query_relays([filter_obj])

        if not events:
            return ScraperResult(
                success=True,
                platform=self.PLATFORM_NAME,
                content_items=[],
                error_message="No notes found"
            )

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.get('created_at', 0), reverse=True)

        # Convert to content items
        content_items = []
        for event in events[:limit]:
            created_at = event.get('created_at')
            published_at = datetime.fromtimestamp(created_at) if created_at else None

            # Determine content type
            kind = event.get('kind', 1)
            if kind == self.KIND_LONG_FORM:
                content_type = 'article'
            else:
                content_type = 'note'

            # Extract any media URLs from tags
            media_urls = []
            for tag in event.get('tags', []):
                if tag[0] in ['image', 'video', 'url'] and len(tag) > 1:
                    media_urls.append(tag[1])

            # Also check for image URLs in content
            content = event.get('content', '')
            import re
            image_pattern = r'https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp)'
            found_images = re.findall(image_pattern, content, re.IGNORECASE)
            media_urls.extend(found_images)

            content_item = {
                'platform': self.PLATFORM_NAME,
                'content_type': content_type,
                'platform_content_id': event.get('id'),
                'text_content': content,
                'published_at': published_at.isoformat() if published_at else None,
                'media_urls': list(set(media_urls)),
                'raw_content': event,
                'tags': [tag[1] for tag in event.get('tags', []) if tag[0] == 't'],
                'mentions': [tag[1] for tag in event.get('tags', []) if tag[0] == 'p'],
                'reply_to': next(
                    (tag[1] for tag in event.get('tags', []) if tag[0] == 'e'),
                    None
                )
            }
            content_items.append(content_item)

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=content_items,
            raw_data=events
        )

    def scrape_following(self, identifier: str) -> ScraperResult:
        """Scrape a user's following list (contact list)."""
        pubkey = self._normalize_identifier(identifier)
        if not pubkey:
            return ScraperResult(
                success=False,
                platform=self.PLATFORM_NAME,
                error_message=f"Invalid Nostr identifier: {identifier}"
            )

        self.logger.info(f"Fetching following list for pubkey: {pubkey}")

        filters = [{"kinds": [self.KIND_CONTACTS], "authors": [pubkey], "limit": 1}]
        events = self._query_relays(filters)

        if not events:
            return ScraperResult(
                success=True,
                platform=self.PLATFORM_NAME,
                content_items=[],
                error_message="No contact list found"
            )

        # Get the most recent contact list
        contact_event = max(events, key=lambda e: e.get('created_at', 0))

        following = []
        for tag in contact_event.get('tags', []):
            if tag[0] == 'p' and len(tag) > 1:
                following.append({
                    'pubkey': tag[1],
                    'relay': tag[2] if len(tag) > 2 else None,
                    'petname': tag[3] if len(tag) > 3 else None
                })

        return ScraperResult(
            success=True,
            platform=self.PLATFORM_NAME,
            content_items=following,
            profile_data={'following_count': len(following)},
            raw_data=contact_event
        )
