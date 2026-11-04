"""codex_charts — the house chart theme for matplotlib (Codex v4.1), v1.0, 3 Nov 2026.

Vendored from Dropbox PKM/09-Meta/chart-theme/codex_charts.py on 4 Nov 2026; do not edit here.

Standard: PKM/09-Meta/Presentation-and-Illustration-Standard.md, §C (R13–R21).
Tokens:   PKM/09-Meta/chart-theme/codex-chart-tokens.json (mirrors personal-site/static/codex/tokens.json).

The theme enforces the chart rules that can be enforced by code:
  R8/R17  figure + sentence as one unit: `finish()` sets a sentence title, a measure/unit
          subtitle and a source caption, and refuses to save without them;
  R14/R15 bars from zero, no dual axis, a line that does not start at zero keeps a third
          of the plot free below its minimum (`headroom()`), no pie above three slices;
  R16     one emphasis series (verdigris) per figure, the rest ink / slate / ash, direct
          labels instead of a legend (`emphasise()`, `label_lines()`), stone-2 gridlines;
  R18     one figure per medium: `use(medium=...)` sets the geometry for paper, web or slide.

Typical use:

    import codex_charts as cx
    cx.use("paper")                                 # or "web", "slide", "typst"
    fig, ax = cx.figure()
    ax.plot(x, y_main, label="Eurodollar deposits")
    ax.plot(x, y_ctx, label="M2")
    cx.emphasise(ax, "Eurodollar deposits")          # the series the title names
    cx.label_lines(ax)
    cx.finish(fig, ax,
              title="Eurodollar deposits overtook M2 in 1981",
              measure="USD bn, end-year, deflated to 2020 prices",
              source="BIS locational statistics; Federal Reserve H.6; author's calculations, 2026")
    cx.save(fig, "fig-01-eurodollar.svg")           # also .pdf / .png
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

_HERE = Path(__file__).resolve().parent
_TOKENS = json.loads((_HERE / "codex-chart-tokens.json").read_text(encoding="utf-8"))

EMPHASIS = _TOKENS["figure"]["emphasis"]        # verdigris
INK = _TOKENS["ink"]["fg_1"]
SLATE = _TOKENS["ink"]["fg_2"]
ASH = _TOKENS["figure"]["context"]
GRID = _TOKENS["figure"]["gridline"]
PLATE = _TOKENS["ground"]["plate"]
PAPER = _TOKENS["ground"]["paper"]
SERIES = list(_TOKENS["figure"]["series"])
DASHES = ["-", "-", (0, (7, 4)), (0, (2, 4))]

# geometry per medium: width in inches, type sizes in pt, line widths in pt
_MEDIA = {
    "paper": dict(width=6.26, height=3.6, title=11, sub=8.25, label=8.25, caption=8.25, line=1.1, emph=1.8, ground=PAPER),
    "web":   dict(width=11.0, height=5.5, title=16.5, sub=10, label=10, caption=10, line=1.6, emph=2.5, ground=PLATE),
    "slide": dict(width=11.78, height=5.6, title=0, sub=14, label=12, caption=12, line=1.6, emph=2.8, ground=PLATE),
    # for AP Publish: the Typst plate() carries title, measure and source; the SVG is the bare chart
    "typst": dict(width=6.26, height=3.4, title=0, sub=0, label=8.25, caption=0, line=1.1, emph=1.8, ground=PAPER),
}
_state = {"medium": "paper"}


def use(medium: str = "paper") -> None:
    """Load the house style and set the geometry for one medium (R18).

    On a slide the title is the slide headline (title=0); for "typst" the plate() in
    codex-charts.typ carries title, measure and source, so the SVG is the bare chart."""
    if medium not in _MEDIA:
        raise ValueError(f"medium must be one of {list(_MEDIA)}")
    plt.style.use(str(_HERE / "codex.mplstyle"))
    m = _MEDIA[medium]
    mpl.rcParams.update({
        "figure.figsize": (m["width"], m["height"]),
        "axes.labelsize": m["label"], "xtick.labelsize": m["label"], "ytick.labelsize": m["label"],
        "font.size": m["label"], "lines.linewidth": m["line"],
        "figure.facecolor": m["ground"], "axes.facecolor": m["ground"], "savefig.facecolor": m["ground"],
    })
    _state["medium"] = medium
    _warn_fonts()


def _warn_fonts() -> None:
    names = {f.name for f in mpl.font_manager.fontManager.ttflist}
    missing = [n for n in ("Forma DJR Text", "Tiempos Headline") if n not in names]
    if missing:
        warnings.warn(f"house fonts not installed: {missing}; geometry is right, faces are fallbacks "
                      f"(install from 09-Meta/fonts/, see chart-theme/README.md)", stacklevel=2)


def figure(**kw):
    """A figure and axes on the house ground."""
    fig, ax = plt.subplots(**kw)
    return fig, ax


def emphasise(ax, label: str) -> None:
    """Make the series named `label` the one verdigris series; every other line becomes
    context (ink, slate, ash with the house dashes, in the order drawn). R16."""
    lines = [l for l in ax.get_lines() if l.get_label() and not l.get_label().startswith("_")]
    if not any(l.get_label() == label for l in lines):
        raise ValueError(f"no series labelled {label!r}; labels are {[l.get_label() for l in lines]}")
    m = _MEDIA[_state["medium"]]
    ctx = [(c, d) for c, d in zip(SERIES[1:], DASHES[1:])]
    i = 0
    for l in lines:
        if l.get_label() == label:
            l.set_color(EMPHASIS); l.set_linestyle("-"); l.set_linewidth(m["emph"]); l.set_zorder(3)
        else:
            c, d = ctx[i % len(ctx)]; i += 1
            l.set_color(c); l.set_linestyle(d); l.set_linewidth(m["line"]); l.set_zorder(2)
    if len(lines) > _TOKENS["rules"]["max_highlighted_series"] + 1:
        warnings.warn("more than four context series: pool the rest as 'Others' (R14)", stacklevel=2)


def label_lines(ax, pad: float = 0.01) -> None:
    """Direct labels at the right end of each line, in the line's colour; no legend. R16."""
    xmin, xmax = ax.get_xlim()
    for l in ax.get_lines():
        lab = l.get_label()
        if not lab or lab.startswith("_"):
            continue
        xs, ys = l.get_xdata(), l.get_ydata()
        if len(xs) == 0:
            continue
        ax.annotate(lab, (xs[-1], ys[-1]), xytext=(4, 0), textcoords="offset points",
                    va="center", ha="left", color=l.get_color(), fontsize=mpl.rcParams["xtick.labelsize"],
                    fontweight="medium" if l.get_color() == EMPHASIS else "normal", clip_on=False)
    ax.set_xlim(xmin, xmax + (xmax - xmin) * pad)
    leg = ax.get_legend()
    if leg is not None:
        leg.remove()


