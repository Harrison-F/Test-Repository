"""
OFAC Sanctions Lookup for the Grant Applicant Vetting Tool.

This module provides integration with the U.S. Treasury's OFAC
(Office of Foreign Assets Control) sanctions list.

API Documentation: https://sanctionssearch.ofac.treas.gov/
"""

import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
import logging

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


@dataclass
class SanctionsMatch:
    """Represents a potential match in the OFAC sanctions list."""
    name: str
    match_score: float  # 0-100, higher = better match
    sdn_type: str  # 'Individual', 'Entity', etc.
    programs: List[str]  # Sanctions programs
    addresses: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    ids: List[Dict] = field(default_factory=list)
    remarks: Optional[str] = None
    source_list: str = 'SDN'  # SDN, Consolidated, etc.

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'match_score': self.match_score,
            'sdn_type': self.sdn_type,
            'programs': self.programs,
            'addresses': self.addresses,
            'aliases': self.aliases,
            'ids': self.ids,
            'remarks': self.remarks,
            'source_list': self.source_list,
        }


@dataclass
class SanctionsCheckResult:
    """Result of a sanctions check."""
    search_name: str
    search_country: Optional[str]
    has_matches: bool
    matches: List[SanctionsMatch] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'search_name': self.search_name,
            'search_country': self.search_country,
            'has_matches': self.has_matches,
            'matches_count': len(self.matches),
            'matches': [m.to_dict() for m in self.matches],
            'checked_at': self.checked_at.isoformat(),
            'error': self.error,
        }


