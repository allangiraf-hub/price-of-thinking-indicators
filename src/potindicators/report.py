"""Build charts, REPORT.md and the static docs/ page (GitHub Pages).

Charts use the vendored Codex house chart theme (chart_theme/): plate ground, one
verdigris emphasis series per chart (the series the title names), the others ink,
slate and ash with distinct dashes, stone-2 gridlines, direct labels instead of a
legend. The sentence title, the measure/unit line and the source line are set by the
page (report_html), not painted into the PNG; the measure is also the axis label.
"""
from __future__ import annotations

import datetime as dt
import json
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import pandas as pd

from .chart_theme import codex_charts as cx
from .config import CHARTS, CURATED, DATA, DOCS, EXTRACTED, FRED_SERIES, ROOT
from .fred import fred_series
from .report_html import depreciation_rows

# A 560 px column at 2x: 5.6 in wide, saved at 200 dpi = 1120 px; the page sets width:100%.
FIG_W = 5.6
DPI = 200
LABEL_PT = 9.5  # 9.5 pt at 100 px/in is 13 px on the page, the Codex caption size

COMPANY = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
           "META": "Meta", "ORCL": "Oracle"}


@dataclass
class Fig:
    file: str          # path relative to docs/
    title: str         # the sentence the chart proves
    measure: str       # measure and unit (also the axis label)
    source: str        # source line
    alt: str           # text alternative


# ----------------------------------------------------------------- helpers
def _new(height: float):
    """A figure on the house plate, web medium, sized for the 560 px column."""
    cx.use("web")
    plt.rcParams.update({
        "font.size": LABEL_PT, "axes.labelsize": LABEL_PT,
        "xtick.labelsize": LABEL_PT, "ytick.labelsize": LABEL_PT,
        "savefig.dpi": DPI,
    })
    fig, ax = plt.subplots(figsize=(FIG_W, height))
    return fig, ax


def _save(fig, ax, name: str) -> str:
    issues = cx.check(ax)
    if issues:
        raise ValueError(f"{name} fails the chart standard: {'; '.join(issues)}")
    CHARTS.mkdir(parents=True, exist_ok=True)
    fig.savefig(CHARTS / name, dpi=DPI)
    plt.close(fig)
    return f"charts/{name}"


def _end_labels(ax, items, min_px: float | None = None) -> None:
    """Direct labels at the end of each series, nudged apart so they never overlap.

    items: (x, y, text, colour, emphasised). Positions are resolved in pixels."""
    fig = ax.figure
    fig.canvas.draw()
    size = plt.rcParams["xtick.labelsize"]
    sep = min_px or size * fig.dpi / 72 * 1.25
    pix = []
    for x, y, text, colour, emph in items:
        px, py = ax.transData.transform((x, y))
        pix.append([px, py, text, colour, emph])
    pix.sort(key=lambda r: r[1])
    for i in range(1, len(pix)):
        if abs(pix[i][0] - pix[i - 1][0]) < 90 and pix[i][1] - pix[i - 1][1] < sep:
            pix[i][1] = pix[i - 1][1] + sep
    inv = ax.transData.inverted()
    for px, py, text, colour, emph in pix:
        x_data, y_data = inv.transform((px, py))
        ax.annotate(text, xy=(x_data, y_data), xytext=(6, 0), textcoords="offset points",
                    va="center", ha="left", color=colour, fontsize=size,
                    fontweight="medium" if emph else "normal", clip_on=False, annotation_clip=False,
                    path_effects=[pe.withStroke(linewidth=3, foreground=cx.PLATE)])


def _series_style(rank: int):
    """rank 0 = the emphasis series; 1-3 = ink, slate, ash with the house dashes;
    beyond that the rest are pooled in faint ash (R14)."""
    if rank == 0:
        return cx.EMPHASIS, "-", plt.rcParams["lines.linewidth"] * 1.6, 1.0, 3
    if rank <= 3:
        return cx.SERIES[rank], cx.DASHES[rank], plt.rcParams["lines.linewidth"], 1.0, 2
    return cx.ASH, "-", plt.rcParams["lines.linewidth"] * 0.7, 0.55, 1


