"""
Database models for the Grant Applicant Vetting Tool.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Text, JSON

db = SQLAlchemy()


class Applicant(db.Model):
    """Represents a grant applicant being vetted."""
    __tablename__ = 'applicants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    organization = db.Column(db.String(255), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    notes = db.Column(Text, nullable=True)

    # Vetting status: pending, in_progress, passed, failed, needs_review
    status = db.Column(db.String(50), default='pending')

    # Overall risk level: low, medium, high, critical
    risk_level = db.Column(db.String(50), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    vetted_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    social_profiles = db.relationship('SocialProfile', backref='applicant', lazy=True, cascade='all, delete-orphan')
    content_items = db.relationship('ContentItem', backref='applicant', lazy=True, cascade='all, delete-orphan')
    flags = db.relationship('Flag', backref='applicant', lazy=True, cascade='all, delete-orphan')
    sanctions_check = db.relationship('SanctionsCheck', backref='applicant', uselist=False, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Applicant {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'organization': self.organization,
            'country': self.country,
            'notes': self.notes,
            'status': self.status,
            'risk_level': self.risk_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'vetted_at': self.vetted_at.isoformat() if self.vetted_at else None,
            'social_profiles': [p.to_dict() for p in self.social_profiles],
            'flags_count': len(self.flags),
            'high_severity_flags': len([f for f in self.flags if f.severity in ['high', 'critical']])
        }


class SocialProfile(db.Model):
    """Represents a social media profile for an applicant."""
    __tablename__ = 'social_profiles'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)

    # Platform: twitter, nostr, instagram, linkedin, blog, other
    platform = db.Column(db.String(50), nullable=False)

    # Profile identifiers
    username = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    platform_id = db.Column(db.String(255), nullable=True)  # e.g., Nostr pubkey

    # Discovery method: provided, discovered, linked
    discovery_method = db.Column(db.String(50), default='provided')

    # Scraping status: pending, in_progress, completed, failed
    scrape_status = db.Column(db.String(50), default='pending')
    last_scraped_at = db.Column(db.DateTime, nullable=True)
    scrape_error = db.Column(Text, nullable=True)

    # Profile metadata
    display_name = db.Column(db.String(255), nullable=True)
    bio = db.Column(Text, nullable=True)
    followers_count = db.Column(db.Integer, nullable=True)
    following_count = db.Column(db.Integer, nullable=True)
    posts_count = db.Column(db.Integer, nullable=True)
    profile_image_url = db.Column(db.String(500), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<SocialProfile {self.platform}:{self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'username': self.username,
            'url': self.url,
            'platform_id': self.platform_id,
            'discovery_method': self.discovery_method,
            'scrape_status': self.scrape_status,
            'last_scraped_at': self.last_scraped_at.isoformat() if self.last_scraped_at else None,
            'display_name': self.display_name,
            'bio': self.bio,
            'followers_count': self.followers_count,
            'following_count': self.following_count,
            'posts_count': self.posts_count
        }


class ContentItem(db.Model):
    """Represents a piece of content (post, tweet, article) from an applicant."""
    __tablename__ = 'content_items'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)
    social_profile_id = db.Column(db.Integer, db.ForeignKey('social_profiles.id'), nullable=True)

    # Content type: post, tweet, article, comment, reply, repost
    content_type = db.Column(db.String(50), nullable=False)

    # Platform source
    platform = db.Column(db.String(50), nullable=False)

    # Content identifiers
    platform_content_id = db.Column(db.String(255), nullable=True)
    url = db.Column(db.String(500), nullable=True)

    # The actual content
    text_content = db.Column(Text, nullable=True)
    raw_content = db.Column(JSON, nullable=True)  # Store original JSON

    # Content metadata
    published_at = db.Column(db.DateTime, nullable=True)
    likes_count = db.Column(db.Integer, nullable=True)
    reposts_count = db.Column(db.Integer, nullable=True)
    replies_count = db.Column(db.Integer, nullable=True)

    # Media attachments (stored as JSON array of URLs)
    media_urls = db.Column(JSON, nullable=True)

    # Analysis status
    analyzed = db.Column(db.Boolean, default=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to flags
    flags = db.relationship('Flag', backref='content_item', lazy=True)

    def __repr__(self):
        return f'<ContentItem {self.platform}:{self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'platform': self.platform,
            'url': self.url,
            'text_content': self.text_content,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'likes_count': self.likes_count,
            'reposts_count': self.reposts_count,
            'replies_count': self.replies_count,
            'media_urls': self.media_urls,
            'flags': [f.to_dict() for f in self.flags]
        }


class Flag(db.Model):
    """Represents a flagged issue found during vetting."""
    __tablename__ = 'flags'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)
    content_item_id = db.Column(db.Integer, db.ForeignKey('content_items.id'), nullable=True)

    # Flag category (matches your guidelines)
    category = db.Column(db.String(100), nullable=False)
    # Categories:
    # - authoritarian_connection: Connection to authoritarian regime
    # - democracy_criticism: Unqualified criticism equating democracies with non-democracies
    # - political_partisanship: Excessive political partisanship
    # - violence_advocacy: Advocacy for violence
    # - hate_speech: Xenophobic, homophobic, or intolerant views
    # - regime_praise: Praise for authoritarian/hybrid regimes
    # - despot_admiration: Admiration for despots/dictators
    # - financial_dealings: Financial dealings with dictatorships
    # - unprofessional: Lack of professionalism
    # - criminal_record: Criminal investigation/charges/conviction
    # - sanctions: Subject to international sanctions
    # - business_concerns: Concerning business ownership

    # Severity: low, medium, high, critical
    severity = db.Column(db.String(50), nullable=False)

    # Flag details
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(Text, nullable=True)
    matched_keywords = db.Column(JSON, nullable=True)  # Keywords that triggered this flag
    evidence_snippet = db.Column(Text, nullable=True)  # Relevant text snippet

    # Review status: pending, confirmed, dismissed
    review_status = db.Column(db.String(50), default='pending')
    reviewed_by = db.Column(db.String(255), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(Text, nullable=True)

    # Detection method: keyword, pattern, manual, llm
    detection_method = db.Column(db.String(50), default='keyword')

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Flag {self.category}:{self.severity}>'

    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'matched_keywords': self.matched_keywords,
            'evidence_snippet': self.evidence_snippet,
            'review_status': self.review_status,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_notes': self.review_notes,
            'detection_method': self.detection_method,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SanctionsCheck(db.Model):
    """Represents an OFAC sanctions check for an applicant."""
    __tablename__ = 'sanctions_checks'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)

    # Check status: pending, completed, error
    status = db.Column(db.String(50), default='pending')

    # Results
    has_matches = db.Column(db.Boolean, default=False)
    matches = db.Column(JSON, nullable=True)  # Store match details

    # Search parameters used
    search_name = db.Column(db.String(255), nullable=True)
    search_country = db.Column(db.String(100), nullable=True)

    # Timestamps
    checked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SanctionsCheck applicant={self.applicant_id} matches={self.has_matches}>'

    def to_dict(self):
        return {
            'id': self.id,
            'status': self.status,
            'has_matches': self.has_matches,
            'matches': self.matches,
            'search_name': self.search_name,
            'search_country': self.search_country,
            'checked_at': self.checked_at.isoformat() if self.checked_at else None
        }


class VettingReport(db.Model):
    """Represents a generated vetting report for an applicant."""
    __tablename__ = 'vetting_reports'

    id = db.Column(db.Integer, primary_key=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey('applicants.id'), nullable=False)

    # Report content
    summary = db.Column(Text, nullable=True)
    recommendation = db.Column(db.String(50), nullable=True)  # approve, reject, review

    # Full report data
    report_data = db.Column(JSON, nullable=True)

    # Generated by
    generated_by = db.Column(db.String(255), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    applicant = db.relationship('Applicant', backref=db.backref('reports', lazy=True))

    def __repr__(self):
        return f'<VettingReport applicant={self.applicant_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'applicant_id': self.applicant_id,
            'summary': self.summary,
            'recommendation': self.recommendation,
            'report_data': self.report_data,
            'generated_by': self.generated_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
