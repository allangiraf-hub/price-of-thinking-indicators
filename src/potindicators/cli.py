"""Run the full refresh: python -m potindicators.cli [step]"""
from __future__ import annotations

import sys

from . import indicators, report


def main() -> None:
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    capex_rev = fin_mix = depr = gpu = None
    if step in ("all", "capex"):
        capex_rev = indicators.capex_vs_revenue()
        print(capex_rev.tail(8).to_string(index=False))
    if step in ("all", "financing"):
        fin_mix = indicators.financing_mix()
        print(fin_mix[["ticker", "year", "capex_to_ocf"]].tail(10).to_string(index=False))
    if step in ("all", "depreciation"):
        depr = indicators.depreciation_table()
        print(depr[["ticker", "equip_life_min_yrs", "equip_life_max_yrs"]].to_string(index=False))
    if step in ("all", "gpu"):
        gpu = indicators.gpu_prices()
        print(gpu.tail(8).to_string(index=False))
    if step == "all":
        report.build(capex_rev, fin_mix, depr, gpu)
        print("report built: REPORT.md, docs/index.html")


if __name__ == "__main__":
    main()
