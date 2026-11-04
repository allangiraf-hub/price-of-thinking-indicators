"""Static dashboard in the Codex design (v4.3), aligned with priceofthinking.com.

Stone page, ink type, no accent colour on the page (verdigris only inside the
figures); Tiempos for reading and Forma DJR for labels, numbers and captions, both
loaded cross-origin from the book's site with system fallbacks; figures set as plates;
dark theme through prefers-color-scheme. Tokens are copied from the site's
themes/antique-ink/static/codex/tokens.json.
"""
from __future__ import annotations

import datetime as dt
import html
import json
import shutil
import struct
from pathlib import Path

import pandas as pd

from .config import DOCS

STATIC = Path(__file__).resolve().parent / "static"
REPO = "https://github.com/allangiraf-hub/price-of-thinking-indicators"
BOOK = "https://priceofthinking.com/"
CHAPTER = "https://priceofthinking.com/chapters/the-boom/"
FONTS = "https://priceofthinking.com/fonts/"

COMPANY = {"MSFT": "Microsoft", "GOOGL": "Alphabet", "AMZN": "Amazon",
           "META": "Meta", "ORCL": "Oracle"}

CSS = """
@font-face { font-family:"Tiempos Text"; src:url("__F__TiemposText-VF-Roman.woff2") format("woff2-variations"), url("__F__TiemposText-VF-Roman.woff2") format("woff2"); font-weight:400 700; font-style:normal; font-display:swap; }
@font-face { font-family:"Tiempos Text"; src:url("__F__TiemposText-VF-Italic.woff2") format("woff2-variations"), url("__F__TiemposText-VF-Italic.woff2") format("woff2"); font-weight:400 700; font-style:italic; font-display:swap; }
@font-face { font-family:"Tiempos Headline"; src:url("__F__TiemposHeadline-Medium.woff2") format("woff2"); font-weight:500; font-style:normal; font-display:swap; }
@font-face { font-family:"Forma DJR"; src:url("__F__FormaDJR-VF.woff2") format("woff2-variations"), url("__F__FormaDJR-VF.woff2") format("woff2"); font-weight:300 700; font-style:normal; font-display:swap; }
@font-face { font-family:"Forma DJR Mono"; src:url("__F__FormaDJRMono-VF.woff2") format("woff2-variations"), url("__F__FormaDJRMono-VF.woff2") format("woff2"); font-weight:300 700; font-style:normal; font-display:swap; }

:root {
  color-scheme: light dark;
  --stone:#e8e5de; --ink:#26292e; --slate:#4f535a;
  --bg:#e8e5de; --inset:#dfdcd4; --fg-1:#26292e; --fg-2:#4f535a;
  --rule:#bdbcb7; --rule-strong:#26292e; --link-rule:#4f535a; --border:#7d7e7d;
  --plate:#f1efe9;
  --block-bg:#26292e; --block-fg-1:#e8e5de; --block-fg-2:#c9c7c2; --block-rule:#515255;
  --tile-1x:url("assets/vine-stone.png"); --tile-2x:url("assets/vine-stone@2x.png");
  --text:"Tiempos Text", Charter, "Iowan Old Style", Georgia, serif;
  --display:"Tiempos Headline", Charter, Georgia, serif;
  --sans:"Forma DJR", "Helvetica Neue", Helvetica, Arial, sans-serif;
  --mono:"Forma DJR Mono", "SF Mono", Menlo, Consolas, monospace;
  --margin:2rem;
  --body-size:1.25rem; --body-lead:2rem; --para:1rem;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg:#1b1d21; --inset:#24262b; --fg-1:#e8e5de; --fg-2:#a09f9c;
    --rule:#48494b; --rule-strong:#e8e5de; --link-rule:#a09f9c; --border:#828180;
    --block-bg:#e8e5de; --block-fg-1:#26292e; --block-fg-2:#4b4f56; --block-rule:#bdbcb7;
    --tile-1x:url("assets/vine-ink.png"); --tile-2x:url("assets/vine-ink@2x.png");
  }
}
@media (max-width: 979px) { :root { --body-size:1.1875rem; --body-lead:1.875rem; } }
@media (max-width: 600px) { :root { --margin:1.25rem; --body-size:1.125rem; --body-lead:1.8125rem; --para:.875rem; } }

* { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--bg); color:var(--fg-1); font-family:var(--text);
       font-size:var(--body-size); line-height:var(--body-lead); font-optical-sizing:auto;
       hyphens:auto; text-wrap:pretty; }
.wrap { max-width:calc(560px + 2 * var(--margin)); margin:0 auto; padding:0 var(--margin); }
p { margin:0 0 var(--para); }
a { color:inherit; text-decoration:underline; text-decoration-thickness:1px;
    text-underline-offset:.2em; text-decoration-color:var(--link-rule); }
a:hover, a:focus-visible { text-decoration-color:currentColor; }
:focus-visible { outline:2px solid var(--fg-1); outline-offset:2px; }
.band :focus-visible { outline-color:var(--block-fg-1); }
em { font-style:italic; }
code, .mono { font-family:var(--mono); font-size:.9em; }
.skip { position:absolute; left:var(--margin); top:.5rem; z-index:30; padding:.5rem .75rem;
        background:var(--fg-1); color:var(--bg); font:500 .8125rem/1.2 var(--sans);
        transform:translateY(-200%); }
.skip:focus { transform:none; }

/* labels, numbers, captions: Forma, lining tabular */
.label, .meta, .num, th, td, summary, .fig-no, .src, .measure, .reading, .head, .kicker {
  font-family:var(--sans); font-variant-numeric:lining-nums tabular-nums; hyphens:manual; }
.label, .kicker { font-size:.75rem; line-height:1rem; font-weight:500; letter-spacing:.08em;
                  text-transform:uppercase; color:var(--fg-2); }
.meta { font-size:.8125rem; line-height:1.1875rem; color:var(--fg-2); }

/* head: seal + name wordmark, page label, link back to the book */
.head { border-bottom:1px solid var(--rule-strong); }
.head .wrap { display:flex; align-items:center; justify-content:space-between; gap:.5rem 1.25rem;
              flex-wrap:wrap; min-height:3rem; padding-top:.5rem; padding-bottom:.5rem; }
.brand { display:flex; align-items:center; gap:.75rem; color:var(--fg-1); text-decoration:none; }
.brand .seal { width:28px; height:26px; flex:none; }
.brand .name { height:.75rem; width:auto; }
.head nav { display:flex; align-items:center; gap:1.25rem; font-size:.8125rem; line-height:1.1875rem;
            letter-spacing:.06em; text-transform:uppercase; font-weight:500; }
.head nav .here { color:var(--fg-1); border-bottom:1px solid var(--fg-1); }
.head nav a { color:var(--fg-2); text-decoration:none; padding:.5rem 0; }
.head nav a:hover, .head nav a:focus-visible { color:var(--fg-1); }
@media (max-width:600px) { .brand .seal { width:22px; height:20px; } .head .wrap { min-height:2.75rem; } }

/* opener band: ink block carrying the vine tile at 17 % */
.band { background-color:var(--block-bg); color:var(--block-fg-1);
        background-image:var(--tile-1x);
        background-image:-webkit-image-set(var(--tile-1x) 1x, var(--tile-2x) 2x);
        background-image:image-set(var(--tile-1x) 1x, var(--tile-2x) 2x);
        background-size:144px 144px; }
.band .wrap { padding-top:2.25rem; padding-bottom:2rem; min-height:14rem; display:flex;
              flex-direction:column; justify-content:flex-end; }
.band .label { color:var(--block-fg-2); margin:0 0 1rem; }
.band a { text-decoration-color:var(--block-fg-2); }
.band h1 { font-family:var(--display); font-weight:500; font-size:clamp(1.75rem, 3.2vw, 2.5rem);
           line-height:1.06; letter-spacing:-.015em; margin:0 0 1rem; hyphens:manual; text-wrap:balance; }
.band .standfirst { font-size:1.125rem; line-height:1.75rem; color:var(--block-fg-1); margin:0; }

main { padding-top:2rem; padding-bottom:3rem; }
.stamp { margin:0 0 1.5rem; }

/* headline readings */
.readings { display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:0 2rem; margin:2rem 0 3rem; }
.reading { border-top:1px solid var(--rule-strong); padding:.75rem 0 1.25rem; }
.reading .num { display:block; font-size:1.75rem; line-height:2rem; font-weight:500; letter-spacing:-.01em; }
.reading .meta { display:block; margin-top:.25rem; }
@media (max-width:420px) { .readings { grid-template-columns:1fr; } }

/* sections */
section.ind { margin:3.5rem 0 0; }
.kicker { display:block; margin:0 0 .5rem; }
h2 { font-family:var(--display); font-weight:500; font-size:1.625rem; line-height:2rem;
     letter-spacing:-.005em; margin:0 0 1rem; hyphens:manual; text-wrap:balance; }
h3.small { font:500 .75rem/1rem var(--sans); letter-spacing:.08em; text-transform:uppercase;
           color:var(--fg-2); margin:0 0 .25rem; }
@media (max-width:600px) { h2 { font-size:1.4375rem; line-height:1.8125rem; } .kicker { font-size:.6875rem; } }

/* plates */
figure.plate { margin:2rem 0; padding:0; }
.plate .top { border-top:1px solid var(--rule-strong); padding-top:.75rem; }
.fig-no { display:block; font-size:.8125rem; line-height:1.1875rem; font-weight:700; color:var(--fg-1); }
.fig-title { font-family:var(--display); font-weight:500; font-size:1.375rem; line-height:1.75rem;
             margin:.125rem 0 .5rem; hyphens:manual; text-wrap:balance; }
.measure { font-size:.8125rem; line-height:1.1875rem; color:var(--fg-2); margin:0 0 .75rem; }
.plate .art { background:var(--plate); border-bottom:1px solid var(--rule); }
.plate img { display:block; width:100%; height:auto; }
.src { font-size:.8125rem; line-height:1.1875rem; color:var(--fg-2); margin:.625rem 0 0; max-width:45em; }
.src b { font-weight:500; color:var(--fg-1); }

/* tables */
details.data { margin:1rem 0 0; }
summary { font-size:.75rem; line-height:1rem; font-weight:500; letter-spacing:.08em;
          text-transform:uppercase; color:var(--fg-2); cursor:pointer; padding:.5rem 0; }
summary:hover { color:var(--fg-1); }
.tablewrap { overflow-x:auto; margin:.25rem 0 0; }
table { border-collapse:collapse; width:100%; font-size:.8125rem; line-height:1.1875rem; }
th { font-size:.75rem; letter-spacing:.06em; text-transform:uppercase; font-weight:500;
     color:var(--fg-2); text-align:left; padding:.375rem .75rem .375rem 0;
     border-bottom:1px solid var(--rule-strong); white-space:nowrap; vertical-align:bottom; }
td { padding:.375rem .75rem .375rem 0; border-bottom:1px solid var(--rule); white-space:nowrap; }
th + th, td + td { padding-left:.75rem; }
th:last-child, td:last-child { padding-right:0; }
th.n, td.n { text-align:right; }
td.t { white-space:normal; }

/* text blocks */
.falsify { margin-top:1.25rem; }
.falsify .label { display:block; margin-bottom:.25rem; }
ul.notes { list-style:none; margin:0; padding:0; font-size:1.0625rem; line-height:1.6875rem; }
ul.notes li { padding:.625rem 0; border-top:1px solid var(--rule); hyphens:auto; }
ul.notes li:last-child { border-bottom:1px solid var(--rule); }
footer { border-top:1px solid var(--rule-strong); margin-top:3.5rem; padding-top:1rem; }
footer p { font-family:var(--sans); font-size:.8125rem; line-height:1.1875rem; color:var(--fg-2); overflow-wrap:anywhere; }

@media print {
  :root { --bg:#fff; --fg-1:#26292e; --fg-2:#4f535a; --plate:#fff; }
  .band { background-image:none; border-bottom:1px solid #26292e; background-color:#fff; color:#26292e; }
  .band .label, .band .standfirst { color:#26292e; }
  details.data { display:none; }
}
""".replace("__F__", FONTS)


