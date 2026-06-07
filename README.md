# price-of-thinking-indicators

Live, falsifiable indicators of whether the AI investment boom is being
financed in a way that can absorb disappointment. Companion to chapter 9 of
[*The Price of Thinking*](https://priceofthinking.com/chapters/the-boom/)
(Allan Pedersen, 2026).

**Dashboard:** https://allangiraf-hub.github.io/price-of-thinking-indicators/
(auto-refreshed weekly by GitHub Actions; every number traceable to a
public primary source).

## The four indicators

| # | Indicator | Question it answers | Falsification condition | Source |
|---|-----------|--------------------|------------------------|--------|
| 1 | Capex vs AI revenue | Is the ~6:1 gap narrowing from the revenue side? | Ratio keeps widening while revenue growth stalls | SEC EDGAR XBRL (capex); curated, cited revenue estimates |
| 2 | Depreciation realism | Are assumed server lives shortening toward the sceptics' 2–3 years? | Disclosed lives lengthen or hold as chip cycles speed up | Useful-life sentences extracted from latest 10-Ks (sentence + URL kept as evidence) |
| 3 | Financing mix | Cash flow or debt? | Capex stays comfortably inside operating cash flow; debt issuance flat | SEC EDGAR XBRL: capex, operating cash flow, debt issuance |
| 4 | GPU spot prices | First hard evidence of overcapacity | Rental prices stable or rising | vast.ai public marketplace, weekly snapshots |

Two FRED context series (information-processing investment, communication
construction) frame the macro picture.

## Method notes

- **No API keys.** EDGAR requires only a User-Agent header; FRED is read via
  the public `fredgraph.csv` endpoint; vast.ai's marketplace is public.
- **Cash-flow XBRL values are year-to-date**; quarterly figures are derived
  by differencing within the fiscal year (`edgar.quarterly_values`).
- **Companies differ in tagging** (Amazon books capex under
  `PaymentsToAcquireProductiveAssets`); tags are tried in fallback order.
- **Extraction is evidence-preserving:** the depreciation table stores the
  verbatim sentence and filing URL for every value, so nothing rests on
  the parser's judgment alone.
- Curated inputs (`data/curated/`) carry a source column and are
  deliberately small: AI revenue has no single official series, and private
  credit deals are not all in public filings. Honest curation beats false
  automation.

## Run it

```bash
pip install -e .
python -m potindicators.cli all        # full refresh
python -m potindicators.cli gpu        # one indicator
pytest                                  # tests
```

## Licence

MIT. Data remain the property of their sources (SEC, FRED, vast.ai).
