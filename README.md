# Daily News Intelligence

Streamlit dashboard for free-source discovery of global, India, and pharma/healthcare news intelligence.

## What it tracks

- Global news including politics, wars, finance, policy, energy, trade, and trending events
- India news including national politics, finance, policy, markets, Andhra Pradesh, and Telangana
- Global pharma including approvals, deals, regulations, trials, and partnerships
- Middle East pharma and healthcare including approvals, deals, regulations, and investments
- Future modules through `news_config.py`

## Dashboard controls

- Set separate lookback windows for Global, India, and Pharma, up to 365 days each.
- Adjust items per query to trade off speed versus coverage.
- Adjust summary depth to show more or fewer top developments in each brief.
- Use CSV or Excel download for the filtered result set.

## Middle East pharma intelligence layer

The Middle East Pharma module includes curated source and entity watchlists so searches are not limited to generic keywords. It tracks sources such as Zawya, Gulf Business, AGBI, Arab News, The National, PharmaBoardroom, Forbes Middle East, TVM Capital Healthcare, SWFI, EBRD, VC Circle, Reuters, FT, and Bloomberg through Google News RSS where available.

It also watches sovereign platforms, investors, manufacturers, and operators including PIF/Lifera, ADQ/Arcera, Mubadala, M42, PureHealth, QIA, TVM Capital Healthcare, Gulf Capital, Jadwa, Waha Capital, Julphar, Hikma, SPIMACO, Jamjoom Pharma, Tabuk Pharmaceuticals, Globalpharma, Pharmax, SaudiBio, Tamer Group, Aster DM Healthcare, Burjeel, NMC Healthcare, Fakeeh Care, Mouwasat, and other regional healthcare entities.

## Summarization

The dashboard includes a native extractive summarization engine in `summarizer.py`. It does not call a paid model or API. It ranks headlines by relevance, freshness, priority-source coverage, and watched-entity matches, then creates summaries by section and module.

Each brief includes a headline, dominant signal type, source-confidence note, top developments, active entities, priority sources, and watch terms.

## Data sources

The first version uses Google News RSS search as a free discovery layer. It does not require paid APIs or API keys. Optional article excerpt extraction is best-effort and only works for publisher pages that allow direct access.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

## Add another module

Edit `news_config.py` and add another `NewsModule` entry:

```python
NewsModule(
    key="digital_health",
    label="Digital Health",
    group="Pharma",
    subgroup="Digital health funding, partnerships, and regulations",
    description="Funding, M&A, regulation, and partnerships in digital health.",
    queries=(
        "digital health acquisition OR funding OR partnership",
        "healthtech deal OR investment OR merger",
    ),
    include_terms=("digital health", "healthtech", "acquisition", "funding", "partnership"),
)
```

The dashboard will automatically show it in the module selector.

## Notes

- This is a scraping/discovery workflow, so results depend on public indexing and publisher availability.
- Respect publisher terms of service and robots policies if expanding beyond RSS discovery.
- Use the relevance label as a triage aid, not a perfect classifier.
