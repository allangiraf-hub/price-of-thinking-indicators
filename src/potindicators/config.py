"""Central configuration: companies, XBRL tags, FRED series, paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CURATED = DATA / "curated"
SNAPSHOTS = DATA / "snapshots"
EXTRACTED = DATA / "extracted"
DOCS = ROOT / "docs"
CHARTS = DOCS / "charts"

# Identify politely to SEC EDGAR (required by their fair-access policy).
EDGAR_USER_AGENT = "price-of-thinking-indicators (allangiraf@gmail.com)"

# Hyperscalers tracked. CIK = SEC central index key.
COMPANIES = {
    "MSFT": 789019,
    "GOOGL": 1652044,
    "AMZN": 1018724,
    "META": 1326801,
    "ORCL": 1341439,
}

# XBRL tags, in fallback order (companies differ; e.g. Amazon books capex
# under PaymentsToAcquireProductiveAssets).
TAG_CAPEX = [
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "PaymentsToAcquireProductiveAssets",
    "PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets",
]
TAG_OCF = ["NetCashProvidedByUsedInOperatingActivities"]
TAG_DEBT_ISSUED = [
    "ProceedsFromIssuanceOfLongTermDebt",
    "ProceedsFromIssuanceOfSeniorLongTermDebt",
    "ProceedsFromNotesPayable",
]

# FRED series (fetched via the keyless fredgraph.csv endpoint).
FRED_SERIES = {
    "Y033RC1Q027SBEA": "Real private fixed investment: information processing equipment (chained $bn, SAAR)",
    "TLCOMCONS": "Total construction spending: communication ($mn, SAAR)",
}

# GPUs whose marketplace rental price we snapshot.
GPU_MODELS = ["H100 SXM", "H100 PCIE", "H200", "A100 SXM4", "RTX 4090", "B200"]
