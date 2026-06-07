import pandas as pd
from potindicators.edgar import annual_values, quarterly_values


def _frame(rows):
    df = pd.DataFrame(rows)
    for col in ("start", "end", "filed"):
        df[col] = pd.to_datetime(df[col])
    return df


def test_quarterly_diffs_ytd_values():
    df = _frame([
        # one fiscal year of YTD capex: 10, 25, 45, 70 -> quarters 10,15,20,25
        {"start": "2025-01-01", "end": "2025-03-31", "val": 10, "form": "10-Q", "filed": "2025-04-20"},
        {"start": "2025-01-01", "end": "2025-06-30", "val": 25, "form": "10-Q", "filed": "2025-07-20"},
        {"start": "2025-01-01", "end": "2025-09-30", "val": 45, "form": "10-Q", "filed": "2025-10-20"},
        {"start": "2025-01-01", "end": "2025-12-31", "val": 70, "form": "10-K", "filed": "2026-02-01"},
    ])
    q = quarterly_values(df)
    assert list(q["usd"]) == [10, 15, 20, 25]


def test_annual_prefers_cy_frames():
    df = _frame([
        {"start": "2025-01-01", "end": "2025-12-31", "val": 70, "form": "10-K",
         "filed": "2026-02-01"},
    ])
    df["frame"] = ["CY2025"]
    a = annual_values(df)
    assert len(a) == 1 and a.iloc[0]["usd"] == 70
