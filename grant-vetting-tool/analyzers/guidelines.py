"""
Guidelines-based content analysis for the Grant Applicant Vetting Tool.

This module implements the HRF vetting guidelines and generates flags for
content that may violate them.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from .keywords import KeywordAnalyzer, KeywordMatch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.regime_classifications import (
    get_regime_classification,
    is_authoritarian_regime,
    KNOWN_AUTHORITARIAN_LEADERS,
)

logger = logging.getLogger(__name__)


@dataclass
class ContentFlag:
    """Represents a flag raised during content analysis."""
    category: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    evidence_snippet: Optional[str] = None
    matched_keywords: List[str] = field(default_factory=list)
    guideline_reference: Optional[str] = None
    content_source: Optional[str] = None
    content_url: Optional[str] = None
    published_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'evidence_snippet': self.evidence_snippet,
            'matched_keywords': self.matched_keywords,
            'guideline_reference': self.guideline_reference,
            'content_source': self.content_source,
            'content_url': self.content_url,
            'published_at': self.published_at,
        }


@dataclass
class AnalysisResult:
    """Result of analyzing an applicant's content."""
    applicant_id: Optional[int] = None
    total_content_items: int = 0
    flags: List[ContentFlag] = field(default_factory=list)
    risk_score: int = 0
    risk_level: str = 'low'  # 'low', 'medium', 'high', 'critical'
    recommendation: str = 'pending_review'  # 'approve', 'reject', 'pending_review'
    analyzed_at: datetime = field(default_factory=datetime.utcnow)
    summary: str = ''

    def to_dict(self) -> Dict:
        return {
            'applicant_id': self.applicant_id,
            'total_content_items': self.total_content_items,
            'flags_count': len(self.flags),
            'flags': [f.to_dict() for f in self.flags],
            'risk_score': self.risk_score,
            'risk_level': self.risk_level,
            'recommendation': self.recommendation,
            'analyzed_at': self.analyzed_at.isoformat(),
            'summary': self.summary,
        }


