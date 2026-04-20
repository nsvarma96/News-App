"""Native extractive summaries for scraped news sections."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd


STOPWORDS = {
    "about",
    "after",
    "against",
    "amid",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "how",
    "in",
    "into",
    "its",
    "new",
    "news",
    "of",
    "on",
    "or",
    "over",
    "says",
    "the",
    "to",
    "under",
    "with",
}

DEAL_WORDS = ("deal", "acquisition", "merger", "investment", "funding", "partnership", "joint venture", "ipo")
POLICY_WORDS = ("policy", "regulation", "approval", "approved", "ministry", "central bank", "government", "sanction")
RISK_WORDS = ("war", "conflict", "crisis", "probe", "recall", "lawsuit", "sanction", "tariff", "shortage")


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text.lower())
        if token not in STOPWORDS
    ]


def clean_sentence(text: object, max_length: int = 240) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rsplit(" ", 1)[0] + "..."


def combined_text(frame: pd.DataFrame) -> str:
    columns = [column for column in ["title", "summary", "matched_entities"] if column in frame]
    if not columns:
        return ""
    return " ".join(frame[columns].fillna("").astype(str).agg(" ".join, axis=1))


def top_terms(frame: pd.DataFrame, limit: int = 8) -> list[str]:
    counts = Counter(tokenize(combined_text(frame)))
    return [term for term, _ in counts.most_common(limit)]


def top_entities(frame: pd.DataFrame, limit: int = 8) -> list[str]:
    if "matched_entities" not in frame:
        return []
    entities: list[str] = []
    for value in frame["matched_entities"].dropna().astype(str):
        entities.extend([item.strip() for item in value.split(",") if item.strip()])
    counts = Counter(entities)
    return [entity for entity, _ in counts.most_common(limit)]


def top_priority_sources(frame: pd.DataFrame, limit: int = 5) -> list[str]:
    if "priority_source" not in frame:
        return []
    priority_frame = frame[frame["priority_source"] == True]  # noqa: E712
    if priority_frame.empty:
        return []
    return priority_frame["source"].dropna().value_counts().head(limit).index.tolist()


def count_word_hits(text: str, words: tuple[str, ...]) -> int:
    lowered = text.lower()
    return sum(lowered.count(word) for word in words)


def signal_mix(frame: pd.DataFrame) -> dict[str, int]:
    text = combined_text(frame)
    return {
        "Deals": count_word_hits(text, DEAL_WORDS),
        "Policy": count_word_hits(text, POLICY_WORDS),
        "Risks": count_word_hits(text, RISK_WORDS),
    }


def dominant_signal(frame: pd.DataFrame) -> str:
    mix = signal_mix(frame)
    if not any(mix.values()):
        return "General monitoring"
    label, count = max(mix.items(), key=lambda item: item[1])
    return f"{label} led the section signal ({count} mentions)"


def ranked_headlines(frame: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    if frame.empty:
        return frame
    ranked = frame.copy()
    ranked["summary_rank"] = ranked["relevance_score"].fillna(0).astype(float)
    if "priority_source" in ranked:
        ranked["summary_rank"] += ranked["priority_source"].fillna(False).astype(int) * 2
    if "matched_entities" in ranked:
        ranked["summary_rank"] += ranked["matched_entities"].fillna("").astype(str).str.len().gt(0).astype(int)
    if "published_utc" in ranked:
        ranked["summary_rank"] += ranked["published_utc"].notna().astype(int)
    return ranked.sort_values(["summary_rank", "published_utc"], ascending=[False, False]).head(limit)


def source_confidence(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "No source signal"
    priority_count = int(frame.get("priority_source", pd.Series(dtype=bool)).fillna(False).sum())
    source_count = frame["source"].nunique() if "source" in frame else 0
    if priority_count >= 5:
        return f"Strong source quality: {priority_count} priority-source items across {source_count} sources"
    if priority_count:
        return f"Moderate source quality: {priority_count} priority-source items across {source_count} sources"
    return f"Exploratory source quality: no priority-source hits across {source_count} sources"


def make_headline(section_name: str, frame: pd.DataFrame, entities: list[str], terms: list[str]) -> str:
    if entities:
        return f"{section_name}: activity clusters around {', '.join(entities[:3])}"
    if terms:
        return f"{section_name}: main themes are {', '.join(terms[:3])}"
    return f"{section_name}: limited signal in this pull"


def summarize_section(frame: pd.DataFrame, section_name: str, limit: int = 5) -> dict[str, object]:
    if frame.empty:
        return {
            "section": section_name,
            "headline": f"{section_name}: no articles available",
            "overview": "No articles available for this section.",
            "signal": "No signal",
            "bullets": [],
            "watch_terms": [],
            "watch_entities": [],
            "priority_sources": [],
            "source_confidence": "No source signal",
        }

    terms = top_terms(frame)
    entities = top_entities(frame)
    top_sources = frame["source"].dropna().value_counts().head(4).index.tolist()
    priority_sources = top_priority_sources(frame)
    signal = dominant_signal(frame)
    confidence = source_confidence(frame)
    bullets = []

    for _, row in ranked_headlines(frame, limit=limit).iterrows():
        summary = clean_sentence(row.get("summary"))
        title = clean_sentence(row.get("title"), max_length=170)
        source = row.get("source") or "Unknown source"
        entity_context = row.get("matched_entities")
        published = row.get("published")
        prefix = f"{title} ({source}"
        if published:
            prefix += f", {published}"
        prefix += ")"
        if entity_context:
            prefix += f" | Entities: {entity_context}"
        bullets.append(f"{prefix}: {summary}" if summary else prefix)

    overview = (
        f"{len(frame)} articles from {frame['source'].nunique()} sources. "
        f"{signal}. "
        f"Top sources: {', '.join(top_sources) or 'not available'}."
    )
    if entities:
        overview += f" Active entities: {', '.join(entities[:6])}."
    if terms:
        overview += f" Watch terms: {', '.join(terms[:6])}."

    return {
        "section": section_name,
        "headline": make_headline(section_name, frame, entities, terms),
        "overview": overview,
        "signal": signal,
        "bullets": bullets,
        "watch_terms": terms,
        "watch_entities": entities,
        "priority_sources": priority_sources,
        "source_confidence": confidence,
    }


def summarize_by_section(frame: pd.DataFrame, section_column: str = "module") -> list[dict[str, object]]:
    if frame.empty or section_column not in frame:
        return []
    summaries = []
    for section, section_frame in frame.groupby(section_column, sort=False):
        summaries.append(summarize_section(section_frame, str(section)))
    return summaries