class OFACSanctionsChecker:
    """
    Checker for OFAC sanctions lists.

    Uses the OFAC Sanctions Search API to check if an individual or entity
    is on any U.S. sanctions lists.
    """

    # OFAC API endpoint
    # Note: The official OFAC website uses a different backend
    # We'll use a fuzzy name matching approach with the downloadable SDN list
    # or the web search interface

    OFAC_SEARCH_URL = "https://sanctionssearch.ofac.treas.gov/api/search"

    # Alternative: Use the SDN CSV download
    SDN_LIST_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    SDN_ALT_URL = "https://www.treasury.gov/ofac/downloads/sdnlist.txt"

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the sanctions checker.

        Args:
            config: Optional config with:
                - min_score: Minimum match score to consider (default: 80)
                - include_fuzzy: Include fuzzy matches (default: True)
                - cache_ttl: Cache duration in seconds (default: 3600)
        """
        self.config = config or {}
        self.min_score = self.config.get('min_score', 80)
        self.include_fuzzy = self.config.get('include_fuzzy', True)
        self.logger = logging.getLogger(__name__)

        self.session = None
        if requests:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            })

    def check_individual(
        self,
        name: str,
        country: Optional[str] = None,
        date_of_birth: Optional[str] = None
    ) -> SanctionsCheckResult:
        """
        Check if an individual is on the OFAC sanctions list.

        Args:
            name: Full name of the individual
            country: Optional country for filtering
            date_of_birth: Optional DOB in YYYY-MM-DD format

        Returns:
            SanctionsCheckResult with any matches found
        """
        if not self.session:
            return SanctionsCheckResult(
                search_name=name,
                search_country=country,
                has_matches=False,
                error="requests library not available"
            )

        self.logger.info(f"Checking OFAC sanctions for: {name}")

        try:
            # Try the web search API first
            matches = self._search_ofac_web(name, country)

            if matches is None:
                # Fallback to local SDN list search
                matches = self._search_local_sdn(name, country)

            # Filter by minimum score
            filtered_matches = [
                m for m in matches
                if m.match_score >= self.min_score
            ]

            return SanctionsCheckResult(
                search_name=name,
                search_country=country,
                has_matches=len(filtered_matches) > 0,
                matches=filtered_matches
            )

        except Exception as e:
            self.logger.error(f"Error checking sanctions: {e}")
            return SanctionsCheckResult(
                search_name=name,
                search_country=country,
                has_matches=False,
                error=str(e)
            )

    def _search_ofac_web(
        self,
        name: str,
        country: Optional[str] = None
    ) -> Optional[List[SanctionsMatch]]:
        """
        Search using the OFAC web interface.

        Returns None if the API is unavailable.
        """
        try:
            # The OFAC website uses a specific API format
            params = {
                'name': name,
                'type': 'individual',
                'minScore': self.min_score if self.include_fuzzy else 100,
            }

            if country:
                params['country'] = country

            response = self.session.get(
                self.OFAC_SEARCH_URL,
                params=params,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return self._parse_ofac_response(data)

            # API not available or returned error
            self.logger.warning(f"OFAC API returned status {response.status_code}")
            return None

        except Exception as e:
            self.logger.warning(f"OFAC web search failed: {e}")
            return None

    def _parse_ofac_response(self, data: Dict) -> List[SanctionsMatch]:
        """Parse OFAC API response into SanctionsMatch objects."""
        matches = []

        results = data.get('results', data.get('matches', []))

        for result in results:
            match = SanctionsMatch(
                name=result.get('name', result.get('fullName', '')),
                match_score=float(result.get('score', result.get('matchScore', 100))),
                sdn_type=result.get('sdnType', result.get('type', 'Individual')),
                programs=result.get('programs', result.get('sanctionsPrograms', [])),
                addresses=result.get('addresses', []),
                aliases=result.get('aliases', result.get('akaList', [])),
                ids=result.get('ids', result.get('identifications', [])),
                remarks=result.get('remarks'),
                source_list=result.get('source', 'SDN')
            )
            matches.append(match)

        return matches

    def _search_local_sdn(
        self,
        name: str,
        country: Optional[str] = None
    ) -> List[SanctionsMatch]:
        """
        Fallback: Search using fuzzy matching against downloaded SDN list.

        This is a simplified version - for production, you'd want to
        download and index the SDN list properly.
        """
        matches = []

        # Normalize the search name
        search_terms = self._normalize_name(name)

        try:
            # Try to fetch the SDN list (in production, this should be cached)
            response = self.session.get(self.SDN_ALT_URL, timeout=60)

            if response.status_code != 200:
                self.logger.warning("Could not fetch SDN list")
                return matches

            sdn_text = response.text

            # Simple line-by-line search
            for line in sdn_text.split('\n'):
                if not line.strip():
                    continue

                # Check if any search term appears in this line
                line_lower = line.lower()
                term_matches = sum(1 for term in search_terms if term in line_lower)

                if term_matches >= len(search_terms) * 0.5:  # At least half the terms match
                    # Parse the line (SDN format is pipe-delimited)
                    parts = line.split('|') if '|' in line else [line]

                    # Calculate a rough match score
                    score = (term_matches / len(search_terms)) * 100

                    match = SanctionsMatch(
                        name=parts[0].strip() if parts else line[:100],
                        match_score=score,
                        sdn_type='Individual',
                        programs=['SDN'],
                        source_list='SDN-Local'
                    )

                    # Apply country filter if specified
                    if country:
                        if country.lower() not in line_lower:
                            continue

                    matches.append(match)

                    # Limit results
                    if len(matches) >= 10:
                        break

        except Exception as e:
            self.logger.error(f"Local SDN search failed: {e}")

        return matches

    def _normalize_name(self, name: str) -> List[str]:
        """Normalize a name into searchable terms."""
        # Remove special characters
        name = re.sub(r'[^\w\s]', ' ', name)

        # Split into terms
        terms = name.lower().split()

        # Remove common titles and suffixes
        stopwords = {'mr', 'mrs', 'ms', 'dr', 'jr', 'sr', 'ii', 'iii', 'iv'}
        terms = [t for t in terms if t not in stopwords and len(t) > 1]

        return terms

    def check_entity(
        self,
        entity_name: str,
        country: Optional[str] = None
    ) -> SanctionsCheckResult:
        """
        Check if an entity/company is on the OFAC sanctions list.

        Args:
            entity_name: Name of the entity
            country: Optional country for filtering

        Returns:
            SanctionsCheckResult with any matches found
        """
        if not self.session:
            return SanctionsCheckResult(
                search_name=entity_name,
                search_country=country,
                has_matches=False,
                error="requests library not available"
            )

        self.logger.info(f"Checking OFAC sanctions for entity: {entity_name}")

        try:
            # Similar to individual check but for entities
            matches = self._search_ofac_web(entity_name, country)

            if matches is None:
                matches = self._search_local_sdn(entity_name, country)

            # Filter by minimum score
            filtered_matches = [
                m for m in matches
                if m.match_score >= self.min_score
            ]

            return SanctionsCheckResult(
                search_name=entity_name,
                search_country=country,
                has_matches=len(filtered_matches) > 0,
                matches=filtered_matches
            )

        except Exception as e:
            self.logger.error(f"Error checking entity sanctions: {e}")
            return SanctionsCheckResult(
                search_name=entity_name,
                search_country=country,
                has_matches=False,
                error=str(e)
            )

    def get_sanctions_list_url(self, name: str) -> str:
        """
        Generate a URL to the OFAC sanctions search for manual verification.

        This allows users to manually verify results on the official website.
        """
        encoded_name = requests.utils.quote(name) if requests else name.replace(' ', '+')
        return f"https://sanctionssearch.ofac.treas.gov/?name={encoded_name}"
