"""Configuration for free-source news intelligence modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class NewsModule:
    key: str
    label: str
    group: str
    subgroup: str
    description: str
    queries: Sequence[str]
    include_terms: Sequence[str] = ()
    exclude_terms: Sequence[str] = ()
    required_terms: Sequence[str] = ()
    priority_sources: Sequence[str] = ()
    watch_entities: Sequence[str] = ()


GLOBAL_NEWS_TERMS = (
    "politics",
    "election",
    "war",
    "conflict",
    "sanctions",
    "finance",
    "markets",
    "central bank",
    "inflation",
    "policy",
    "trade",
    "energy",
    "geopolitics",
)

INDIA_TERMS = (
    "india",
    "indian",
    "modi",
    "parliament",
    "rbi",
    "budget",
    "policy",
    "andhra",
    "telangana",
    "hyderabad",
    "amaravati",
    "vijayawada",
    "investment",
    "markets",
)

PHARMA_TERMS = (
    "pharma",
    "pharmaceutical",
    "biotech",
    "drug",
    "therapy",
    "clinical",
    "fda",
    "ema",
    "approval",
    "healthcare",
    "hospital",
    "medtech",
)

HEALTHCARE_TOPIC_TERMS = PHARMA_TERMS + (
    "biopharma",
    "life sciences",
    "medicine",
    "medicines",
    "medical",
    "clinic",
    "clinics",
    "diagnostics",
    "patient",
    "patients",
    "vaccine",
    "vaccines",
    "manufacturing",
)

DEAL_TERMS = (
    "acquisition",
    "merger",
    "m&a",
    "deal",
    "licensing",
    "partnership",
    "collaboration",
    "investment",
    "joint venture",
    "funding",
)

INNOVATION_TERMS = (
    "approval",
    "approved",
    "breakthrough",
    "trial",
    "phase 3",
    "phase iii",
    "launch",
    "innovation",
    "new drug",
    "therapy",
    "vaccine",
    "fda",
    "ema",
)

MIDDLE_EAST_TERMS = (
    "middle east",
    "uae",
    "saudi",
    "ksa",
    "qatar",
    "oman",
    "kuwait",
    "bahrain",
    "egypt",
    "jordan",
    "gcc",
    "mena",
    "dubai",
    "abu dhabi",
    "riyadh",
)

GLOBAL_PRIORITY_SOURCES = (
    "reuters.com",
    "ft.com",
    "bloomberg.com",
    "wsj.com",
    "economist.com",
    "apnews.com",
    "bbc.com",
    "aljazeera.com",
)

INDIA_PRIORITY_SOURCES = (
    "economictimes.indiatimes.com",
    "business-standard.com",
    "livemint.com",
    "thehindu.com",
    "indianexpress.com",
    "moneycontrol.com",
    "vccircle.com",
)

PHARMA_PRIORITY_SOURCES = (
    "reuters.com",
    "ft.com",
    "bloomberg.com",
    "fiercepharma.com",
    "fiercebiotech.com",
    "endpts.com",
    "statnews.com",
    "biopharmadive.com",
    "pharmaphorum.com",
    "pharmaboardroom.com",
)

MIDDLE_EAST_PRIORITY_SOURCES = (
    "zawya.com",
    "gulfbusiness.com",
    "agbi.com",
    "arabnews.com",
    "khaleejtimes.com",
    "thenationalnews.com",
    "pharmaboardroom.com",
    "forbesmiddleeast.com",
    "tvmcapitalhealthcare.com",
    "swfinstitute.org",
    "ebrd.com",
    "vccircle.com",
)

MIDDLE_EAST_HEALTHCARE_ENTITIES = (
    "PIF",
    "Lifera",
    "ADQ",
    "Arcera",
    "Mubadala",
    "M42",
    "PureHealth",
    "QIA",
    "Qatar Investment Authority",
    "Emirates Investment Authority",
    "Amanat Holdings",
    "Investcorp",
    "TVM Capital Healthcare",
    "Gulf Capital",
    "Jadwa Investment",
    "Waha Capital",
    "aMoon",
    "OrbiMed",
    "Julphar",
    "Gulf Pharmaceutical Industries",
    "Hikma",
    "SPIMACO",
    "Jamjoom Pharma",
    "Tabuk Pharmaceuticals",
    "Globalpharma",
    "Pharmax",
    "CinnaGen",
    "SaudiBio",
    "Arabio",
    "Tamer Group",
    "Saja Pharmaceuticals",
    "Cigalah",
    "Avalon Pharma",
    "Nahdi Medical",
    "Altibbi",
    "Vezeeta",
    "PureLab",
    "SEHA",
    "Daman",
    "Aster DM Healthcare",
    "Dr. Sulaiman Al Habib",
    "HMG",
    "Burjeel Holdings",
    "NMC Healthcare",
    "Fakeeh Care",
    "Mouwasat",
    "Mediclinic Middle East",
    "Dallah Healthcare",
    "Saudi German Health",
    "Emirates Drug Establishment",
    "SFDA",
    "Dubai Health Authority",
    "Department of Health Abu Dhabi",
    "Saudi Ministry of Health",
)

MIDDLE_EAST_SOURCE_QUERIES = tuple(
    f"site:{source} Middle East pharma healthcare deal investment"
    for source in MIDDLE_EAST_PRIORITY_SOURCES[:9]
)

MIDDLE_EAST_ENTITY_QUERIES = tuple(
    f'"{entity}" pharma OR healthcare OR biopharma OR hospital OR acquisition OR partnership'
    for entity in MIDDLE_EAST_HEALTHCARE_ENTITIES[:28]
)


NEWS_MODULES: tuple[NewsModule, ...] = (
    NewsModule(
        key="global_news",
        label="Global News",
        group="Global",
        subgroup="Politics, wars, finance, policy, and trending issues",
        description="Global politics, wars, finance, policy, energy, trade, and major trending stories.",
        queries=(
            'global politics war finance policy trending news',
            'geopolitics conflict sanctions markets central bank policy',
            'world news energy trade economy inflation policy',
        ),
        include_terms=GLOBAL_NEWS_TERMS,
        priority_sources=GLOBAL_PRIORITY_SOURCES,
    ),
    NewsModule(
        key="india_news",
        label="India News",
        group="India",
        subgroup="National, Andhra, Telangana, finance, policy, and trending issues",
        description="India national politics, finance, policy, markets, and state-level Andhra Pradesh and Telangana coverage.",
        queries=(
            'India politics finance policy markets trending news',
            'Andhra Pradesh politics policy investment finance news',
            'Telangana politics Hyderabad policy investment finance news',
        ),
        include_terms=INDIA_TERMS,
        priority_sources=INDIA_PRIORITY_SOURCES,
    ),
    NewsModule(
        key="global_pharma",
        label="Global Pharma",
        group="Pharma",
        subgroup="Global approvals, deals, and regulations",
        description="M&A, licensing, partnerships, investments, and strategic transactions in pharma and biotech.",
        queries=(
            'global pharma approvals deals regulations FDA EMA',
            'pharma acquisition merger licensing partnership regulation',
            'biotech clinical trial approval deal collaboration',
        ),
        include_terms=PHARMA_TERMS + DEAL_TERMS + INNOVATION_TERMS,
        required_terms=HEALTHCARE_TOPIC_TERMS,
        priority_sources=PHARMA_PRIORITY_SOURCES,
    ),
    NewsModule(
        key="middle_east_pharma",
        label="Middle East Pharma",
        group="Pharma",
        subgroup="Middle East approvals, deals, and regulations",
        description="Transactions, partnerships, investments, and expansion moves across MENA pharma and healthcare.",
        queries=(
            'Middle East pharma approvals deals regulations',
            'UAE Saudi Qatar pharma healthcare investment acquisition partnership',
            'MENA pharmaceutical regulation hospital medtech deal joint venture',
            'GCC healthcare private equity pharma sovereign wealth fund',
            'Saudi pharma localization Lifera SFDA biologics CDMO',
            'UAE healthcare pharma ADQ Arcera PureHealth M42 Mubadala',
            'Middle East hospital operator acquisition investment IPO healthcare',
        )
        + MIDDLE_EAST_SOURCE_QUERIES
        + MIDDLE_EAST_ENTITY_QUERIES,
        include_terms=PHARMA_TERMS + DEAL_TERMS + INNOVATION_TERMS + MIDDLE_EAST_TERMS,
        required_terms=HEALTHCARE_TOPIC_TERMS,
        priority_sources=MIDDLE_EAST_PRIORITY_SOURCES,
        watch_entities=MIDDLE_EAST_HEALTHCARE_ENTITIES,
    ),
)


DEFAULT_SOURCES = (
    "Google News RSS",
)
