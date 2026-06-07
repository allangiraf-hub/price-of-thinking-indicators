import pandas as pd
from potindicators.config import CURATED


def test_ai_revenue_file_well_formed():
    df = pd.read_csv(CURATED / "ai_revenue_estimates.csv")
    assert {"year", "ai_revenue_usd_bn", "source"} <= set(df.columns)
    assert df["ai_revenue_usd_bn"].gt(0).all()
