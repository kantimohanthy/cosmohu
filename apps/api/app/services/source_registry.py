"""
SOURCE REGISTRY MODULE (STAGE 4.4 ENHANCED)
--------------------------------------------
Manages authoritative space economy sources with explicit tiering, source categories,
entity scoping, provenance tracking, and crawl lifecycle management.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
from app.services.crawler import SourceQualityTier, determine_source_tier
from app.models.schemas import SourceType

class SourceCategory(str, Enum):
    OFFICIAL_COMPANY = "OFFICIAL_COMPANY"
    ESA = "ESA"
    EU_INSTITUTION = "EU_INSTITUTION"
    GOVERNMENT = "GOVERNMENT"
    REGULATOR = "REGULATOR"
    INVESTOR = "INVESTOR"
    ACADEMIC = "ACADEMIC"
    INDUSTRY_PUBLICATION = "INDUSTRY_PUBLICATION"
    NEWS = "NEWS"
    DATABASE = "DATABASE"
    OTHER = "OTHER"

class RegisteredSource(BaseModel):
    source_id: str
    publisher: str
    source_url: str
    source_tier: str = SourceQualityTier.TIER_1
    source_type: SourceType = SourceType.WEB
    category: SourceCategory = SourceCategory.OFFICIAL_COMPANY
    entity_scope: List[str] = Field(default_factory=list)
    enabled: bool = True
    last_crawled: Optional[str] = None
    provenance_status: str = "LIVE"
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Authoritative Space Economy Source Registry
AUTHORITATIVE_SOURCE_REGISTRY: List[RegisteredSource] = [
    # 1. ESA & Institutional Sources
    RegisteredSource(
        source_id="src_esa_transport",
        publisher="European Space Agency (ESA)",
        source_url="https://www.esa.int/Enabling_Support/Space_Transportation",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.ESA,
        entity_scope=["esa", "launch", "ariane6", "vega", "pld", "isar", "rfa", "orbex", "maia"],
        enabled=True,
        provenance_status="LIVE"
    ),
    RegisteredSource(
        source_id="src_eib_financing",
        publisher="European Investment Bank (EIB)",
        source_url="https://www.eib.org/en/projects/all/index.htm",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.EU_INSTITUTION,
        entity_scope=["eib", "pld", "isar", "maia", "funding"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 2. PLD Space
    RegisteredSource(
        source_id="src_pld_official",
        publisher="PLD Space Official",
        source_url="https://www.pldspace.com",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["pld", "miura", "launch"],
        enabled=True,
        provenance_status="LIVE"
    ),
    RegisteredSource(
        source_id="src_pld_miura5_spec",
        publisher="PLD Space Technical Documentation",
        source_url="https://www.pldspace.com/en/miura-5.html",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["pld", "miura"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 3. Isar Aerospace
    RegisteredSource(
        source_id="src_isar_official",
        publisher="Isar Aerospace Official",
        source_url="https://www.isaraerospace.com",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["isar", "spectrum", "launch"],
        enabled=True,
        provenance_status="LIVE"
    ),
    RegisteredSource(
        source_id="src_isar_spectrum_spec",
        publisher="Isar Aerospace Spectrum Overview",
        source_url="https://www.isaraerospace.com/spectrum.html",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["isar", "spectrum"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 4. Rocket Factory Augsburg (RFA)
    RegisteredSource(
        source_id="src_rfa_official",
        publisher="Rocket Factory Augsburg (RFA)",
        source_url="https://www.rfa.space",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["rfa", "rfaone", "launch"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 5. Orbex
    RegisteredSource(
        source_id="src_orbex_official",
        publisher="Orbex Official",
        source_url="https://www.orbex.space",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["orbex", "prime", "launch"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 6. MaiaSpace
    RegisteredSource(
        source_id="src_maiaspace_official",
        publisher="MaiaSpace Official",
        source_url="https://www.maiaspace.com",
        source_tier=SourceQualityTier.TIER_1,
        source_type=SourceType.WEB,
        category=SourceCategory.OFFICIAL_COMPANY,
        entity_scope=["maia", "colibri", "launch"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 7. Industry News / Tier 3
    RegisteredSource(
        source_id="src_euro_spaceflight",
        publisher="European Spaceflight News",
        source_url="https://europeanspaceflight.com",
        source_tier=SourceQualityTier.TIER_3,
        source_type=SourceType.WEB,
        category=SourceCategory.INDUSTRY_PUBLICATION,
        entity_scope=["launch", "isar", "pld", "rfa", "maia", "orbex"],
        enabled=True,
        provenance_status="LIVE"
    ),
    # 8. Wikipedia Redirect Mismatch Negative Test
    RegisteredSource(
        source_id="src_maiaspace_wiki",
        publisher="Wikipedia / Redirect Mismatch Test",
        source_url="https://en.wikipedia.org/wiki/MaiaSpace",
        source_tier=SourceQualityTier.TIER_4,
        source_type=SourceType.WEB,
        category=SourceCategory.OTHER,
        entity_scope=["maia"],
        enabled=True,
        provenance_status="LIVE"
    )
]

class SourceRegistryService:
    def __init__(self, sources: Optional[List[RegisteredSource]] = None):
        self.sources = {s.source_id: s for s in (sources or AUTHORITATIVE_SOURCE_REGISTRY)}

    def list_sources(self, enabled_only: bool = True) -> List[RegisteredSource]:
        if enabled_only:
            return [s for s in self.sources.values() if s.enabled]
        return list(self.sources.values())

    def get_source(self, source_id: str) -> Optional[RegisteredSource]:
        return self.sources.get(source_id)

    def register_source(self, source: RegisteredSource) -> RegisteredSource:
        self.sources[source.source_id] = source
        return source

source_registry = SourceRegistryService()

def get_source_roots_for_entity(entity_id: str) -> List[RegisteredSource]:
    """Returns registered authoritative source roots for a given entity."""
    return [s for s in source_registry.list_sources(enabled_only=True) if entity_id in s.entity_scope]
