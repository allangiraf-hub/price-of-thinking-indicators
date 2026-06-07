"""Styled static dashboard, visually aligned with priceofthinking.com."""
from __future__ import annotations

import datetime as dt
import json

import pandas as pd

from .config import DOCS

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI boom indicators — The Price of Thinking</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
:root {
  --bg:#faf8f5; --ink:#1f1d1a; --muted:#6f6a62; --rule:#e4ded4;
  --accent:#4878a8; --accent2:#e0913f; --bad:#c0504d; --card:#ffffff;
}
@media (prefers-color-scheme: dark) {
  :root { --bg:#171513; --ink:#e8e4dd; --muted:#9b948a; --rule:#33302b;
          --accent:#7ea4c9; --accent2:#e0a35f; --bad:#d4716e; --card:#201d1a; }
}
* { box-sizing:border-box; }
body { font-family: Georgia, 'Times New Roman', serif; background:var(--bg);
       color:var(--ink); max-width:880px; margin:0 auto; padding:2.5rem 1.2rem 4rem;
       line-height:1.55; }
.mark { font-size:.8rem; letter-spacing:.28em; text-transform:uppercase;
        color:var(--muted); }
.mark a { color:inherit; text-decoration:none; }
h1 { font-size:2rem; font-weight:normal; margin:.4rem 0 .2rem; }
.stamp { color:var(--muted); font-size:.85rem; margin-bottom:2rem; }
.lede { font-size:1.02rem; max-width:60ch; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
         gap:.8rem; margin:2rem 0 2.5rem; }
.card { background:var(--card); border:1px solid var(--rule); border-radius:6px;
        padding:.9rem 1rem; }
.card .num { font-size:1.7rem; }
.card .num.warn { color:var(--bad); }
.card .lbl { font-size:.8rem; color:var(--muted); }
section { margin:3rem 0; }
h2 { font-size:1.15rem; font-weight:normal; border-top:1px solid var(--rule);
     padding-top:1.6rem; }
h2 .no { color:var(--muted); margin-right:.5em; }
.falsify { font-style:italic; color:var(--muted); font-size:.92rem;
           margin:-.3rem 0 1rem; }
.chartbox { background:var(--card); border:1px solid var(--rule);
            border-radius:6px; padding:1rem; }
canvas { max-height:340px; }
footer { border-top:1px solid var(--rule); margin-top:3.5rem; padding-top:1.2rem;
         color:var(--muted); font-size:.85rem; }
a { color:var(--accent); }
</style></head><body>
<div class="mark"><a href="https://priceofthinking.com/">The Price of Thinking</a> · Indicators</div>
<h1>AI boom indicators</h1>
<div class="stamp">Last refresh: __STAMP__ · updated weekly, automatically ·
<a href="https://github.com/allangiraf-hub/price-of-thinking-indicators">source &amp; methodology</a></div>
<p class="lede">Four falsifiable indicators of whether the AI investment boom is
being financed in a way that can absorb disappointment — the live companion to
<a href="https://priceofthinking.com/chapters/the-boom/">chapter&nbsp;9 of
<em>The Price of Thinking</em></a>. Every number is drawn from a public primary
source: SEC filings, FRED, and the GPU rental marketplace.</p>

<div class="cards" id="cards"></div>

<section>
<h2><span class="no">1</span>Capex vs AI revenue</h2>
<p class="falsify">Doubt the boom if the ratio keeps widening while revenue growth stalls.</p>
<div class="chartbox"><canvas id="c_capex"></canvas></div>
</section>

<section>
<h2><span class="no">2</span>Depreciation realism</h2>
<p class="falsify">Chips age like fish: watch for assumed server lives shortening toward the sceptics&rsquo; 2&ndash;3 years. Each value is extracted from the latest 10-K with its source sentence preserved.</p>
<div class="chartbox"><canvas id="c_depr"></canvas></div>
</section>

<section>
<h2><span class="no">3</span>Financing mix</h2>
<p class="falsify">A boom funded from cash flow can absorb disappointment; one funded by debt cannot. Above the dashed line, capex exceeds operating cash flow.</p>
<div class="chartbox"><canvas id="c_fin"></canvas></div>
</section>

<section>
<h2><span class="no">4</span>GPU rental spot prices</h2>
<p class="falsify">Falling rental prices for top-end chips would be the first hard evidence of overcapacity.</p>
<div class="chartbox"><canvas id="c_gpu"></canvas></div>
</section>

<footer>Sources: SEC EDGAR (XBRL company facts; 10-K text), FRED
(fredgraph.csv), vast.ai public marketplace. Curated inputs carry citations in
<a href="https://github.com/allangiraf-hub/price-of-thinking-indicators/tree/main/data/curated">data/curated</a>.
© Allan Pedersen · MIT licence.</footer>

<script>
const DATA = __DATA__;
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
const A = css('--accent'), A2 = css('--accent2'), BAD = css('--bad'),
      MUT = css('--muted'), INK = css('--ink');
Chart.defaults.font.family = "Georgia, serif";
Chart.defaults.color = MUT;

// ----- headline cards -----
const last = DATA.capex[DATA.capex.length - 1];
const worstFin = DATA.financing.filter(d => d.year === Math.max(...DATA.financing.map(x => x.year)))
                              .sort((a, b) => b.ratio - a.ratio)[0];
const cut = DATA.depreciation.find(d => d.from && d.from > d.life);
const gpuModels = [...new Set(DATA.gpu.map(d => d.model))];
const topGpu = DATA.gpu.filter(d => d.model === (gpuModels.includes('B200') ? 'B200' : gpuModels[0]));
const cards = [
  [last.ratio ? last.ratio.toFixed(1) + ':1' : '—', `capex vs AI revenue, ${last.year}`, false],
  [worstFin ? (worstFin.ratio).toFixed(2) : '—', `${worstFin.ticker} capex / operating cash flow, ${worstFin.year}`, worstFin.ratio > 1],
  [cut ? `${cut.from}y → ${cut.life}y` : 'none', cut ? `${cut.ticker} shortened server lives` : 'no shortened server lives', !!cut],
  [topGpu.length ? '$' + topGpu[topGpu.length-1].usd.toFixed(2) : '—', `${topGpu.length ? topGpu[0].model : ''} median $/GPU-hr`, false],
];
document.getElementById('cards').innerHTML = cards.map(([n, l, warn]) =>
  `<div class="card"><div class="num${warn ? ' warn' : ''}">${n}</div><div class="lbl">${l}</div></div>`).join('');

// ----- 1: capex vs revenue -----
const cy = DATA.capex.filter(d => d.year >= 2019);
new Chart(c_capex, { type: 'bar', data: { labels: cy.map(d => d.year), datasets: [
  { label: 'Hyperscaler capex ($bn)', data: cy.map(d => d.capex), backgroundColor: A },
  { label: 'Est. AI revenue ($bn)', data: cy.map(d => d.revenue), backgroundColor: A2 },
]}, options: { plugins: { tooltip: { callbacks: { afterBody: (it) => {
  const d = cy[it[0].dataIndex];
  return d.ratio ? `ratio ${d.ratio.toFixed(1)} : 1` : '';
}}}}, scales: { y: { title: { display: true, text: 'USD bn / year' }}}}});

// ----- 2: depreciation -----
const dep = DATA.depreciation;
new Chart(c_depr, { type: 'bar', data: { labels: dep.map(d => d.ticker), datasets: [{
  label: 'disclosed server life (years)', data: dep.map(d => d.life),
  backgroundColor: dep.map(d => d.from && d.from > d.life ? BAD : A),
}]}, options: { indexAxis: 'y', plugins: { tooltip: { callbacks: { afterBody: (it) => {
  const d = dep[it[0].dataIndex];
  return d.from ? `changed from ${d.from}y` : 'range disclosure';
}}}}, scales: { x: { max: 8, title: { display: true, text: 'years' }}}}});

// ----- 3: financing mix -----
const tickers = [...new Set(DATA.financing.map(d => d.ticker))];
const finYears = [...new Set(DATA.financing.filter(d => d.year >= 2019).map(d => d.year))].sort();
const palette = [A, A2, BAD, MUT, INK];
new Chart(c_fin, { type: 'line', data: { labels: finYears, datasets: [
  ...tickers.map((t, i) => ({ label: t, borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length],
    data: finYears.map(y => { const r = DATA.financing.find(d => d.ticker === t && d.year === y);
                              return r ? r.ratio : null; }) })),
  { label: 'capex = cash flow', data: finYears.map(() => 1), borderColor: BAD,
    borderDash: [6, 4], pointRadius: 0, borderWidth: 1 },
]}, options: { scales: { y: { title: { display: true, text: 'capex / operating cash flow' }}}}});