def _svg(name: str) -> str:
    return (STATIC / name).read_text().strip()


def _preloads() -> str:
    out = []
    for f in ("TiemposText-VF-Roman.woff2", "TiemposHeadline-Medium.woff2", "FormaDJR-VF.woff2"):
        out.append(f'<link rel="preload" href="{FONTS}{f}" as="font" type="font/woff2" crossorigin>')
    return "\n".join(out)


def _head(title: str) -> str:
    return f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="theme-color" content="#e8e5de" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#1b1d21" media="(prefers-color-scheme: dark)">
<title>{html.escape(title)}</title>
<link rel="preconnect" href="https://priceofthinking.com" crossorigin>
{_preloads()}
<style>{CSS}</style></head>"""


def _top(stamp: str) -> str:
    return f"""<a class="skip" href="#main">Skip to the indicators</a>
<header class="head"><div class="wrap">
<a class="brand" href="{BOOK}" aria-label="The Price of Thinking, home">
<svg class="seal" viewBox="0 0 1000 926" fill="currentColor" aria-hidden="true" focusable="false">{_inner(_svg("pot-mark.svg"))}</svg>
<svg class="name" viewBox="0.02 28.80 456.90 24.50" fill="currentColor" aria-hidden="true" focusable="false">{_inner(_svg("pot-name.svg"))}</svg>
</a>
<nav aria-label="Site"><span class="here" aria-current="page">Indicators</span>
<a href="{CHAPTER}">The book</a></nav>
</div></header>
<section class="band" aria-labelledby="t"><div class="wrap">
<p class="label">Companion to <a href="{CHAPTER}">chapter&nbsp;9 of <em>The Price of Thinking</em></a></p>
<h1 id="t">AI boom indicators</h1>
<p class="standfirst">Four falsifiable indicators of whether the AI investment boom is being financed in a way that can absorb disappointment.</p>
</div></section>"""


def _inner(svg: str) -> str:
    a = svg.index(">") + 1
    return svg[a:svg.rindex("</svg>")]


def _png_size(path: Path) -> tuple[int, int] | None:
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        return struct.unpack(">II", head[16:24])
    except Exception:  # noqa: BLE001
        return None


def _figure(n: int, f) -> str:
    size = _png_size(DOCS / f.file)
    wh = f' width="{size[0]}" height="{size[1]}"' if size else ""
    return f"""<figure class="plate" id="fig-{n}">
