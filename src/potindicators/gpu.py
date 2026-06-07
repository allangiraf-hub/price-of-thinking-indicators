"""GPU rental spot prices from the vast.ai public marketplace.

Falling rental prices for top-end chips would be the first hard evidence
of overcapacity (The Price of Thinking, ch. 9, 'What to watch').
Each run appends today's median $/hr per GPU model to a growing CSV,
so the time series builds itself.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd
import requests

from .config import GPU_MODELS, SNAPSHOTS

SNAPSHOT_FILE = SNAPSHOTS / "gpu_prices.csv"


def fetch_offers() -> pd.DataFrame:
    r = requests.get("https://console.vast.ai/api/v0/bundles/", timeout=60)
    r.raise_for_status()
    offers = r.json().get("offers", [])
    df = pd.DataFrame(
        {
            "gpu_name": o.get("gpu_name"),
            "num_gpus": o.get("num_gpus"),
            "dph_total": o.get("dph_total"),
        }
        for o in offers
    )
    df = df.dropna()
    df = df[df["num_gpus"] > 0]
    df["usd_per_gpu_hr"] = df["dph_total"] / df["num_gpus"]
    return df


def snapshot() -> pd.DataFrame:
    """Append today's median price per tracked GPU model; return full history."""
    offers = fetch_offers()
    today = dt.date.today().isoformat()
    rows = []
    for model in GPU_MODELS:
        sel = offers[offers["gpu_name"].str.contains(model, case=False, na=False)]
        if len(sel) >= 3:
            rows.append(
                {
                    "date": today,
                    "gpu_model": model,
                    "median_usd_hr": round(float(sel["usd_per_gpu_hr"].median()), 4),
                    "n_offers": len(sel),
                }
            )
    new = pd.DataFrame(rows)
    if SNAPSHOT_FILE.exists():
        hist = pd.read_csv(SNAPSHOT_FILE)
        hist = hist[hist["date"] != today]  # idempotent within a day
        new = pd.concat([hist, new], ignore_index=True)
    SNAPSHOT_FILE.parent.mkdir(parents=True, exist_ok=True)
    new.to_csv(SNAPSHOT_FILE, index=False)
    return new