def _plot_series(ax, series, emphasis_label):
    """series: list of (label, x, y). Emphasis first, the rest by last value, high to low.
    Returns the label items for _end_labels."""
    ordered = sorted((s for s in series if s[0] != emphasis_label),
                     key=lambda s: -s[2].iloc[-1] if hasattr(s[2], "iloc") else -s[2][-1])
    ordered = [s for s in series if s[0] == emphasis_label] + ordered
    items = []
    for rank, (label, x, y) in enumerate(ordered):
        colour, dash, lw, alpha, z = _series_style(rank)
        ax.plot(x, y, color=colour, linestyle=dash, linewidth=lw, alpha=alpha, zorder=z,
                solid_capstyle="round", label="_" + label)
        xl = list(x)[-1]
        yl = list(y)[-1]
        items.append((xl, yl, label, cx.SLATE if colour == cx.ASH else colour, rank == 0))
    return items


# ------------------------------------------------------------------ charts
def chart_capex_vs_revenue(df: pd.DataFrame) -> Fig:
    d = df[df["year"] >= 2019]
    sel = d.dropna(subset=["ai_revenue_usd_bn"])
    fig, ax = _new(3.5)
    ax.bar(d["year"], d["capex_usd_bn"], color=cx.EMPHASIS, width=0.62, zorder=2)
    ax.bar(sel["year"], sel["ai_revenue_usd_bn"], color=cx.INK, width=0.34, zorder=3)
    ax.set_ylim(bottom=0)
    ax.set_xticks(list(d["year"]))
    ax.set_xticklabels([str(int(y)) for y in d["year"]])
    ax.set_ylabel("USD bn per year", loc="top")
    top = float(d["capex_usd_bn"].max())
    ax.annotate("Capex of the five hyperscalers", xy=(2019 - 0.3, top * 0.93), ha="left",
                va="center", color=cx.EMPHASIS, fontweight="medium", fontsize=LABEL_PT)
    for _, r in sel.iterrows():
        yr, rev, cap, ratio = int(r["year"]), r["ai_revenue_usd_bn"], r["capex_usd_bn"], r["capex_to_revenue"]
        ax.annotate(f"{ratio:.1f} : 1", (yr, cap), xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=LABEL_PT, color=cx.INK, fontweight="medium")
        ax.annotate(f"Estimated AI revenue,\n${rev:.0f}bn in {yr}", xy=(yr, rev),
                    xytext=(yr - 3.2, top * 0.62), ha="left", va="center", color=cx.INK,
                    fontsize=LABEL_PT,
                    arrowprops=dict(arrowstyle="-", color=cx.SLATE, lw=0.7,
                                    shrinkA=2, shrinkB=1, connectionstyle="arc3,rad=0"))
    ax.set_ylim(0, top * 1.12)
    if sel.empty:
        title = "Hyperscaler capex keeps rising while AI revenue has no single official series"
    else:
        r = sel.iloc[-1]
        title = (f"In {int(r['year'])}, hyperscaler capex ran at {r['capex_to_revenue']:.1f} "
                 f"times estimated AI revenue")
    name = _save(fig, ax, "capex_vs_revenue.png")
    return Fig(name, title, "USD bn per year, calendar years; ratio of capex to AI revenue labelled",
               "SEC EDGAR XBRL company facts (Microsoft, Alphabet, Amazon, Meta, Oracle; payments "
               "for property, plant and equipment); AI revenue is a single curated estimate, "
               "Derek Thompson, 2025.",
               "Bar chart of annual capex of five hyperscalers from 2019, with the one year of "
               "estimated AI revenue drawn narrower in front. " + title + ".")