<div class="top"><span class="fig-no">Figure {n}.</span>
<p class="fig-title">{html.escape(f.title)}</p>
<p class="measure">{html.escape(f.measure)}</p></div>
<div class="art"><img src="{f.file}"{wh} alt="{html.escape(f.alt)}"></div>
<p class="src"><b>Source:</b> {html.escape(f.source)}</p>
</figure>"""


def _table(caption: str, head: list[tuple[str, bool]], rows: list[list[str]]) -> str:
    th = "".join(f'<th scope="col"{" class=n" if num else ""}>{html.escape(h)}</th>' for h, num in head)
    body = "".join(
        "<tr>" + "".join(
            f'<td class="{"n" if head[i][1] else ""}">{html.escape(c)}</td>'
            for i, c in enumerate(r)) + "</tr>" for r in rows)
    return (f'<details class="data"><summary>Data table</summary><div class="tablewrap" tabindex="0" '
            f'role="region" aria-label="{html.escape(caption)}"><table><thead><tr>{th}</tr></thead>'
            f"<tbody>{body}</tbody></table></div></details>")


def depreciation_rows(depr: pd.DataFrame) -> list[dict]:
    rows = []
    for ticker, grp in depr.groupby("ticker"):
        chg = grp.dropna(subset=["life_changed_to_yrs"])
        explicit = chg.dropna(subset=["life_changed_from_yrs"])
        chg = explicit if not explicit.empty else chg
        rng = grp.dropna(subset=["equip_life_max_yrs"])
        if not chg.empty:
            r = chg.iloc[-1]
            rows.append({"ticker": ticker, "life": float(r["life_changed_to_yrs"]),
                         "from": float(r["life_changed_from_yrs"]) if pd.notna(r["life_changed_from_yrs"]) else None})
        elif not rng.empty:
            rows.append({"ticker": ticker, "life": float(rng.iloc[-1]["equip_life_max_yrs"]), "from": None})
    return rows


def _data(capex_rev, fin_mix, depr, gpu, generated: str) -> dict:
    return {
        "generated": generated,
        "capex": [
            {"year": int(r.year), "capex": round(float(r.capex_usd_bn), 1),
             "revenue": None if pd.isna(r.ai_revenue_usd_bn) else float(r.ai_revenue_usd_bn),
             "ratio": None if pd.isna(r.capex_to_revenue) else float(r.capex_to_revenue)}
            for r in capex_rev.itertuples()
        ],
        "financing": [
            {"ticker": r.ticker, "year": int(r.year), "ratio": round(float(r.capex_to_ocf), 3)}
            for r in fin_mix.itertuples() if pd.notna(r.capex_to_ocf)
        ],
        "depreciation": depreciation_rows(depr),
        "gpu": [
            {"date": r.date if isinstance(r.date, str) else str(r.date)[:10], "model": r.gpu_model,
             "usd": float(r.median_usd_hr)}
            for r in gpu.itertuples()
        ],
    }


def _readings(data: dict) -> str:
    withratio = [d for d in data["capex"] if d["ratio"]]
    cap = withratio[-1] if withratio else None
    maxy = max((d["year"] for d in data["financing"]), default=None)
    worst = sorted((d for d in data["financing"] if d["year"] == maxy), key=lambda d: -d["ratio"])
    worst = worst[0] if worst else None
    cut = next((d for d in data["depreciation"] if d["from"] and d["from"] > d["life"]), None)
    models = sorted({d["model"] for d in data["gpu"]})
    pick = "B200" if "B200" in models else (models[0] if models else None)
    top = [d for d in data["gpu"] if d["model"] == pick]
    top.sort(key=lambda d: d["date"])
    items = [
        (f'{cap["ratio"]:.1f} : 1' if cap else "—",
         f'Capex against estimated AI revenue, {cap["year"]}' if cap else "Capex against AI revenue"),
        (f'{worst["ratio"]:.2f}' if worst else "—",
         f'{COMPANY.get(worst["ticker"], worst["ticker"])}: capex / operating cash flow, {worst["year"]}' if worst else "Capex / operating cash flow"),
        (f'{cut["from"]:.0f} → {cut["life"]:.0f} years' if cut else "None",
         f'{COMPANY.get(cut["ticker"], cut["ticker"])} shortened its server lives' if cut else "No shortened server lives"),
        (f'${top[-1]["usd"]:.2f}' if top else "—",
         f'{pick} median rental price per GPU-hour, {top[-1]["date"]}' if top else "GPU rental price"),
    ]
    return '<div class="readings" role="list">' + "".join(
        f'<div class="reading" role="listitem"><span class="num">{html.escape(n)}</span>'
        f'<span class="meta">{html.escape(l)}</span></div>' for n, l in items) + "</div>"


def _tables(data: dict) -> dict:
    t = {}
    rows = [[str(d["year"]), f'{d["capex"]:.1f}',
             f'{d["revenue"]:.0f}' if d["revenue"] else "—",
             f'{d["ratio"]:.1f} : 1' if d["ratio"] else "—"] for d in data["capex"] if d["year"] >= 2019]
    t["capex"] = _table("Capex and estimated AI revenue by year",
                        [("Year", False), ("Capex, $bn", True), ("AI revenue, $bn", True), ("Capex : revenue", True)], rows)
    rows = [[COMPANY.get(d["ticker"], d["ticker"]), f'{d["life"]:.1f}',
             f'{d["from"]:.0f}' if d["from"] else "—"] for d in data["depreciation"]]
    t["depr"] = _table("Disclosed server life by company",
                       [("Company", False), ("Life, years", True), ("Changed from, years", True)], rows)
    years = sorted({d["year"] for d in data["financing"] if d["year"] >= 2019})
    tick = sorted({d["ticker"] for d in data["financing"]})
    look = {(d["ticker"], d["year"]): d["ratio"] for d in data["financing"]}
    rows = [[COMPANY.get(k, k)] + [f'{look[(k, y)]:.2f}' if (k, y) in look else "—" for y in years] for k in tick]
    t["fin"] = _table("Capex divided by operating cash flow, by company and year",
                      [("Company", False)] + [(str(y), True) for y in years], rows)
    rows = []
    for m in sorted({d["model"] for d in data["gpu"]}):
        g = sorted((d for d in data["gpu"] if d["model"] == m), key=lambda d: d["date"])
        rows.append([m, g[0]["date"], f'{g[0]["usd"]:.2f}', g[-1]["date"], f'{g[-1]["usd"]:.2f}', str(len(g))])
    t["gpu"] = _table("Median rental price by GPU model",
                      [("Model", False), ("First week", False), ("First, USD/hr", True), ("Latest week", False), ("Latest, USD/hr", True), ("Weeks", True)], rows)
    return t


METHOD = [
    "<strong>No API keys.</strong> EDGAR requires only a User-Agent header; FRED is read through the public <span class=\"mono\">fredgraph.csv</span> endpoint; the vast.ai marketplace is public.",
    "<strong>Cash-flow XBRL values are year-to-date;</strong> quarterly figures are derived by differencing within the fiscal year.",
    "<strong>Companies differ in tagging</strong> (Amazon books capex under <span class=\"mono\">PaymentsToAcquireProductiveAssets</span>); tags are tried in fallback order.",
    "<strong>Extraction keeps its evidence:</strong> the depreciation table stores the verbatim sentence and filing URL for every value, so nothing rests on the parser alone.",
    "<strong>Curated inputs are few and cited.</strong> AI revenue has no single official series, and private credit deals are not all in public filings; each curated row carries its source.",
]


def build_page(data: dict, figs: dict, stamp: str) -> str:
    tables = _tables(data)
    n = iter(range(1, 20))

    def fig(key):
        return _figure(next(n), figs[key])

    def sec(num, title, falsify, key, tbl=True):
        t = tables.get(key, "") if tbl else ""
        return f"""<section class="ind" aria-labelledby="h{num}">
