"""Free-source news discovery and lightweight article extraction."""

from __future__ import annotations

import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Iterable
from urllib.parse import quote_plus, urlparse

import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from news_config import NewsModule


GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
)


def build_rss_url(query: str, days_back: int) -> str:
    if days_back <= 31:
        dated_query = f"{query} when:{days_back}d"
    else:
        start_date = (datetime.now(timezone.utc) - timedelta(days=days_back)).date().isoformat()
        dated_query = f"{query} after:{start_date}"
    return GOOGLE_NEWS_RSS.format(query=quote_plus(dated_query))


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = date_parser.parse(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", BeautifulSoup(value, "html.parser").get_text(" ")).strip()


def result_id(title: str, link: str) -> str:
    return hashlib.sha256(f"{title}|{link}".encode("utf-8")).hexdigest()[:16]


def domain_from_url(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc.removeprefix("www.")


def term_score(text: str, terms: Iterable[str]) -> int:
    lowered = text.lower()
    return sum(1 for term in terms if term.lower() in lowered)


def matched_terms(text: str, terms: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [term for term in terms if term.lower() in lowered]


def source_score(domain: str, source: str, module: NewsModule) -> int:
    source_text = re.sub(r"[^a-z0-9]+", "", f"{domain} {source}".lower())
    score = 0
    for priority_source in module.priority_sources:
        normalized = priority_source.lower().removeprefix("www.")
        root = normalized.split(".", 1)[0]
        normalized_key = re.sub(r"[^a-z0-9]+", "", normalized)
        root_key = re.sub(r"[^a-z0-9]+", "", root)
        if normalized_key in source_text or root_key in source_text:
            score += 1
    return score


def classify_relevance(text: str, module: NewsModule, domain: str = "", source: str = "") -> tuple[str, int]:
    includes = term_score(text, module.include_terms)
    excludes = term_score(text, module.exclude_terms)
    required_hits = term_score(text, module.required_terms)
    entity_hits = len(matched_terms(text, module.watch_entities))
    priority_source_hits = source_score(domain, source, module)
    score = max(0, includes + (entity_hits * 2) + (priority_source_hits * 2) - excludes)
    if module.required_terms and required_hits == 0:
        score = min(score, 2)
    if score >= 6:
        label = "High"
    elif score >= 3:
        label = "Medium"
    else:
        label = "Low"
    return label, score


def fetch_article_excerpt(url: str, timeout: int = 8) -> str:
    """Best-effort extraction for pages that allow direct access."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException:
        return ""

    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        tag.decompose()

    paragraphs = [
        normalize_text(p.get_text(" "))
        for p in soup.find_all("p")
        if len(normalize_text(p.get_text(" "))) > 60
    ]
    excerpt = " ".join(paragraphs[:4])
    return excerpt[:1200]


def fetch_module_news(
    module: NewsModule,
    days_back: int = 7,
    max_items_per_query: int = 25,
    fetch_excerpts: bool = False,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    def fetch_query_entries(query: str) -> list[tuple[str, object]]:
        rss_url = build_rss_url(query, days_back)
        try:
            response = requests.get(rss_url, headers={"User-Agent": USER_AGENT}, timeout=12)
            response.raise_for_status()
        except requests.RequestException:
            return []
        feed = feedparser.parse(response.content)
        return [(query, entry) for entry in feed.entries[:max_items_per_query]]

    max_workers = min(12, max(1, len(module.queries)))
    query_entries: list[tuple[str, object]] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_query_entries, query) for query in module.queries]
        for future in as_completed(futures):
            query_entries.extend(future.result())

    for query, entry in query_entries:
        title = normalize_text(entry.get("title"))
        link = entry.get("link", "")
        summary = normalize_text(entry.get("summary"))
        published = parse_datetime(entry.get("published"))
        source = normalize_text(entry.get("source", {}).get("title") if entry.get("source") else "")
        excerpt = fetch_article_excerpt(link) if fetch_excerpts and link else ""
        combined_text = " ".join([title, summary, excerpt, source])
        domain = domain_from_url(link)
        entities = matched_terms(combined_text, module.watch_entities)
        priority_source = source_score(domain, source, module) > 0
        relevance, score = classify_relevance(combined_text, module, domain, source)

        rows.append(
            {
                "id": result_id(title, link),
                "module_key": module.key,
                "module": module.label,
                "group": module.group,
                "subgroup": module.subgroup,
                "query": query,
                "title": title,
                "source": source or domain_from_url(link),
                "domain": domain,
                "published_utc": published,
                "published": published.strftime("%Y-%m-%d %H:%M UTC") if published else "",
                "summary": summary,
                "excerpt": excerpt,
                "relevance": relevance,
                "relevance_score": score,
                "matched_entities": ", ".join(entities[:10]),
                "priority_source": priority_source,
                "url": link,
            }
        )

    if not rows:
        return pd.DataFrame()

    frame = pd.DataFrame(rows)
    frame = frame.drop_duplicates(subset=["id"]).sort_values(
        by=["published_utc", "relevance_score"],
        ascending=[False, False],
        na_position="last",
    )
    return frame.reset_index(drop=True)


def fetch_all_modules(
    modules: Iterable[NewsModule],
    days_back: int = 7,
    max_items_per_query: int = 25,
    fetch_excerpts: bool = False,
) -> pd.DataFrame:
    frames = [
        fetch_module_news(module, days_back, max_items_per_query, fetch_excerpts)
        for module in modules
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["module_key", "id"])


def fetch_modules_with_lookbacks(
    modules: Iterable[NewsModule],
    lookback_by_group: dict[str, int],
    max_items_per_query: int = 25,
    fetch_excerpts: bool = False,
) -> pd.DataFrame:
    frames = [
        fetch_module_news(
            module,
            days_back=lookback_by_group.get(module.group, 30),
            max_items_per_query=max_items_per_query,
            fetch_excerpts=fetch_excerpts,
        )
        for module in modules
    ]
    frames = [frame for frame in frames if not frame.empty]
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["module_key", "id"])


def module_to_dict(module: NewsModule) -> dict[str, object]:
    return asdict(module)
