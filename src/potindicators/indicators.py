"""Compute the four chapter-9 indicators into tidy frames.

Each indicator states its falsification condition — the observation that
would tell against the 'this boom is financeable' thesis.
"""
from __future__ import annotations

import pandas as pd

from . import edgar
from .config import COMPANIES, CURATED, TAG_CAPEX, TAG_DEBT_ISSUED, TAG_OCF


def hyperscaler_annual(tags: list[str]) -> pd.DataFrame:
    """Annual values per company for the first tag that has data."""
    frames = []
    for ticker, cik in COMPANIES.items():
        raw = edgar.concept_with_fallback(cik, tags)
        if raw.empty:
            continue
        ann = edgar.annual_values(raw)
        ann["ticker"] = ticker
        frames.append(ann)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def capex_vs_revenue() -> pd.DataFrame:
    """Indicator 1 — falsified if the capex/AI-revenue ratio keeps widening
    while revenue growth stalls."""
    capex = hyperscaler_annual(TAG_CAPEX)
    capex["year"] = capex["period_end"].dt.year
    total = capex.groupby("year")["usd"].sum().div(1e9).rename("capex_usd_bn").reset_index()
    revenue = pd.read_csv(CURATED / "ai_revenue_estimates.csv")
    out = total.merge(revenue[["year", "ai_revenue_usd_bn"]], on="year", how="left")
    out["capex_to_revenue"] = out["capex_usd_bn"] / out["ai_revenue_usd_bn"]
    return out


def financing_mix() -> pd.DataFrame:
    """Indicator 3 — falsified if capex stays comfortably inside operating
    cash flow and debt issuance stays flat."""
    capex = hyperscaler_annual(TAG_CAPEX).rename(columns={"usd": "capex"})
    ocf = hyperscaler_annual(TAG_OCF).rename(columns={"usd": "ocf"})
    debt = hyperscaler_annual(TAG_DEBT_ISSUED).rename(columns={"usd": "debt_issued"})
    out = capex.merge(ocf, on=["ticker", "period_end"], how="inner")
    out = out.merge(debt, on=["ticker", "period_end"], how="left")
    out["capex_to_ocf"] = out["capex"] / out["ocf"]
    out["year"] = out["period_end"].dt.year
    return out


def depreciation_table() -> pd.DataFrame:
    """Indicator 2 — falsified (for the sceptics) if disclosed server lives
    lengthen or hold as chips cycle faster."""
    from . import depreciation

    return depreciation.run()


def gpu_prices() -> pd.DataFrame:
    """Indicator 4 — falling spot rental prices are the first hard evidence
    of overcapacity."""
    from . import gpu

    return gpu.snapshot()