<span class="kicker">Indicator {num}</span>
<h2 id="h{num}">{title}</h2>
{fig(key) if key in figs else ""}
{t}
<div class="falsify"><span class="label">Falsification condition</span>
<p>{falsify}</p></div>
</section>"""

    body = [
        sec(1, "Capex vs AI revenue", "Doubt the boom if the ratio keeps widening while revenue growth stalls.", "capex"),
        sec(2, "Depreciation realism", "Chips age like fish: watch for assumed server lives shortening toward the sceptics&rsquo; 2&ndash;3 years. Each value is extracted from the latest 10-K with its source sentence preserved.", "depr"),
        sec(3, "Financing mix", "A boom funded from cash flow can absorb disappointment; one funded by debt cannot. Above the dotted line, capex exceeds operating cash flow.", "fin"),
        sec(4, "GPU rental spot prices", "Falling rental prices for top-end chips would be the first hard evidence of overcapacity.", "gpu"),
    ]
    macro = ""
    if figs.get("macro"):
        macro = ('<section class="ind" aria-labelledby="hc"><span class="kicker">Context</span>'
                 '<h2 id="hc">Two macro series</h2>'
                 '<p>Information-processing investment and communication construction frame the macro picture; they are context, not indicators.</p>'
                 + "".join(_figure(next(n), f) for f in figs["macro"]) + "</section>")
    notes = ('<section class="ind" aria-labelledby="hm"><span class="kicker">Method</span>'
             '<h2 id="hm">Method notes</h2><ul class="notes">'
             + "".join(f"<li>{m}</li>" for m in METHOD) + "</ul></section>")
    return (_head("AI boom indicators — The Price of Thinking") + "<body>\n" + _top(stamp)
            + f"""