class GuidelinesAnalyzer:
    """
    Analyzes content against HRF vetting guidelines.

    Guidelines checked:
    1. Authoritarian regime connection
    2. Democracy criticism / false equivalences
    3. Excessive political partisanship
    4. Violence advocacy
    5. Hate speech / intolerance
    6. Regime praise / authoritarian sympathy
    7. Despot admiration
    8. Financial dealings with dictatorships
    9. Unprofessional conduct
    10. Criminal record
    11. Sanctions
    12. Business concerns
    """

    # Guideline definitions with descriptions
    GUIDELINES = {
        'authoritarian_connection': {
            'title': 'Authoritarian Regime Connection',
            'description': 'Individual is from and/or doing work relevant to a country with an authoritarian regime.',
            'reference': 'Guideline 1',
        },
        'democracy_criticism': {
            'title': 'Unqualified Democracy Criticism',
            'description': 'Engaged in unqualified criticism of democracies, making blunt equivalences between democracies and non-democracies.',
            'reference': 'Guideline 2',
        },
        'political_partisanship': {
            'title': 'Excessive Political Partisanship',
            'description': 'Displayed excessive political partisanship when dealing with democratic governments on social media.',
            'reference': 'Guideline 3',
        },
        'violence_advocacy': {
            'title': 'Violence Advocacy',
            'description': 'Has used or advocated for the use of violence as a valid method to fight government oppression.',
            'reference': 'Guideline 4',
        },
        'hate_speech': {
            'title': 'Hate Speech / Intolerance',
            'description': 'Expressed xenophobic, homophobic, or other intolerant views or opinions, or displayed clear instances of hate speech.',
            'reference': 'Guideline 5',
        },
        'regime_praise': {
            'title': 'Authoritarian Regime Relationship/Praise',
            'description': 'Has a relationship with, or expressed praise for, hybrid authoritarian or fully authoritarian regimes.',
            'reference': 'Guideline 6',
        },
        'despot_admiration': {
            'title': 'Despot/Dictator Admiration',
            'description': 'Expressed admiration for despots, dictators, or tyrants.',
            'reference': 'Guideline 7',
        },
        'financial_dealings': {
            'title': 'Financial Dealings with Dictatorships',
            'description': 'Engaged in significant financial or commercial dealings with dictatorships or their instrumentalities.',
            'reference': 'Guideline 8',
        },
        'unprofessional': {
            'title': 'Lack of Professionalism',
            'description': 'Displays a lack of professionalism.',
            'reference': 'Guideline 9',
        },
        'criminal_record': {
            'title': 'Criminal Record',
            'description': 'Has been investigated for, charged with, or convicted of any type of crime.',
            'reference': 'Guideline 10',
        },
        'sanctions': {
            'title': 'International Sanctions',
            'description': 'Subject to international sanctions.',
            'reference': 'Guideline 11',
        },
        'business_concerns': {
            'title': 'Business Ownership Concerns',
            'description': 'Owner or operator of private companies that HRF should be aware of.',
            'reference': 'Guideline 12',
        },
    }

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize the guidelines analyzer.

        Args:
            config: Optional configuration dict with:
                - custom_keywords: Additional keywords to check
                - llm_api_key: API key for LLM-based analysis (future)
                - strict_mode: If True, flag more aggressively
        """
        self.config = config or {}
        self.keyword_analyzer = KeywordAnalyzer(
            custom_keywords=self.config.get('custom_keywords')
        )
        self.strict_mode = self.config.get('strict_mode', False)
        self.logger = logging.getLogger(__name__)

    def analyze_applicant(
        self,
        applicant_data: Dict,
        content_items: List[Dict],
        social_profiles: List[Dict] = None
    ) -> AnalysisResult:
        """
        Analyze all content for an applicant.

        Args:
            applicant_data: Dict with applicant info (name, country, etc.)
            content_items: List of content items to analyze
            social_profiles: Optional list of social profile data

        Returns:
            AnalysisResult with flags and recommendations
        """
        result = AnalysisResult(
            applicant_id=applicant_data.get('id'),
            total_content_items=len(content_items)
        )

        # Check 1: Country classification
        country = applicant_data.get('country')
        if country:
            country_flags = self._check_country(country)
            result.flags.extend(country_flags)

        # Check 2: Analyze all content items
        for item in content_items:
            text = item.get('text_content', '')
            if not text:
                continue

            content_flags = self._analyze_content(
                text=text,
                source=item.get('platform', 'unknown'),
                url=item.get('url'),
                published_at=item.get('published_at')
            )
            result.flags.extend(content_flags)

        # Check 3: Analyze profile bios
        if social_profiles:
            for profile in social_profiles:
                bio = profile.get('bio', '')
                if bio:
                    bio_flags = self._analyze_content(
                        text=bio,
                        source=f"{profile.get('platform', 'unknown')}_bio",
                        url=profile.get('url')
                    )
                    result.flags.extend(bio_flags)

        # Calculate risk score and level
        result.risk_score = self._calculate_risk_score(result.flags)
        result.risk_level = self._determine_risk_level(result.risk_score)
        result.recommendation = self._generate_recommendation(result)
        result.summary = self._generate_summary(result)

        return result

    def _check_country(self, country: str) -> List[ContentFlag]:
        """Check if the applicant's country has regime concerns."""
        flags = []
        classification = get_regime_classification(country)

        if classification['classification'] == 'fully_authoritarian':
            flags.append(ContentFlag(
                category='authoritarian_connection',
                severity='high',
                title=f'From Fully Authoritarian Regime: {country}',
                description=f"The applicant is from {country}, which is classified as a fully authoritarian regime.",
                guideline_reference='Guideline 1'
            ))
        elif classification['classification'] == 'hybrid_authoritarian':
            flags.append(ContentFlag(
                category='authoritarian_connection',
                severity='medium',
                title=f'From Hybrid Authoritarian Regime: {country}',
                description=f"The applicant is from {country}, which is classified as a hybrid authoritarian regime.",
                guideline_reference='Guideline 1'
            ))

        return flags

    def _analyze_content(
        self,
        text: str,
        source: str = 'unknown',
        url: Optional[str] = None,
        published_at: Optional[str] = None
    ) -> List[ContentFlag]:
        """Analyze a single piece of content for guideline violations."""
        flags = []

        # Run keyword analysis
        matches = self.keyword_analyzer.analyze_text(text)

        # Group matches by category
        matches_by_category: Dict[str, List[KeywordMatch]] = {}
        for match in matches:
            if match.category not in matches_by_category:
                matches_by_category[match.category] = []
            matches_by_category[match.category].append(match)

        # Generate flags for each category
        for category, category_matches in matches_by_category.items():
            # Determine highest severity in this category
            severity_order = ['critical', 'high', 'medium', 'low']
            highest_severity = 'low'
            for sev in severity_order:
                if any(m.severity == sev for m in category_matches):
                    highest_severity = sev
                    break

            # Get the best evidence snippet (highest severity match)
            best_match = max(category_matches, key=lambda m: severity_order.index(m.severity) if m.severity in severity_order else 99)

            # Map keyword category to guideline category
            guideline_category = self._map_keyword_to_guideline(category)
            guideline = self.GUIDELINES.get(guideline_category, {})

            flag = ContentFlag(
                category=guideline_category,
                severity=highest_severity,
                title=guideline.get('title', f'Potential Issue: {category}'),
                description=f"Content may violate: {guideline.get('description', category)}",
                evidence_snippet=best_match.context,
                matched_keywords=[m.keyword for m in category_matches],
                guideline_reference=guideline.get('reference'),
                content_source=source,
                content_url=url,
                published_at=published_at
            )
            flags.append(flag)

        # Check for authoritarian mentions (informational, lower severity)
        auth_mentions = self.keyword_analyzer.check_for_authoritarian_mentions(text)
        if auth_mentions and self.strict_mode:
            # Only flag in strict mode since mentions alone aren't violations
            for mention in auth_mentions[:5]:  # Limit to 5 mentions
                flags.append(ContentFlag(
                    category='regime_praise',
                    severity='low',
                    title=f'Mentions {mention.keyword}',
                    description=f"Content mentions {mention.category.replace('_', ' ')}: {mention.keyword}",
                    evidence_snippet=mention.context,
                    matched_keywords=[mention.keyword],
                    content_source=source,
                    content_url=url,
                    published_at=published_at
                ))

        return flags

    def _map_keyword_to_guideline(self, keyword_category: str) -> str:
        """Map keyword analyzer categories to guideline categories."""
        mapping = {
            'violence_advocacy': 'violence_advocacy',
            'hate_speech': 'hate_speech',
            'regime_praise': 'regime_praise',
            'democracy_criticism': 'democracy_criticism',
            'despot_admiration': 'despot_admiration',
            'financial_dealings': 'financial_dealings',
            'unprofessional': 'unprofessional',
            'criminal_activity': 'criminal_record',
            'authoritarian_mention': 'regime_praise',
            'authoritarian_entity_mention': 'regime_praise',
            'authoritarian_country_mention': 'authoritarian_connection',
        }
        return mapping.get(keyword_category, keyword_category)

    def _calculate_risk_score(self, flags: List[ContentFlag]) -> int:
        """Calculate overall risk score from flags."""
        if not flags:
            return 0

        severity_weights = {
            'critical': 30,
            'high': 20,
            'medium': 10,
            'low': 3
        }

        total = sum(
            severity_weights.get(flag.severity, 0)
            for flag in flags
        )

        # Cap at 100
        return min(100, total)

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level from score."""
        if score >= 70:
            return 'critical'
        elif score >= 40:
            return 'high'
        elif score >= 20:
            return 'medium'
        else:
            return 'low'

    def _generate_recommendation(self, result: AnalysisResult) -> str:
        """Generate a recommendation based on analysis."""
        # Auto-reject for critical issues
        critical_categories = ['violence_advocacy', 'hate_speech', 'despot_admiration']
        critical_flags = [
            f for f in result.flags
            if f.severity == 'critical' or
            (f.severity == 'high' and f.category in critical_categories)
        ]

        if critical_flags:
            return 'reject'

        # Recommend review for medium/high risk
        if result.risk_level in ['high', 'critical']:
            return 'pending_review'

        if result.risk_level == 'medium':
            return 'pending_review'

        # Low risk with no significant flags
        if result.risk_score < 10 and not any(f.severity in ['high', 'critical'] for f in result.flags):
            return 'approve'

        return 'pending_review'

    def _generate_summary(self, result: AnalysisResult) -> str:
        """Generate a human-readable summary of the analysis."""
        if not result.flags:
            return "No concerning content found. Applicant appears to meet vetting guidelines."

        # Count flags by severity
        severity_counts = {}
        for flag in result.flags:
            severity_counts[flag.severity] = severity_counts.get(flag.severity, 0) + 1

        # Count flags by category
        category_counts = {}
        for flag in result.flags:
            category_counts[flag.category] = category_counts.get(flag.category, 0) + 1

        summary_parts = [
            f"Analysis found {len(result.flags)} potential issue(s)."
        ]

        if severity_counts.get('critical'):
            summary_parts.append(f"CRITICAL: {severity_counts['critical']} critical issue(s) found.")
        if severity_counts.get('high'):
            summary_parts.append(f"HIGH: {severity_counts['high']} high-severity issue(s) found.")

        # List categories with issues
        category_list = ', '.join(
            self.GUIDELINES.get(cat, {}).get('title', cat)
            for cat in category_counts.keys()
        )
        summary_parts.append(f"Categories: {category_list}")

        summary_parts.append(f"Risk Level: {result.risk_level.upper()}")
        summary_parts.append(f"Recommendation: {result.recommendation.replace('_', ' ').upper()}")

        return ' '.join(summary_parts)

    def analyze_single_content(
        self,
        text: str,
        source: str = 'unknown'
    ) -> List[ContentFlag]:
        """
        Analyze a single piece of content.

        Useful for real-time checking or one-off analysis.
        """
        return self._analyze_content(text, source)
