from __future__ import annotations

from datetime import datetime
from io import BytesIO

import pandas as pd
import streamlit as st

from news_config import NEWS_MODULES
from scraper import fetch_modules_with_lookbacks, module_to_dict
from summarizer import summarize_section


st.set_page_config(
    page_title="Daily News Intelligence",
    page_icon="",
    layout="wide",
)


GROUP_ORDER = ["Global", "India", "Pharma"]


@st.cache_data(ttl=1800, show_spinner=False)
def cached_fetch_all(
    selected_module_keys: tuple[str, ...],
    lookback_items: tuple[tuple[str, int], ...],
    max_items_per_query: int,
    fetch_excerpts: bool,
) -> pd.DataFrame:
    selected_modules = [module for module in NEWS_MODULES if module.key in selected_module_keys]
    return fetch_modules_with_lookbacks(
        selected_modules,
        dict(lookback_items),
        max_items_per_query,
        fetch_excerpts,
    )


def dataframe_to_excel(frame: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        frame.to_excel(writer, sheet_name="news", index=False)
    return output.getvalue()


def module_map() -> dict[str, list]:
    grouped: dict[str, list] = {}
    for module in NEWS_MODULES:
        grouped.setdefault(module.group, []).append(module)
    return grouped


def render_summary_card(summary: dict[str, object]) -> None:
    with st.container(border=True):
        st.subheader(str(summary.get("headline") or summary["section"]))
        if summary.get("source_confidence"):
            st.caption(str(summary["source_confidence"]))
        st.write(str(summary["overview"]))
        if summary["bullets"]:
            st.markdown("**Top developments**")
            for bullet in summary["bullets"]:
                st.markdown(f"- {bullet}")
        priority_sources = summary.get("priority_sources") or []
        if priority_sources:
            st.caption("Priority sources: " + ", ".join(priority_sources[:5]))
        watch_entities = summary.get("watch_entities") or []
        if watch_entities:
            st.caption("Active entities: " + ", ".join(watch_entities[:8]))
        watch_terms = summary.get("watch_terms") or []
        if watch_terms:
            st.caption("Watch terms: " + ", ".join(watch_terms[:8]))


def render_article(row: pd.Series, fetch_excerpts: bool) -> None:
    with st.container(border=True):
        top = st.columns([5, 1], vertical_alignment="top")
        with top[0]:
            st.markdown(f"#### {row['title']}")
            st.caption(
                f"{row['group']} / {row['module']} | {row['source']} | "
                f"{row['published']} | Relevance: {row['relevance']}"
            )
            if row.get("matched_entities"):
                st.caption(f"Matched entities: {row['matched_entities']}")
        with top[1]:
            st.link_button("Open", row["url"], width="stretch")
        if row.get("summary"):
            st.write(row["summary"])
        if fetch_excerpts and row.get("excerpt"):
            with st.expander("Extracted excerpt"):
                st.write(row["excerpt"])


st.markdown(
    """
    <style>
    .block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
    h1 {line-height: 1.1;}
    h3, h4 {line-height: 1.25;}
    div[data-testid="stMetric"] {
        background: #f4f7f7;
        border: 1px solid #dfe8e6;
        border-radius: 8px;
        padding: 12px 14px;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #dfe8e6;
        border-radius: 8px;
    }
    .section-eyebrow {
        color: #0a7c72;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0;
        text-transform: uppercase;
    }
    @media (max-width: 760px) {
        .block-container {padding-left: 0.85rem; padding-right: 0.85rem; padding-top: 1rem;}
        div[data-testid="stHorizontalBlock"] {gap: 0.6rem;}
        div[data-testid="stMetric"] {padding: 10px 11px;}
        h1 {font-size: 1.75rem;}
        h3 {font-size: 1.18rem;}
        h4 {font-size: 1rem;}
        div[data-testid="stButton"] button,
        div[data-testid="stDownloadButton"] button,
        a[data-testid="stLinkButton"] {min-height: 42px;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Daily News Intelligence")
st.caption("Free-source monitoring for global events, India coverage, and pharma/healthcare developments.")

grouped_modules = module_map()

with st.sidebar:
    st.header("Refresh controls")
    selected_keys: list[str] = []
    lookback_by_group: dict[str, int] = {}
    for group in GROUP_ORDER:
        modules = grouped_modules.get(group, [])
        if not modules:
            continue
        st.markdown(f"**{group}**")
        default_window = 14 if group in {"Global", "India"} else 30
        lookback_by_group[group] = st.slider(
            f"{group} lookback",
            min_value=1,
            max_value=365,
            value=default_window,
            key=f"lookback_{group}",
        )
        for module in modules:
            checked = st.checkbox(
                module.label,
                value=True,
                key=f"module_{module.key}",
                help=module.subgroup,
            )
            if checked:
                selected_keys.append(module.key)

    st.divider()
    max_items_per_query = st.slider("Items per query", min_value=5, max_value=100, value=25, step=5)
    summary_items = st.slider("Summary depth", min_value=3, max_value=8, value=5)
    fetch_excerpts = st.toggle(
        "Fetch article excerpts",
        value=False,
        help="Slower. Attempts direct page extraction only where publishers allow it.",
    )

    load_news = st.button("Load / Refresh news", type="primary", width="stretch")
    if load_news:
        st.cache_data.clear()

    st.divider()
    st.caption("New modules can be added in news_config.py without changing the UI.")

if not selected_keys:
    st.warning("Select at least one module.")
    st.stop()

settings = (
    tuple(selected_keys),
    tuple(sorted(lookback_by_group.items())),
    max_items_per_query,
    fetch_excerpts,
)

if "news_data" not in st.session_state:
    st.session_state.news_data = None
    st.session_state.news_settings = None

if load_news:
    with st.spinner("Pulling free-source news feeds..."):
        st.session_state.news_data = cached_fetch_all(*settings)
        st.session_state.news_settings = settings

if st.session_state.news_data is None:
    st.info("Choose your modules and lookback windows, then tap Load / Refresh news to fetch the latest free-source articles.")
    preview_cols = st.columns(3)
    for index, group in enumerate(GROUP_ORDER):
        with preview_cols[index % 3]:
            with st.container(border=True):
                st.subheader(group)
                modules = grouped_modules.get(group, [])
                for module in modules:
                    st.caption(f"{module.label}: {module.subgroup}")
    st.stop()

news = st.session_state.news_data

if news.empty:
    st.info("No news found for the selected modules and filters. Try increasing the lookback window.")
    st.stop()

left_filter, middle_filter, right_filter = st.columns([2, 1, 1], vertical_alignment="bottom")
with left_filter:
    query = st.text_input("Search", placeholder="Company, country, policy, approval, acquisition...")
with middle_filter:
    selected_group = st.selectbox("Section", options=["All"] + GROUP_ORDER)
with right_filter:
    relevance_filter = st.selectbox("Relevance", options=["All", "High", "Medium", "Low"])

filtered = news.copy()
if query:
    q = query.lower()
    searchable_columns = [
        "title",
        "summary",
        "source",
        "domain",
        "group",
        "module",
        "subgroup",
        "matched_entities",
        "query",
        "excerpt",
    ]
    filtered = filtered[
        filtered[searchable_columns]
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
        .str.contains(q, regex=False)
    ]

if selected_group != "All":
    filtered = filtered[filtered["group"] == selected_group]

if relevance_filter != "All":
    filtered = filtered[filtered["relevance"] == relevance_filter]

filtered = filtered.sort_values(
    ["relevance_score", "published_utc"],
    ascending=[False, False],
    na_position="last",
)
summary_frame = filtered[filtered["relevance"] != "Low"]
if summary_frame.empty:
    summary_frame = filtered

metric_cols = st.columns(5)
metric_cols[0].metric("Articles", len(filtered))
metric_cols[1].metric("Sources", filtered["source"].nunique())
metric_cols[2].metric("Sections", filtered["group"].nunique())
metric_cols[3].metric("Modules", filtered["module"].nunique())
metric_cols[4].metric("Last refresh", datetime.now().strftime("%H:%M"))

download_columns = [
    "group",
    "module",
    "subgroup",
    "title",
    "source",
    "published",
    "relevance",
    "matched_entities",
    "priority_source",
    "summary",
    "excerpt",
    "url",
    "query",
]
download_frame = filtered[download_columns].copy()

download_col1, download_col2 = st.columns([1, 1])
with download_col1:
    st.download_button(
        "Download CSV",
        data=download_frame.to_csv(index=False).encode("utf-8-sig"),
        file_name="daily_news_intelligence.csv",
        mime="text/csv",
        width="stretch",
    )
with download_col2:
    st.download_button(
        "Download Excel",
        data=dataframe_to_excel(download_frame),
        file_name="daily_news_intelligence.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

tabs = st.tabs(["Executive Summary", "Section Streams", "Source View", "Module Config"])

with tabs[0]:
    st.markdown('<div class="section-eyebrow">Native extractive summary</div>', unsafe_allow_html=True)
    st.write("Summaries are generated from titles, snippets, source frequency, freshness, and relevance scores.")

    group_summaries = [
        summarize_section(section_frame, str(section), limit=summary_items)
        for section, section_frame in summary_frame.groupby("group", sort=False)
    ]
    summary_cols = st.columns(3)
    for index, summary in enumerate(group_summaries):
        with summary_cols[index % 3]:
            render_summary_card(summary)

    st.divider()
    st.subheader("Module Summaries")
    module_summaries = [
        summarize_section(section_frame, str(section), limit=summary_items)
        for section, section_frame in summary_frame.groupby("module", sort=False)
    ]
    for summary in module_summaries:
        render_summary_card(summary)

with tabs[1]:
    for group in GROUP_ORDER:
        group_frame = filtered[filtered["group"] == group]
        if group_frame.empty:
            continue
        st.markdown(f"### {group}")
        group_summary_frame = summary_frame[summary_frame["group"] == group]
        render_summary_card(
            summarize_section(
                group_summary_frame if not group_summary_frame.empty else group_frame,
                group,
                limit=summary_items,
            )
        )

        modules = [module for module in NEWS_MODULES if module.group == group and module.key in selected_keys]
        if len(modules) > 1:
            module_tabs = st.tabs([module.label for module in modules])
            for module_tab, module in zip(module_tabs, modules):
                with module_tab:
                    module_frame = group_frame[group_frame["module_key"] == module.key]
                    st.caption(module.subgroup)
                    for _, row in module_frame.head(20).iterrows():
                        render_article(row, fetch_excerpts)
        else:
            for _, row in group_frame.head(25).iterrows():
                render_article(row, fetch_excerpts)

with tabs[2]:
    source_counts = (
        filtered.groupby(["group", "module", "source"])
        .size()
        .reset_index(name="articles")
        .sort_values("articles", ascending=False)
    )
    st.dataframe(source_counts, width="stretch", hide_index=True)

with tabs[3]:
    st.write("Current modules are plain Python config objects, so new categories can be added without changing the Streamlit UI.")
    st.json([module_to_dict(module) for module in NEWS_MODULES])