def chart_financing_mix(df: pd.DataFrame) -> Fig:
    d = df[df["year"] >= 2019].dropna(subset=["capex_to_ocf"])
    last = {t: g.sort_values("year").iloc[-1] for t, g in d.groupby("ticker")}
    lead = max(last, key=lambda t: last[t]["capex_to_ocf"])
    fig, ax = _new(3.6)
    series = [(t, g.sort_values("year")["year"], g.sort_values("year")["capex_to_ocf"].reset_index(drop=True))
              for t, g in d.groupby("ticker")]
    series = [(t, list(x), pd.Series(list(y))) for t, x, y in series]
    ax.axhline(1.0, color=cx.SLATE, lw=0.8, ls=(0, (1, 3)), zorder=1, label="_parity")
    ymax = float(d["capex_to_ocf"].max())
    ax.set_ylim(0, ymax * 1.1)
    years = sorted(d["year"].unique())
    ax.set_xticks(years)
    ax.set_xticklabels([str(int(y)) for y in years])
    ax.set_xlim(years[0] - 0.2, years[-1] + 1.15)
    items = _plot_series(ax, series, lead)
    ax.annotate("Capex equals operating cash flow", xy=(years[0] - 0.1, 1.0), xytext=(0, 4),
                textcoords="offset points", ha="left", va="bottom", color=cx.SLATE, fontsize=LABEL_PT)
    ax.set_ylabel("Capex divided by operating cash flow", loc="top")
    _end_labels(ax, [(x, y, COMPANY.get(t, t), c, e) for (x, y, t, c, e) in items])
    r = last[lead]
    title = (f"{COMPANY.get(lead, lead)}'s capex ran at {r['capex_to_ocf']:.1f} times its "
             f"operating cash flow in {int(r['year'])}")
    name = _save(fig, ax, "financing_mix.png")
    return Fig(name, title, "Ratio of annual capex to net cash from operating activities; "
                            "above the dotted line, capex exceeds operating cash flow",
               "SEC EDGAR XBRL company facts; fiscal years; the latest year may be incomplete.",
               "Line chart of capex over operating cash flow for five hyperscalers since 2019. "
               + title + ".")


def chart_depreciation(df: pd.DataFrame) -> Fig:
    """Effective disclosed server life per company, marking recent changes.

    A downward change (Amazon, Jan 2025: 6y -> 5y) is the sceptics'
    scenario; upward changes flatter reported profits.
    """
    rows = depreciation_rows(df)
    fig, ax = _new(2.7)
    d = pd.DataFrame(rows)
    cut = [r for r in rows if r["from"] and r["from"] > r["life"]]
    if not d.empty:
        d = d.sort_values("life", ascending=False).reset_index(drop=True)
        ypos = list(range(len(d)))[::-1]
        colours = [cx.EMPHASIS if (f and f > l) else cx.SLATE for f, l in zip(d["from"], d["life"])]
        ax.barh(ypos, d["life"], color=colours, height=0.58, zorder=2)
        ax.set_yticks(ypos)
        ax.set_yticklabels([COMPANY.get(t, t) for t in d["ticker"]])
        for y, (_, r) in zip(ypos, d.iterrows()):
            note = (f'{r["from"]:g} → {r["life"]:g} years' if pd.notna(r["from"])
                    else f'{r["life"]:g} years')
            ax.text(r["life"] + 0.12, y, note, va="center", ha="left", fontsize=LABEL_PT,
                    color=cx.EMPHASIS if pd.notna(r["from"]) and r["from"] > r["life"] else cx.SLATE,
                    fontweight="medium" if pd.notna(r["from"]) and r["from"] > r["life"] else "normal")
        ax.axvline(3, color=cx.INK, lw=0.9, ls=(0, (2, 3)), zorder=1)
        ax.annotate("Sceptics: 2 to 3 years", xy=(3, len(d) - 0.5), xytext=(4, 0),
                    textcoords="offset points", ha="left", va="center", color=cx.INK,
                    fontsize=LABEL_PT)
    ax.set_xlim(0, 9)
    ax.set_ylim(-0.6, len(d) - 0.1 + 0.3)
    ax.set_xlabel("Disclosed useful life of servers, years", loc="left")
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=cx.GRID, linewidth=0.6)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="x", length=0)
    ax.tick_params(axis="y", length=0)
    if cut:
        c = cut[0]
        title = (f"{COMPANY.get(c['ticker'], c['ticker'])} shortened its server life from "
                 f"{c['from']:.0f} to {c['life']:.0f} years; the others hold at {min(r['life'] for r in rows if r is not c):.1f} years or more"
                 if len(rows) > 1 else f"{COMPANY.get(c['ticker'], c['ticker'])} shortened its server life")
    else:
        title = "No hyperscaler has shortened its disclosed server life"
    name = _save(fig, ax, "depreciation.png")
    return Fig(name, title, "Disclosed useful life of servers in the latest Form 10-K, years; "
                            "green marks a shortened life",
               "Latest Form 10-K of each company via SEC EDGAR, property and equipment note; "
               "the extracted sentence and filing URL are kept in the repository. "
               "Alphabet and Oracle disclose no figure.",
               "Horizontal bars of disclosed server life by company. " + title + ".")