// ----- 4: GPU prices -----
const gDates = [...new Set(DATA.gpu.map(d => d.date))].sort();
new Chart(c_gpu, { type: 'line', data: { labels: gDates, datasets:
  gpuModels.map((m, i) => ({ label: m, borderColor: palette[i % palette.length],
    backgroundColor: palette[i % palette.length],
    data: gDates.map(dt => { const r = DATA.gpu.find(d => d.model === m && d.date === dt);
                             return r ? r.usd : null; }) })),
}, options: { scales: { y: { title: { display: true, text: 'USD per GPU-hour' }}}}});
</script>
</body></html>"""


def build_html(capex_rev: pd.DataFrame, fin_mix: pd.DataFrame,
               depr: pd.DataFrame, gpu: pd.DataFrame) -> None:
    """Write docs/index.html (data embedded, works from file:// and Pages)
    and docs/data.json (for transparency/reuse)."""
    dep_rows = []
    for ticker, grp in depr.groupby("ticker"):
        chg = grp.dropna(subset=["life_changed_to_yrs"])
        explicit = chg.dropna(subset=["life_changed_from_yrs"])
        chg = explicit if not explicit.empty else chg
        rng = grp.dropna(subset=["equip_life_max_yrs"])
        if not chg.empty:
            r = chg.iloc[-1]
            dep_rows.append({"ticker": ticker, "life": float(r["life_changed_to_yrs"]),
                             "from": float(r["life_changed_from_yrs"]) if pd.notna(r["life_changed_from_yrs"]) else None})
        elif not rng.empty:
            dep_rows.append({"ticker": ticker,
                             "life": float(rng.iloc[-1]["equip_life_max_yrs"]), "from": None})
    data = {
        "generated": dt.date.today().isoformat(),
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
        "depreciation": dep_rows,
        "gpu": [
            {"date": r.date, "model": r.gpu_model, "usd": float(r.median_usd_hr)}
            for r in gpu.itertuples()
        ],
    }
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "data.json").write_text(json.dumps(data, indent=1))
    html = TEMPLATE.replace("__DATA__", json.dumps(data)).replace(
        "__STAMP__", data["generated"])
    (DOCS / "index.html").write_text(html)
