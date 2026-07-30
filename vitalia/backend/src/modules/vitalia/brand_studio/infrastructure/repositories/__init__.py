# cap: brand_studio.brand-studio-medical-sections
# story-origin: vitalia-fase2-s7-TBD
"""Brand studio infrastructure repositories — ABCs + impls."""

from .prohibited_phrase_repository import ProhibitedPhraseRepository
from .prohibited_phrase_repository_impl import ProhibitedPhraseRepositoryImpl
from .trust_signal_repository import TrustSignalRepository
from .trust_signal_repository_impl import TrustSignalRepositoryImpl

__all__ = [
    "ProhibitedPhraseRepository",
    "ProhibitedPhraseRepositoryImpl",
    "TrustSignalRepository",
    "TrustSignalRepositoryImpl",
]
