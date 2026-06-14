"""Aggregate the raw CarbonPlan OffsetsDB into compact analysis artifacts.

The raw database (credits.csv ~65 MB, ~530k transactions) is far too large to
ship in a repo or load on a free Streamlit host. This script does the heavy
lifting once — downloading and aggregating — and writes a handful of small CSVs
(a few KB each) that the dashboard reads instantly.

Run it to refresh the data:

    python prep_data.py            # uses data/raw_offsetsdb.csv.zip if present
    python prep_data.py --download # always fetch the latest snapshot

Source: CarbonPlan OffsetsDB — https://carbonplan.org/research/offsets-db
Registries: ACR, ART, Cercarbono, CAR, Gold Standard, Isometric, Verra.
CarbonPlan claims no copyright in the underlying factual registry data.
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

DATA = Path(__file__).parent / "data"
RAW_ZIP = DATA / "raw_offsetsdb.csv.zip"
URL = "https://carbonplan-offsets-db.s3.us-west-2.amazonaws.com/production/latest/offsets-db.csv.zip"

# tidy category labels for display
CATEGORY_LABELS = {
    "renewable-energy": "Renewable energy",
    "forest": "Forestry & land use",
    "energy-efficiency": "Energy efficiency",
    "ghg-management": "GHG management",
    "agriculture": "Agriculture",
    "fuel-switching": "Fuel switching",
    "biomass-cdr": "Biomass carbon removal",
    "land-use": "Land use",
    "alkalinity-cdr": "Ocean alkalinity (CDR)",
    "mineralization-cdr": "Mineralization (CDR)",
    "dac-cdr": "Direct air capture (CDR)",
    "unknown": "Unknown / unclassified",
}

REGISTRY_LABELS = {
    "verra": "Verra (VCS)",
    "gold-standard": "Gold Standard",
    "climate-action-reserve": "Climate Action Reserve",
    "american-carbon-registry": "American Carbon Registry",
    "cercarbono": "Cercarbono",
    "isometric": "Isometric",
    "art-trees": "ART TREES",
}

# obvious duplicate spellings in the harmonized beneficiary field
BENEFICIARY_FIXES = {
    "Delta Airlines": "Delta Air Lines",
}


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    if "--download" in sys.argv or not RAW_ZIP.exists():
        print("Downloading latest OffsetsDB snapshot…")
        r = requests.get(URL, timeout=300)
        r.raise_for_status()
        RAW_ZIP.write_bytes(r.content)
    with zipfile.ZipFile(RAW_ZIP) as z:
        with z.open("projects.csv") as f:
            projects = pd.read_csv(f)
        with z.open("credits.csv") as f:
            credits = pd.read_csv(f, low_memory=False)
    return projects, credits


def main() -> None:
    projects, credits = load_raw()
    print(f"projects: {projects.shape} | credits: {credits.shape}")

    # ---------- headline KPIs ----------
    issued = projects["issued"].sum()
    retired = projects["retired"].sum()
    kpis = {
        "n_projects": int(len(projects)),
        "n_registries": int(projects["registry"].nunique()),
        "n_countries": int(projects["country"].nunique()),
        "issued_mt": round(issued / 1e6, 1),
        "retired_mt": round(retired / 1e6, 1),
        "surplus_mt": round((issued - retired) / 1e6, 1),
        "retirement_rate": round(retired / issued, 3),
        "snapshot": pd.Timestamp.today().strftime("%B %Y"),
    }
    (DATA / "kpis.json").write_text(json.dumps(kpis, indent=2))

    # ---------- market flow by year (issuance vs retirement) ----------
    credits["year"] = pd.to_datetime(credits["transaction_date"], errors="coerce").dt.year
    flow = (
        credits[credits["transaction_type"].isin(["issuance", "retirement"])]
        .query("2010 <= year <= 2025")
        .groupby(["year", "transaction_type"])["quantity"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    flow["year"] = flow["year"].astype(int)
    for col in ("issuance", "retirement"):
        flow[col] = (flow[col] / 1e6).round(2)
    flow.to_csv(DATA / "flow_by_year.csv", index=False)

    # ---------- by project category ----------
    cat = (
        projects.groupby("category")
        .agg(issued=("issued", "sum"), retired=("retired", "sum"),
             n_projects=("project_id", "count"))
        .reset_index()
    )
    cat["label"] = cat["category"].map(CATEGORY_LABELS).fillna(cat["category"])
    cat["issued_mt"] = (cat["issued"] / 1e6).round(1)
    cat["retired_mt"] = (cat["retired"] / 1e6).round(1)
    cat["retirement_rate"] = (cat["retired"] / cat["issued"]).round(3)
    cat = cat.sort_values("issued", ascending=False)
    cat[["label", "n_projects", "issued_mt", "retired_mt", "retirement_rate"]].to_csv(
        DATA / "by_category.csv", index=False
    )

    # ---------- by host country ----------
    country = (
        projects.groupby("country")
        .agg(issued=("issued", "sum"), retired=("retired", "sum"),
             n_projects=("project_id", "count"))
        .reset_index()
    )
    country["issued_mt"] = (country["issued"] / 1e6).round(1)
    country["retired_mt"] = (country["retired"] / 1e6).round(1)
    country = country[country["issued_mt"] > 0].sort_values("issued", ascending=False)
    country[["country", "n_projects", "issued_mt", "retired_mt"]].head(25).to_csv(
        DATA / "by_country.csv", index=False
    )

    # ---------- by registry ----------
    reg = (
        projects.groupby("registry")
        .agg(issued=("issued", "sum"), retired=("retired", "sum"),
             n_projects=("project_id", "count"))
        .reset_index()
    )
    reg["label"] = reg["registry"].map(REGISTRY_LABELS).fillna(reg["registry"])
    reg["issued_mt"] = (reg["issued"] / 1e6).round(1)
    reg["retired_mt"] = (reg["retired"] / 1e6).round(1)
    reg = reg.sort_values("issued", ascending=False)
    reg[["label", "n_projects", "issued_mt", "retired_mt"]].to_csv(
        DATA / "by_registry.csv", index=False
    )

    # ---------- top corporate retirers ----------
    ret = credits[credits["transaction_type"] == "retirement"].copy()
    ret["who"] = ret["retirement_beneficiary_harmonized"].replace(BENEFICIARY_FIXES)
    ret = ret[ret["who"].notna() & (ret["who"].str.strip() != "")]
    top_ben = (
        ret.groupby("who")["quantity"].sum().sort_values(ascending=False).head(15)
        / 1e6
    ).round(2).reset_index()
    top_ben.columns = ["beneficiary", "retired_mt"]
    top_ben.to_csv(DATA / "top_beneficiaries.csv", index=False)

    # ---------- largest projects (with retirement progress) ----------
    top_proj = projects.nlargest(15, "issued")[
        ["name", "country", "category", "registry", "issued", "retired"]
    ].copy()
    top_proj["label"] = top_proj["category"].map(CATEGORY_LABELS).fillna(top_proj["category"])
    top_proj["issued_mt"] = (top_proj["issued"] / 1e6).round(1)
    top_proj["retired_pct"] = (top_proj["retired"] / top_proj["issued"]).round(3)
    top_proj[["name", "country", "label", "issued_mt", "retired_pct"]].to_csv(
        DATA / "top_projects.csv", index=False
    )

    print("Wrote artifacts:")
    for p in sorted(DATA.glob("*.csv")) + [DATA / "kpis.json"]:
        print(f"  {p.name}: {p.stat().st_size/1024:.1f} KB")
    print("\nKPIs:", json.dumps(kpis, indent=2))


if __name__ == "__main__":
    main()