def bars(ax, categories, values, emphasis=None, horizontal=True, sort=True):
    """Ranking bars: sorted, from zero, one emphasised bar, direct value labels. R14/R15."""
    pairs = list(zip(categories, values))
    if sort:
        pairs.sort(key=lambda p: p[1], reverse=not horizontal)
    cats, vals = zip(*pairs)
    colors = [EMPHASIS if c == emphasis else SLATE for c in cats]
    if horizontal:
        b = ax.barh(cats, vals, color=colors, height=0.62)
        ax.set_xlim(left=0)
        ax.grid(axis="x", color=GRID, linewidth=0.6); ax.grid(axis="y", visible=False)
        ax.spines["bottom"].set_visible(False); ax.tick_params(axis="x", length=0)
        ax.bar_label(b, fmt="%g", padding=3, fontsize=mpl.rcParams["xtick.labelsize"], color=SLATE)
    else:
        b = ax.bar(cats, vals, color=colors, width=0.62)
        ax.set_ylim(bottom=0)
        ax.bar_label(b, fmt="%g", padding=3, fontsize=mpl.rcParams["xtick.labelsize"], color=SLATE)
    return b


def headroom(ax, share: float | None = None) -> None:
    """A line chart whose axis does not start at zero keeps at least a third of the plot
    free below the lowest point (the Economist's rule). R15."""
    share = share or _TOKENS["rules"]["line_min_headroom_below"]
    ymin, ymax = ax.get_ylim()
    data_min = min(min(l.get_ydata()) for l in ax.get_lines() if len(l.get_ydata()))
    if ymin <= 0 <= data_min:
        return
    span = ymax - data_min
    ax.set_ylim(data_min - span * share / (1 - share), ymax)


