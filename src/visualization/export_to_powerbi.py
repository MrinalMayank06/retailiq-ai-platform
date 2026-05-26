#link for master curated table /  final table 
#https://app.fabric.microsoft.com/groups/cbec3cd8-6a7a-48ff-91e5-2056e657574c/lakehouses/df93b0e4-9dea-4677-b7e2-bfaff2ef35a3?redirectedFromSignup=1&experience=fabric-developer&clientSideAuth=0&selectedPath=dbo%2Fcurated_master_sales&extensionScenario=openArtifact

from pathlib import Path
import pandas as pd

from src.common.constants import DATA_CURATED_DIR, ARTIFACTS_DIR


def export_dashboard_csv() -> Path:
    source = DATA_CURATED_DIR / "master_sales_dataset.csv"
    target = ARTIFACTS_DIR / "powerbi_export.csv"

    if not source.exists():
        raise FileNotFoundError("master_sales_dataset.csv not found. Run training first.")

    df = pd.read_csv(source)
    df.to_csv(target, index=False)
    return target


