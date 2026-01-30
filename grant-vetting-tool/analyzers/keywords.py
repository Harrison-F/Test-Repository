"""
Keyword-based content analysis for the Grant Applicant Vetting Tool.

This module defines keywords and patterns for detecting potentially concerning
content based on the HRF vetting guidelines.
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Import regime data
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.regime_classifications import (
    KNOWN_AUTHORITARIAN_LEADERS,
    AUTHORITARIAN_ENTITIES,
    ALL_FULLY_AUTHORITARIAN,
    ALL_HYBRID_AUTHORITARIAN,
)


@dataclass
class KeywordMatch:
    """Represents a keyword match in content."""
    keyword: str
    category: str
    severity: str
    context: str  # Surrounding text
    position: int


class KeywordAnalyzer:
    """
    Analyzer for detecting concerning content via keyword matching.

    Categories map to the HRF vetting guidelines.
    """

    def __init__(self, custom_keywords: Optional[Dict] = None):
        """
        Initialize the keyword analyzer.

        Args:
            custom_keywords: Optional dict of category -> keyword list to add/override
        """
        self.keywords = self._build_keyword_database()
        if custom_keywords:
            for category, keywords in custom_keywords.items():
                if category in self.keywords:
                    self.keywords[category].extend(keywords)
                else:
                    self.keywords[category] = keywords

    def _build_keyword_database(self) -> Dict[str, List[Tuple[str, str]]]:
        """
        Build the keyword database organized by category.

        Returns dict of category -> list of (keyword/pattern, severity)
        """
        return {
            # Category: Violence Advocacy
            'violence_advocacy': [
                # High severity - explicit calls for violence
                (r'\b(kill|murder|assassinate|execute)\s+(the\s+)?(government|president|leader|politician)', 'critical'),
                (r'\bviolent\s+(revolution|uprising|overthrow)\b', 'high'),
                (r'\b(armed|violent)\s+resistance\b', 'high'),
                (r'\btake\s+up\s+arms\b', 'high'),
                (r'\bblood\s+(must|will|shall)\s+(flow|be\s+spilled)\b', 'high'),
                (r'\bonly\s+(violence|war)\s+(can|will)\s+solve\b', 'high'),
                (r'\bpeaceful\s+protest\s+(is\s+)?useless\b', 'medium'),
                (r'\b(support|celebrate)\s+(terrorism|terrorist)\b', 'critical'),

                # Medium severity - ambiguous language
                (r'\bby\s+any\s+means\s+necessary\b', 'medium'),
                (r'\btime\s+for\s+action\b', 'low'),
            ],

            # Category: Hate Speech / Intolerance
            'hate_speech': [
                # Ethnic/racial slurs - critical severity
                # Note: Being careful not to include words that could have legitimate uses
                (r'\b(subhuman|untermensch)\b', 'critical'),
                (r'\bethnic\s+cleansing\b', 'critical'),
                (r'\b(racial|white|black|jewish|muslim)\s+supremacy\b', 'critical'),

                # Homophobic language
                (r'\b(homosexuality|being\s+gay)\s+(is\s+)?(a\s+)?(sin|disease|mental\s+illness|abomination)\b', 'high'),
                (r'\b(gay|lgbt)\s+agenda\b', 'medium'),
                (r'\banti-(gay|lgbt|homosexual)\b', 'medium'),

                # Xenophobic language
                (r'\b(immigrants?|refugees?|migrants?)\s+(are\s+)?(all\s+)?(criminals?|terrorists?|invaders?)\b', 'high'),
                (r'\bclose\s+the\s+borders?\b', 'low'),
                (r'\b(invasion|great\s+replacement)\b', 'medium'),

                # Religious intolerance
                (r'\b(ban|outlaw)\s+(islam|muslims?|christianity|christians?|judaism|jews?)\b', 'high'),
                (r'\b(all\s+)?(muslims?|jews?|christians?)\s+(are\s+)?(terrorists?|evil)\b', 'critical'),

                # General hate
                (r'\b(death\s+to|kill\s+all)\s+\w+\b', 'critical'),
            ],

            # Category: Authoritarian Regime Praise
            'regime_praise': [
                # Direct praise patterns
                (r'\b(great|strong|effective|successful)\s+(leader|leadership)\b.*(' + '|'.join(
                    re.escape(leader) for leader in KNOWN_AUTHORITARIAN_LEADERS[:20]
                ) + ')', 'high'),
                (r'\b(' + '|'.join(
                    re.escape(leader) for leader in KNOWN_AUTHORITARIAN_LEADERS[:20]
                ) + r')\s+(is|was)\s+(right|correct|great|visionary)\b', 'high'),

                # Regime defense
                (r'\b(china|russia|iran|cuba|venezuela|north\s+korea)\s+(is\s+)?(actually|not\s+that)\s+(democratic|free|good)\b', 'high'),
                (r'\bwestern\s+(propaganda|lies)\s+about\s+(china|russia|iran)\b', 'medium'),
                (r'\b(ccp|chinese\s+communist\s+party)\s+(is\s+)?(effective|good|successful)\b', 'high'),
            ],

            # Category: Democracy Equivalence / Criticism
            'democracy_criticism': [
                # Equivalence between democracies and non-democracies
                (r'\b(us|usa|america|west|europe)\s+(is\s+)?(just\s+as\s+bad|no\s+better|worse\s+than)\s+(china|russia|iran)\b', 'high'),
                (r'\bdemocracy\s+(is\s+)?(a\s+)?(lie|illusion|facade|sham)\b', 'medium'),
                (r'\b(western|american)\s+(democracy|freedom)\s+(is\s+)?(fake|false|hypocrisy)\b', 'medium'),
                (r'\bso-called\s+(free|democratic)\s+(world|countries)\b', 'medium'),

                # Anti-democratic sentiment
                (r'\bdemocracy\s+(doesn\'t|does\s+not)\s+work\b', 'medium'),
                (r'\bauthoritarian\s+(systems?|regimes?)\s+(are\s+)?(more\s+)?(efficient|effective)\b', 'high'),
            ],

            # Category: Despot Admiration
            'despot_admiration': [
                # Patterns for admiring historical dictators
                (r'\b(hitler|stalin|mao|pol\s+pot)\s+(was\s+)?(right|correct|misunderstood)\b', 'critical'),
                (r'\b(admire|respect|support)\s+(hitler|stalin|mao|pol\s+pot|mussolini|franco)\b', 'critical'),
                (r'\b(hitler|stalin|mao)\s+did\s+(some\s+)?(good|nothing\s+wrong)\b', 'critical'),

                # Current authoritarian leaders - create patterns dynamically
            ] + [
                (rf'\b(admire|respect|support)\s+{re.escape(leader)}\b', 'high')
                for leader in KNOWN_AUTHORITARIAN_LEADERS[:30]
            ],

            # Category: Financial Dealings with Dictatorships
            'financial_dealings': [
                (r'\b(business|deal|contract|investment)\s+(with|in)\s+(russia|china|iran|north\s+korea|venezuela|cuba|syria)\b', 'medium'),
                (r'\b(partnership|collaboration)\s+(with|for)\s+(' + '|'.join(
                    re.escape(entity) for entity in AUTHORITARIAN_ENTITIES
                ) + ')', 'high'),
                (r'\b(funded|financed|sponsored)\s+by\s+(russia|china|iran|qatar|saudi)\b', 'high'),
            ],

            # Category: Unprofessional Conduct
            'unprofessional': [
                # Explicit content
                (r'\b(fuck|shit|damn)\s+(you|this|that|everyone)\b', 'low'),
                (r'\b(idiot|moron|stupid|dumb)\b', 'low'),

                # Harassment patterns
                (r'\b(harass|stalk|threaten)\b', 'medium'),
                (r'\b(dox|doxx|doxxing)\b', 'medium'),

                # Conspiracy theories
                (r'\b(flat\s+earth|moon\s+landing\s+(was\s+)?fake|chemtrails)\b', 'low'),
                (r'\b(illuminati|deep\s+state|new\s+world\s+order)\s+(controls?|runs?)\b', 'low'),
            ],

            # Category: Criminal Activity
            'criminal_activity': [
                (r'\b(arrested|charged|convicted|indicted)\s+(for|of|with)\b', 'medium'),
                (r'\b(fraud|embezzlement|corruption|bribery)\s+(charges?|conviction|scandal)\b', 'high'),
                (r'\b(assault|battery)\s+(charges?|conviction)\b', 'high'),
                (r'\b(sexual\s+)?(harassment|misconduct)\s+(allegations?|charges?|lawsuit)\b', 'high'),
            ],
        }

    def analyze_text(self, text: str, categories: Optional[List[str]] = None) -> List[KeywordMatch]:
        """
        Analyze text for keyword matches.

        Args:
            text: The text to analyze
            categories: Optional list of categories to check (defaults to all)

        Returns:
            List of KeywordMatch objects
        """
        if not text:
            return []

        matches = []
        text_lower = text.lower()

        categories_to_check = categories or list(self.keywords.keys())

        for category in categories_to_check:
            if category not in self.keywords:
                continue

            for pattern, severity in self.keywords[category]:
                try:
                    for match in re.finditer(pattern, text_lower, re.IGNORECASE):
                        # Extract context (50 chars before and after)
                        start = max(0, match.start() - 50)
                        end = min(len(text), match.end() + 50)
                        context = text[start:end]

                        # Add ellipsis if truncated
                        if start > 0:
                            context = '...' + context
                        if end < len(text):
                            context = context + '...'

                        matches.append(KeywordMatch(
                            keyword=match.group(0),
                            category=category,
                            severity=severity,
                            context=context,
                            position=match.start()
                        ))
                except re.error as e:
                    # Log but don't fail on bad regex
                    continue

        return matches

    def check_for_authoritarian_mentions(self, text: str) -> List[KeywordMatch]:
        """
        Check for mentions of authoritarian leaders, regimes, or entities.

        Returns matches with context.
        """
        matches = []
        text_lower = text.lower()

        # Check for leader mentions
        for leader in KNOWN_AUTHORITARIAN_LEADERS:
            leader_lower = leader.lower()
            for match in re.finditer(re.escape(leader_lower), text_lower):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                matches.append(KeywordMatch(
                    keyword=leader,
                    category='authoritarian_mention',
                    severity='medium',
                    context=context,
                    position=match.start()
                ))

        # Check for entity mentions
        for entity in AUTHORITARIAN_ENTITIES:
            entity_lower = entity.lower()
            for match in re.finditer(re.escape(entity_lower), text_lower):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                matches.append(KeywordMatch(
                    keyword=entity,
                    category='authoritarian_entity_mention',
                    severity='medium',
                    context=context,
                    position=match.start()
                ))

        # Check for country mentions (authoritarian)
        for country in ALL_FULLY_AUTHORITARIAN + ALL_HYBRID_AUTHORITARIAN:
            country_lower = country.lower()
            # Only match if it's a word boundary
            pattern = rf'\b{re.escape(country_lower)}\b'
            for match in re.finditer(pattern, text_lower):
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end]

                matches.append(KeywordMatch(
                    keyword=country,
                    category='authoritarian_country_mention',
                    severity='low',
                    context=context,
                    position=match.start()
                ))

        return matches

    def get_severity_score(self, matches: List[KeywordMatch]) -> int:
        """
        Calculate an overall severity score from matches.

        Returns a score from 0-100.
        """
        if not matches:
            return 0

        severity_weights = {
            'critical': 25,
            'high': 15,
            'medium': 8,
            'low': 3
        }

        total_score = sum(
            severity_weights.get(match.severity, 0)
            for match in matches
        )

        # Cap at 100
        return min(100, total_score)

    def add_keywords(self, category: str, keywords: List[Tuple[str, str]]):
        """
        Add keywords to a category.

        Args:
            category: The category name
            keywords: List of (pattern, severity) tuples
        """
        if category not in self.keywords:
            self.keywords[category] = []
        self.keywords[category].extend(keywords)
