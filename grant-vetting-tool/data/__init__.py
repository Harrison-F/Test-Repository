"""
Data module containing static data for the Grant Applicant Vetting Tool.
"""

from .regime_classifications import (
    get_regime_classification,
    is_authoritarian_regime,
    is_fully_authoritarian,
    is_hybrid_authoritarian,
    ALL_DEMOCRATIC,
    ALL_HYBRID_AUTHORITARIAN,
    ALL_FULLY_AUTHORITARIAN,
    ALL_AUTHORITARIAN,
    KNOWN_AUTHORITARIAN_LEADERS,
    AUTHORITARIAN_ENTITIES,
)

__all__ = [
    'get_regime_classification',
    'is_authoritarian_regime',
    'is_fully_authoritarian',
    'is_hybrid_authoritarian',
    'ALL_DEMOCRATIC',
    'ALL_HYBRID_AUTHORITARIAN',
    'ALL_FULLY_AUTHORITARIAN',
    'ALL_AUTHORITARIAN',
    'KNOWN_AUTHORITARIAN_LEADERS',
    'AUTHORITARIAN_ENTITIES',
]
