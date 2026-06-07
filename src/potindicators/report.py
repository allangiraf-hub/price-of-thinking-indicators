"""Build charts, REPORT.md and the static docs/ page (GitHub Pages)."""
from __future__ import annotations

import datetime as dt

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from .config import CHARTS, DOCS, FRED_SERIES, ROOT
from .fred import fred_series

plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3})


def _save(fig, name: str) -> str:
    CHARTS.mkdir(parents=True, exist_ok=True)
    path = CHARTS / name
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return f"charts/{name}"


def chart_capex_vs_revenue(df: pd.DataFrame) -> str:
    fig, ax1 = plt.subplots(figsize=(8, 4.5))
    d = df[df["year"] >= 2019]
    ax1.bar(d["year"], d["capex_usd_bn"], color="#4878a8", label="Hyperscaler capex ($bn)")
    sel = d.dropna(subset=["ai_revenue_usd_bn"])
    ax1.bar(sel["year"], sel["ai_revenue_usd_bn"], color="#e0913f",
            label="Est. AI revenue ($bn)", width=0.5)
    for _, r in sel.iterrows():
        ax1.annotate(f'{r["capex_to_revenue"]:.0f}:1', (r["year"], r["capex_usd_bn"]),
                     ha="center", va="bottom", fontsize=9)
    ax1.set_title("Indicator 1 — Capex vs AI revenue (MSFT+GOOGL+AMZN+META+ORCL)")
    ax1.set_ylabel("USD bn / year")
    ax1.legend()
    return _save(fig, "capex_vs_revenue.png")


def chart_financing_mix(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    d = df[df["year"] >= 2019]
    for ticker, grp in d.groupby("ticker"):
        ax.plot(grp["year"], grp["capex_to_ocf"], marker="o", label=ticker)
    ax.axhline(1.0, color="red", ls="--", lw=1,
               label="capex = operating cash flow")
    ax.set_title("Indicator 3 — Capex as share of operating cash flow")
    ax.set_ylabel("capex / OCF")
    ax.legend(ncol=3, fontsize=8)
    return _save(fig, "financing_mix.png")


def chart_depreciation(df: pd.DataFrame) -> str:
    """Effective disclosed server life per company, marking recent changes.

    A downward change (Amazon, Jan 2025: 6y -> 5y) is the sceptics'
    scenario; upward changes flatter reported profits.
    """
    fig, ax = plt.subplots(figsize=(8, 3.8))
    rows = []
    for ticker, grp in df.groupby("ticker"):
        chg = grp.dropna(subset=["life_changed_to_yrs"])
        explicit = chg.dropna(subset=["life_changed_from_yrs"])
        chg = explicit if not explicit.empty else chg
        rng = grp.dropna(subset=["equip_life_max_yrs"])
        if not chg.empty:
            r = chg.iloc[-1]
            rows.append({"ticker": ticker, "life": r["life_changed_to_yrs"],
                         "from": r["life_changed_from_yrs"]})
        elif not rng.empty:
            rows.append({"ticker": ticker, "life": rng.iloc[-1]["equip_life_max_yrs"],
                         "from": None})
    d = pd.DataFrame(rows)
    if not d.empty:
        colors = ["#c0504d" if f and f > l else "#4878a8"
                  for f, l in zip(d["from"], d["life"])]
        ax.barh(d["ticker"], d["life"], color=colors)
        for i, r in d.iterrows():
            note = (f'{r["from"]:.0f}y \u2192 {r["life"]:.1f}y'
                    if pd.notna(r["from"]) else f'{r["life"]:.1f}y')
            ax.text(r["life"] + 0.05, i, note, va="center", fontsize=8)
        ax.axvline(3, color="red", ls="--", lw=1, label="sceptics' estimate (~2-3y)")
    ax.set_title("Indicator 2 - Disclosed server useful life (red = shortened)", fontsize=11)
    ax.set_xlabel("years")
    ax.set_xlim(0, 8)
    ax.legend(fontsize=8, loc="lower right")
    return _save(fig, "depreciation.png")


def chart_gpu(df: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(8, 4))
    for model, grp in df.groupby("gpu_model"):
        grp = grp.sort_values("date")
        ax.plot(pd.to_datetime(grp["date"]), grp["median_usd_hr"], marker="o", label=model)
    ax.set_title("Indicator 4 — GPU rental spot price, median $/GPU-hr (vast.ai)")
    ax.set_ylabel("USD per GPU-hour")
    ax.legend(fontsize=8)
    return _save(fig, "gpu_prices.png")


def chart_macro() -> list[str]:
    out = []
    for sid, label in FRED_SERIES.items():
        df = fred_series(sid)
        df = df[df["date"] >= "2015-01-01"]
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(df["date"], df["value"], color="#4878a8")
        ax.set_title(f"Context — {label} [FRED: {sid}]", fontsize=10)
        out.append(_save(fig, f"fred_{sid}.png"))
    return out


INTRO = """\
Four falsifiable indicators of whether the AI investment boom is being
financed in a way that can absorb disappointment. Companion to chapter 9
of [The Price of Thinking](https://priceofthinking.com/chapters/the-boom/).
Data: SEC EDGAR (XBRL + 10-K text), FRED, vast.ai marketplace. Updated
automatically; every number traceable to a public primary source.
"""


def build(capex_rev, fin_mix, depr, gpu) -> None:
    stamp = dt.date.today().isoformat()
    charts = [
        chart_capex_vs_revenue(capex_rev),
        chart_depreciation(depr),
        chart_financing_mix(fin_mix),
        chart_gpu(gpu),
        *chart_macro(),
    ]
    md = [f"# AI boom indicators\n\n*Last refresh: {stamp}*\n\n{INTRO}\n"]
    for c in charts:
        md.append(f"![{c}](docs/{c})\n")
    (ROOT / "REPORT.md").write_text("\n".join(md))

    imgs = "\n".join(
        f'<figure><img src="{c}" alt="{c}" style="max-width:100%"></figure>'
        for c in charts
    )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI boom indicators — The Price of Thinking</title>
<style>
 body {{ font-family: Georgia, serif; max-width: 760px; margin: 2rem auto;
        padding: 0 1rem; color: #222; }}
 h1 {{ font-size: 1.6rem; }} figure {{ margin: 2rem 0; }}
 .stamp {{ color: #777; font-size: .9rem; }}
 a {{ color: #4878a8; }}
</style></head><body>
<h1>AI boom indicators</h1>
<p class="stamp">Last refresh: {stamp} · auto-updated ·
<a href="https://github.com/allangiraf-hub/price-of-thinking-indicators">source &amp; methodology</a></p>
<p>Four falsifiable indicators of whether the AI investment boom is being
financed in a way that can absorb disappointment. Companion to
<a href="https://priceofthinking.com/chapters/the-boom/">chapter 9 of
<em>The Price of Thinking</em></a>. Data: SEC EDGAR, FRED, vast.ai.</p>
{imgs}
<p>© Allan Pedersen · MIT licence · indicator definitions and
falsification conditions in the <a
href="https://github.com/allangiraf-hub/price-of-thinking-indicators">README</a>.</p>
</body></html>"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "fallback.html").write_text(html)
    from .report_html import build_html
    build_html(capex_rev, fin_mix, depr, gpu)