<main id="main"><div class="wrap">
<p class="meta stamp">Last refresh: {html.escape(stamp)} &middot; updated weekly, automatically &middot;
<a href="{REPO}">source &amp; methodology</a></p>
<p>Every number is drawn from a public primary source: SEC filings, FRED, and the GPU rental marketplace.</p>
{_readings(data)}
{"".join(body)}
{macro}
{notes}
<footer><p>Sources: SEC EDGAR (XBRL company facts; 10-K text), FRED (fredgraph.csv), vast.ai public marketplace.
Curated inputs carry citations in <a href="{REPO}/tree/main/data/curated">data/curated</a>.
Typeset in the design of <a href="{BOOK}">The Price of Thinking</a>. &copy; Allan Pedersen &middot; MIT licence.</p></footer>
</div></main>
</body></html>""")


def fallback_html(figs: list, stamp: str) -> str:
    items = "".join(_figure(i + 1, f) for i, f in enumerate(figs))
    return (_head("AI boom indicators — The Price of Thinking") + "<body>\n" + _top(stamp)
            + f"""
<main id="main"><div class="wrap">
<p class="meta stamp">Last refresh: {html.escape(stamp)} &middot; auto-updated &middot;
<a href="{REPO}">source &amp; methodology</a></p>
<p>Four falsifiable indicators of whether the AI investment boom is being financed in a way that can
absorb disappointment. Data: SEC EDGAR, FRED, vast.ai.</p>
{items}
<footer><p>&copy; Allan Pedersen &middot; MIT licence &middot; indicator definitions and falsification
conditions in the <a href="{REPO}">README</a>.</p></footer>
</div></main>
</body></html>""")


def build_html(capex_rev: pd.DataFrame, fin_mix: pd.DataFrame,
               depr: pd.DataFrame, gpu: pd.DataFrame, figs: dict | None = None,
               stamp: str | None = None) -> None:
    """Write docs/index.html (static, no scripts) and docs/data.json (for transparency/reuse)."""
    stamp = stamp or dt.date.today().isoformat()
    data = _data(capex_rev, fin_mix, depr, gpu, stamp)
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "data.json").write_text(json.dumps(data, indent=1))
    assets = DOCS / "assets"
    assets.mkdir(exist_ok=True)
    for f in STATIC.glob("*.png"):
        shutil.copyfile(f, assets / f.name)
    if figs is None:
        raise ValueError("build_html needs the chart figures (see report.build)")
    (DOCS / "index.html").write_text(build_page(data, figs, stamp))