def check(ax) -> list[str]:
    """Rule violations the code can see. Empty list = pass."""
    issues = []
    if ax.get_legend() is not None:
        issues.append("legend present — use direct labels (R16)")
    if any(isinstance(a, mpl.axes.Axes) and a is not ax and a.get_shared_x_axes().joined(a, ax) for a in ax.figure.axes):
        issues.append("secondary y-axis — use two panels (R15)")
    if ax.patches and ax.get_ylim()[0] > 0 and not ax.get_xlim()[0] > 0:
        issues.append("bars not from zero (R15)")
    n_emph = sum(1 for l in ax.get_lines() if l.get_color() == EMPHASIS) + sum(
        1 for p in ax.patches if mpl.colors.to_hex(p.get_facecolor()) == EMPHASIS)
    if n_emph > 1 and ax.get_lines():
        issues.append(f"{n_emph} verdigris series — one per figure (R16)")
    wedges = [p for p in ax.patches if p.__class__.__name__ == "Wedge"]
    if len(wedges) > _TOKENS["rules"]["pie_max_slices"]:
        issues.append("pie with more than three slices — use sorted bars (R14)")
    return issues


def finish(fig, ax, title: str, measure: str, source: str, note: str | None = None) -> None:
    """Title (the message), subtitle (measure and unit), caption (source). R8/R11/R17.
    On a slide the title is left to the slide headline."""
    m = _MEDIA[_state["medium"]]
    for t in (title, measure, source):
        if not t or not t.strip():
            raise ValueError("title, measure and source are not optional (R17)")
    if title.rstrip()[-1:] in ".:" or len(title.split()) < 3:
        warnings.warn("the title should be a sentence stating the finding, no full stop (R3)", stacklevel=2)
    problems = check(ax)
    if problems:
        raise ValueError("figure fails the standard: " + "; ".join(problems))
    # subtitle (measure and unit) is the axes title so the layout engine makes room for it;
    # the message is the figure title above it, in Tiempos Headline
    if m["sub"]:
        ax.set_title(measure, loc="left", fontsize=m["sub"], fontweight="normal", color=SLATE, pad=10)
    st = None
    if m["title"]:
        st = fig.suptitle(title, x=0.0, ha="left", fontsize=m["title"], fontweight="medium",
                          fontfamily=["Tiempos Headline", "Tiempos Text", "DejaVu Serif"], color=INK)
    ct = None
    if m["caption"]:
        cap = f"Source: {source}" + (f"  ·  Note: {note}" if note else "")
        ct = fig.text(0.0, -0.02, cap, ha="left", va="top", fontsize=m["caption"], color=SLATE,
                      fontfamily=["Forma DJR Micro", "Forma DJR Text", "DejaVu Sans"])
    # align title and caption on the plot's left edge (R25: one left edge for the unit)
    fig.canvas.draw()
    x0 = ax.get_position().x0
    if ct is not None:
        ct.set_x(x0)
    if st is not None:
        st.set_x(x0)


def save(fig, path: str | os.PathLike, formats: tuple[str, ...] = ()) -> list[Path]:
    """Save as the path's own format plus any extra formats. SVG keeps text as text."""
    p = Path(path)
    out = [p] + [p.with_suffix("." + f) for f in formats]
    for q in out:
        fig.savefig(q, bbox_inches="tight", pad_inches=0.1)
    return out


__all__ = ["use", "figure", "emphasise", "label_lines", "bars", "headroom", "check", "finish", "save",
           "EMPHASIS", "INK", "SLATE", "ASH", "GRID", "PLATE", "PAPER", "SERIES"]
