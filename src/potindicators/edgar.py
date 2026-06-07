"""SEC EDGAR fetchers: XBRL company facts and 10-K documents. No API key needed."""
from __future__ import annotations

import re
import time

import pandas as pd
import requests

from .config import COMPANIES, EDGAR_USER_AGENT

HEADERS = {"User-Agent": EDGAR_USER_AGENT, "Accept-Encoding": "gzip, deflate"}
_PAUSE = 0.15  # stay well under SEC's 10 req/s fair-access limit


def _get(url: str) -> requests.Response:
    time.sleep(_PAUSE)
    r = requests.get(url, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r


def company_concept(cik: int, tag: str) -> pd.DataFrame:
    """All reported USD values for one XBRL tag for one company."""
    url = (
        f"https://data.sec.gov/api/xbrl/companyconcept/"
        f"CIK{cik:010d}/us-gaap/{tag}.json"
    )
    data = _get(url).json()
    rows = data.get("units", {}).get("USD", [])
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for col in ("start", "end", "filed"):
        if col in df:
            df[col] = pd.to_datetime(df[col])
    return df


def concept_with_fallback(cik: int, tags: list[str]) -> pd.DataFrame:
    """Fetch every tag that yields data and merge.

    Companies switch tags over time (Amazon moved capex from
    PaymentsToAcquirePropertyPlantAndEquipment to
    PaymentsToAcquireProductiveAssets in 2017), so first-hit is not enough.
    Where the same period is reported under two tags, the larger value is
    kept (the broader concept).
    """
    frames = []
    for tag in tags:
        try:
            df = company_concept(cik, tag)
        except requests.HTTPError:
            continue
        if not df.empty:
            df["tag"] = tag
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    merged = pd.concat(frames, ignore_index=True)
    merged = merged.sort_values("val").drop_duplicates(["start", "end", "form"], keep="last")
    return merged.sort_values("end")


def annual_values(df: pd.DataFrame) -> pd.DataFrame:
    """Reduce a company-concept frame to one value per fiscal year.

    Candidates are full-year 'frame' entries (CY2024 etc.) and 10-K rows
    spanning ~a year; per fiscal-year end we keep the latest-filed row, so
    calendar and non-calendar fiscal years (MSFT ends June) both work.
    """
    if df.empty:
        return df
    frame_col = df.get("frame", pd.Series(index=df.index, dtype=object))
    frames = df[frame_col.astype(str).str.fullmatch(r"CY\d{4}")]
    spans = df[(df["end"] - df["start"]).dt.days > 300]
    tenk = spans[spans["form"].astype(str).str.startswith("10-K")]
    out = pd.concat([frames, tenk], ignore_index=True)
    out = out.sort_values("filed").drop_duplicates("end", keep="last")
    out = out.sort_values("end")
    return out[["end", "val"]].rename(columns={"end": "period_end", "val": "usd"})


def quarterly_values(df: pd.DataFrame) -> pd.DataFrame:
    """Derive true quarterly values from YTD cash-flow figures.

    Cash-flow XBRL values are year-to-date; within each fiscal year we
    difference successive YTD values to recover individual quarters.
    """
    if df.empty:
        return df
    d = df[df["form"].isin(["10-K", "10-Q"])].copy()
    d = d[(d["end"] - d["start"]).dt.days < 400]
    d = d.sort_values("filed").drop_duplicates(["start", "end"], keep="last")
    d = d.sort_values("end")
    rows = []
    for fy_start, grp in d.groupby("start"):
        grp = grp.sort_values("end")
        prev = 0.0
        for _, r in grp.iterrows():
            rows.append({"period_end": r["end"], "usd": r["val"] - prev})
            prev = r["val"]
    q = pd.DataFrame(rows).drop_duplicates("period_end", keep="last").sort_values("period_end")
    return q[q["usd"] > 0]


def latest_10k_url(cik: int) -> tuple[str, str]:
    """Return (filing_date, document_url) of the company's latest 10-K."""
    data = _get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json").json()
    recent = data["filings"]["recent"]
    for form, acc, doc, date in zip(
        recent["form"], recent["accessionNumber"],
        recent["primaryDocument"], recent["filingDate"],
    ):
        if form == "10-K":
            acc_nodash = acc.replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"
            return date, url
    raise LookupError(f"No 10-K found for CIK {cik}")


def fetch_filing_text(url: str) -> str:
    """Fetch a filing document and strip it to plain text."""
    raw = _get(url).text
    text = re.sub(r"<[^>]+>", " ", raw)
    import html as _html
    return re.sub(r"\s+", " ", _html.unescape(text))