def chart_gpu(df: pd.DataFrame) -> Fig:
    fig, ax = _new(3.4)
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    models = sorted(df["gpu_model"].unique())
    lead = "B200" if "B200" in models else models[0]
    series = []
    for m, g in df.groupby("gpu_model"):
        g = g.sort_values("date")
        series.append((m, list(g["date"]), pd.Series(list(g["median_usd_hr"]))))
    items = _plot_series(ax, series, lead)
    ax.set_ylim(0, float(df["median_usd_hr"].max()) * 1.1)
    lo, hi = df["date"].min(), df["date"].max()
    ax.set_xlim(lo - pd.Timedelta(days=4), hi + pd.Timedelta(days=22))
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.set_ylabel("USD per GPU-hour", loc="top")
    _end_labels(ax, [(mdates.date2num(x), y, t, c, e) for (x, y, t, c, e) in items])
    g = df[df["gpu_model"] == lead].sort_values("date")
    first, last = g.iloc[0], g.iloc[-1]
    if len(g) > 1:
        title = (f"{lead} rentals cost ${last['median_usd_hr']:.2f} per GPU-hour in "
                 f"{last['date']:%B}, against ${first['median_usd_hr']:.2f} in {first['date']:%B}")
    else:
        title = f"{lead} rentals cost ${last['median_usd_hr']:.2f} per GPU-hour"
    name = _save(fig, ax, "gpu_prices.png")
    return Fig(name, title, "Median asking price of rentable offers, USD per GPU-hour, weekly snapshots",
               "vast.ai public marketplace. Offers for the newest chips are few and some weeks have none, "
               "so a line stops where no offers were listed.",
               "Line chart of median GPU rental prices by model. " + title + ".")


def _macro_title(sid: str, df: pd.DataFrame) -> str:
    last = df.iloc[-1]
    base = df[(df["date"].dt.year == 2019) & (df["date"].dt.quarter == last["date"].quarter
                                                if sid.startswith("Y") else df["date"].dt.month == last["date"].month)]
    ref = base["value"].iloc[0] if not base.empty else df.iloc[0]["value"]
    pct = (last["value"] / ref - 1) * 100
    subject = {"Y033RC1Q027SBEA": "Real investment in information-processing equipment",
               "TLCOMCONS": "Spending on communication construction"}.get(sid, FRED_SERIES[sid])
    stamp = f"{last['date']:%B %Y}" if not sid.startswith("Y") else f"Q{last['date'].quarter} {last['date']:%Y}"
    return f"{subject} stood {abs(pct):.0f}% {'above' if pct >= 0 else 'below'} its 2019 level in {stamp}"


MACRO_MEASURE = {
    "Y033RC1Q027SBEA": "Real private fixed investment, information processing equipment, "
                       "chained dollars, billions, seasonally adjusted annual rate",
    "TLCOMCONS": "Total construction spending, communication, millions of dollars, "
                 "seasonally adjusted annual rate",
}
MACRO_AXIS = {"Y033RC1Q027SBEA": "Chained $bn, SAAR", "TLCOMCONS": "$mn, SAAR"}


