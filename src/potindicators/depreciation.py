"""Indicator 2: depreciation realism.

Extracts useful-life disclosures for computer/server equipment from each
hyperscaler's latest 10-K. Any move to shorten assumed chip lives signals
the profit-flattering era is ending (ch. 9, 'What to watch').

Extraction is automated but every row carries the source sentence and
filing URL so a human can verify — the sentence IS the evidence.
"""
from __future__ import annotations

import re

import pandas as pd

from .config import COMPANIES, EXTRACTED
from .edgar import fetch_filing_text, latest_10k_url

OUT_FILE = EXTRACTED / "useful_lives.csv"

_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "fifteen": 15, "twenty": 20,
}
_NUM = r"(?:\d+|" + "|".join(_WORDS) + r")"
EQUIP_RE = re.compile(
    rf"(server|computer|network)[\w\s,&-]*?equipment[^.;]*?({_NUM})\s*(?:to|-|–)\s*({_NUM})\s*years",
    re.IGNORECASE,
)


def _to_int(token: str) -> int:
    token = token.lower()
    return _WORDS.get(token, int(token) if token.isdigit() else 0)


def extract_useful_life_sentences(text: str) -> list[str]:
    """Sentences mentioning useful lives of computing equipment."""
    out = []
    for m in re.finditer(r"[^.]*useful liv(?:[^.]|\.(?=\d))*\.", text, re.IGNORECASE):
        s = m.group(0).strip()
        if any(k in s.lower() for k in ("server", "computer", "network equipment")):
            out.append(s[:600])
    return out


def parse_equipment_life(sentence: str) -> tuple[int, int] | None:
    """Return (min_years, max_years) for computing equipment, if stated."""
    m = EQUIP_RE.search(sentence)
    if not m:
        return None
    lo, hi = _to_int(m.group(2)), _to_int(m.group(3))
    return (lo, hi) if 0 < lo <= hi else None


CHANGE_RE = re.compile(
    rf"(?:chang|increas|decreas|extend|reduc)\w*[^.;]*?"
    rf"(?:from\s+({_NUM})\s*years?\s+)?to\s+({_NUM}(?:\.\d)?)\s*years",
    re.IGNORECASE,
)


def parse_life_change(sentence: str) -> tuple[float | None, float] | None:
    """Parse 'changed/extended useful life from X years to Y years' events.

    Returns (old_years_or_None, new_years). These announcements are the
    indicator's clearest signal: a shortening is the sceptics' scenario.
    """
    low = sentence.lower()
    if "server" not in low and "network" not in low:
        return None
    m = CHANGE_RE.search(sentence)
    if not m:
        return None
    old = float(_to_int(m.group(1))) if m.group(1) else None
    new_tok = m.group(2).lower()
    new = float(new_tok) if re.fullmatch(r"\d+(?:\.\d)?", new_tok) else float(_to_int(new_tok))
    if new <= 0:
        return None
    return (old, new)


def run() -> pd.DataFrame:
    rows = []
    for ticker, cik in COMPANIES.items():
        try:
            filing_date, url = latest_10k_url(cik)
            text = fetch_filing_text(url)
            sentences = extract_useful_life_sentences(text)
        except Exception as exc:  # noqa: BLE001 — record, don't crash the run
            rows.append({"ticker": ticker, "error": str(exc)})
            continue
        if not sentences:
            rows.append({"ticker": ticker, "filing_date": filing_date,
                         "filing_url": url, "error": "no disclosure found"})
        for s in sentences:
            rng = parse_equipment_life(s)
            chg = parse_life_change(s)
            rows.append(
                {
                    "ticker": ticker,
                    "filing_date": filing_date,
                    "equip_life_min_yrs": rng[0] if rng else None,
                    "equip_life_max_yrs": rng[1] if rng else None,
                    "life_changed_from_yrs": chg[0] if chg else None,
                    "life_changed_to_yrs": chg[1] if chg else None,
                    "sentence": s,
                    "filing_url": url,
                    "error": "",
                }
            )
    df = pd.DataFrame(rows)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_FILE, index=False)
    return df
