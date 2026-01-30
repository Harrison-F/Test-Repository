"""
Configuration for the Grant Applicant Vetting Tool.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///grant_vetting.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Apify settings (for Twitter/Instagram scraping)
    APIFY_API_TOKEN = os.environ.get('APIFY_API_TOKEN', '')

    # Nostr settings
    NOSTR_RELAYS = [
        "wss://relay.damus.io",
        "wss://relay.nostr.band",
        "wss://nos.lol",
        "wss://relay.snort.social",
        "wss://relay.primal.net",
    ]
    NOSTR_TIMEOUT = 10
    NOSTR_MAX_EVENTS = 500

    # Scraping settings
    SCRAPE_TIMEOUT = 30
    MAX_CONTENT_ITEMS_PER_PROFILE = 200

    # Analysis settings
    ANALYSIS_STRICT_MODE = False

    # LLM settings (for future use)
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

    # Sanctions check settings
    SANCTIONS_MIN_SCORE = 80

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

    # Override secret key requirement
    @property
    def SECRET_KEY(self):
        key = os.environ.get('SECRET_KEY')
        if not key:
            raise ValueError('SECRET_KEY environment variable must be set in production')
        return key


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