def chart_macro() -> list[Fig]:
    out = []
    for sid, label in FRED_SERIES.items():
        df = fred_series(sid)
        df = df[df["date"] >= "2015-01-01"]
        fig, ax = _new(2.9)
        ax.plot(df["date"], df["value"], color=cx.EMPHASIS, lw=plt.rcParams["lines.linewidth"] * 1.6,
                solid_capstyle="round", zorder=3, label="_" + sid)
        ax.set_ylim(0, float(df["value"].max()) * 1.1)
        ax.set_ylabel(MACRO_AXIS.get(sid, ""), loc="top")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:,.0f}"))
        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        title = _macro_title(sid, df)
        name = _save(fig, ax, f"fred_{sid}.png")
        out.append(Fig(name, title, MACRO_MEASURE.get(sid, label),
                       f"FRED, Federal Reserve Bank of St. Louis, series {sid}.",
                       f"Line chart of {label} since 2015. {title}."))
    return out


# ------------------------------------------------------------------ outputs
INTRO = """\
Four falsifiable indicators of whether the AI investment boom is being
financed in a way that can absorb disappointment. Companion to chapter 9
of [The Price of Thinking](https://priceofthinking.com/chapters/the-boom/).
Data: SEC EDGAR (XBRL + 10-K text), FRED, vast.ai marketplace. Updated
automatically; every number traceable to a public primary source.
"""


def build(capex_rev, fin_mix, depr, gpu) -> None:
    stamp = dt.date.today().isoformat()
    figs = {
        "capex": chart_capex_vs_revenue(capex_rev),
        "depr": chart_depreciation(depr),
        "fin": chart_financing_mix(fin_mix),
        "gpu": chart_gpu(gpu),
    }
    macro = chart_macro()
    figs["macro"] = macro
    _write_outputs(figs, capex_rev, fin_mix, depr, gpu, stamp)


def _write_outputs(figs, capex_rev, fin_mix, depr, gpu, stamp) -> None:
    from .report_html import build_html, fallback_html

    ordered = [figs["capex"], figs["depr"], figs["fin"], figs["gpu"], *figs["macro"]]
    md = [f"# AI boom indicators\n\n*Last refresh: {stamp}*\n\n{INTRO}\n"]
    for f in ordered:
        md.append(f"**{f.title}.** {f.measure}.\n\n![{f.alt}](docs/{f.file})\n\n*Source: {f.source}*\n")
    (ROOT / "REPORT.md").write_text("\n".join(md))
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "fallback.html").write_text(fallback_html(ordered, stamp))
    build_html(capex_rev, fin_mix, depr, gpu, figs=figs, stamp=stamp)


# ------------------------------------------------------- offline re-render
def frames_from_disk():
    """Rebuild the four indicator frames from docs/data.json and the extracted CSVs,
    without touching the network (EDGAR, vast.ai). FRED is still read for the two
    context charts; if it is unreachable they are kept as last drawn."""
    d = json.loads((DOCS / "data.json").read_text())
    capex = pd.DataFrame(d["capex"]).rename(columns={
        "capex": "capex_usd_bn", "revenue": "ai_revenue_usd_bn", "ratio": "capex_to_revenue"})
    fin = pd.DataFrame(d["financing"]).rename(columns={"ratio": "capex_to_ocf"})
    gpu = pd.DataFrame(d["gpu"]).rename(columns={"model": "gpu_model", "usd": "median_usd_hr"})
    depr = pd.read_csv(EXTRACTED / "useful_lives.csv")
    return capex, fin, depr, gpu, d.get("generated")


def render_offline() -> None:
    capex, fin, depr, gpu, generated = frames_from_disk()
    figs = {
        "capex": chart_capex_vs_revenue(capex),
        "depr": chart_depreciation(depr),
        "fin": chart_financing_mix(fin),
        "gpu": chart_gpu(gpu),
    }
    try:
        figs["macro"] = chart_macro()
    except Exception as exc:  # noqa: BLE001 — keep the last drawn PNGs
        print(f"FRED unreachable ({exc}); context charts not redrawn")
        figs["macro"] = []
    _write_outputs(figs, capex, fin, depr, gpu, generated or dt.date.today().isoformat())
