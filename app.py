"""Voluntary Carbon Market Analytics — a data-storytelling dashboard.

Built on the CarbonPlan OffsetsDB: ~11,700 carbon-offset projects and ~530k
credit transactions across seven registries. The raw data is pre-aggregated by
prep_data.py into small artifacts; this app turns them into an analytical
narrative about how the voluntary carbon market actually behaves.
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import branding

st.set_page_config(page_title="Voluntary Carbon Market Analytics",
                   page_icon=":material/eco:", layout="wide")
branding.inject()

DATA = Path(__file__).parent / "data"
ACCENT1, ACCENT2 = "#7b5cff", "#2fc8f5"
GRID = "rgba(255,255,255,0.07)"


@st.cache_data
def load():
    kpis = json.loads((DATA / "kpis.json").read_text())
    return {
        "kpis": kpis,
        "flow": pd.read_csv(DATA / "flow_by_year.csv"),
        "category": pd.read_csv(DATA / "by_category.csv"),
        "country": pd.read_csv(DATA / "by_country.csv"),
        "registry": pd.read_csv(DATA / "by_registry.csv"),
        "beneficiaries": pd.read_csv(DATA / "top_beneficiaries.csv"),
        "projects": pd.read_csv(DATA / "top_projects.csv"),
    }


D = load()
K = D["kpis"]


def style(fig, height=380, legend=True):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#cfcfd6", "family": "Inter"},
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0,
                    bgcolor="rgba(0,0,0,0)") if legend else None,
        showlegend=legend,
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True)
    return fig


def insight(text):
    st.markdown(
        f'<div style="border-left:3px solid {ACCENT2};background:rgba(47,200,245,0.06);'
        f'padding:12px 16px;border-radius:0 10px 10px 0;margin:6px 0 14px;'
        f'color:#dcdce2;font-size:0.95rem"><b style="color:{ACCENT2}">What stands out — </b>'
        f'{text}</div>',
        unsafe_allow_html=True,
    )


# ---------------- header ----------------

branding.eyebrow("ESG · Carbon Markets · Data Storytelling")
st.title("The Voluntary Carbon Market, in Numbers")
st.caption(
    "Every carbon credit is a claim that one tonne of CO₂ was avoided or removed. "
    "This dashboard interrogates ~11,700 projects and ~530,000 credit transactions "
    "to ask a simple question: does the market behave the way its buyers assume?"
)

c = st.columns(5)
c[0].metric("Projects", f"{K['n_projects']:,}")
c[1].metric("Credits issued", f"{K['issued_mt']/1000:.2f} Gt")
c[2].metric("Credits retired", f"{K['retired_mt']/1000:.2f} Gt")
c[3].metric("Retirement rate", f"{K['retirement_rate']:.0%}")
c[4].metric("Unretired surplus", f"{K['surplus_mt']/1000:.2f} Gt")

tab_market, tab_supply, tab_integrity, tab_how = st.tabs(
    ["Market over time", "What & where", "Market integrity", "How it's built"]
)

# ================= TAB 1: market over time =================

with tab_market:
    st.subheader("Issuance has outpaced retirement every single year")
    flow = D["flow"]
    fig = go.Figure()
    fig.add_bar(x=flow["year"], y=flow["issuance"], name="Issued",
                marker_color=ACCENT1)
    fig.add_bar(x=flow["year"], y=flow["retirement"], name="Retired",
                marker_color=ACCENT2)
    fig.update_layout(barmode="group", yaxis_title="Million tonnes CO₂e")
    st.plotly_chart(style(fig), use_container_width=True)
    insight(
        "In no year has retirement (credits actually used against an emissions "
        "claim) caught up with issuance. The gap compounds into today's "
        f"<b>{K['surplus_mt']/1000:.2f} Gt unretired surplus</b> — credits sitting "
        "in accounts, unused. Issuance peaked in 2022 at ~342 Mt; retirements "
        "peaked a year earlier and then cooled as press scrutiny and integrity "
        "concerns hit demand through 2023–24."
    )

    cum = flow.copy()
    cum["surplus"] = (cum["issuance"] - cum["retirement"]).cumsum()
    fig2 = go.Figure()
    fig2.add_scatter(x=cum["year"], y=cum["surplus"], fill="tozeroy",
                     line=dict(color=ACCENT1, width=2), name="Cumulative surplus")
    fig2.update_layout(yaxis_title="Cumulative unretired credits (Mt CO₂e)")
    st.plotly_chart(style(fig2, height=300, legend=False), use_container_width=True)

# ================= TAB 2: what & where =================

with tab_supply:
    left, right = st.columns(2, gap="large")

    with left:
        st.subheader("What kind of credits")
        cat = D["category"].sort_values("issued_mt", ascending=True)
        fig = go.Figure(go.Bar(
            x=cat["issued_mt"], y=cat["label"], orientation="h",
            marker_color=ACCENT1, name="Issued",
        ))
        fig.update_layout(xaxis_title="Million tonnes CO₂e issued")
        st.plotly_chart(style(fig, height=420, legend=False), use_container_width=True)

    with right:
        st.subheader("Where they come from")
        country = D["country"].head(12).sort_values("issued_mt", ascending=True)
        fig = go.Figure(go.Bar(
            x=country["issued_mt"], y=country["country"], orientation="h",
            marker_color=ACCENT2, name="Issued",
        ))
        fig.update_layout(xaxis_title="Million tonnes CO₂e issued")
        st.plotly_chart(style(fig, height=420, legend=False), use_container_width=True)

    insight(
        "Two project types — forestry &amp; land use and renewable energy — account "
        "for roughly two-thirds of all credits ever issued. Both are heavily "
        "debated: forestry for measurement and permanence, renewables for "
        "additionality (would the wind farm have been built anyway?). Issuance is "
        "concentrated in a handful of host countries (the US, India, China, Brazil), "
        "while engineered carbon <i>removal</i> — biomass, mineralization, direct air "
        "capture — is still under 0.3 Mt combined, a rounding error against the "
        f"{K['issued_mt']/1000:.1f} Gt legacy market."
    )

    st.subheader("Who runs the registries")
    reg = D["registry"]
    fig = go.Figure()
    fig.add_bar(x=reg["label"], y=reg["issued_mt"], name="Issued", marker_color=ACCENT1)
    fig.add_bar(x=reg["label"], y=reg["retired_mt"], name="Retired", marker_color=ACCENT2)
    fig.update_layout(barmode="group", yaxis_title="Million tonnes CO₂e")
    st.plotly_chart(style(fig, height=340), use_container_width=True)
    insight(
        "Verra alone has issued more than half of all voluntary credits. Registry "
        "concentration matters: a methodology decision at one standard-setter moves "
        "the entire market."
    )

# ================= TAB 3: market integrity =================

with tab_integrity:
    st.subheader("How much of each credit type actually gets used")
    cat = D["category"]
    cat = cat[cat["issued_mt"] >= 1].dropna(subset=["retirement_rate"])
    cat = cat.sort_values("retirement_rate")
    colors = [ACCENT2 if r >= K["retirement_rate"] else "#ff7a59"
              for r in cat["retirement_rate"]]
    fig = go.Figure(go.Bar(
        x=cat["retirement_rate"] * 100, y=cat["label"], orientation="h",
        marker_color=colors,
        text=[f"{r:.0%}" for r in cat["retirement_rate"]], textposition="outside",
    ))
    fig.add_vline(x=K["retirement_rate"] * 100, line_dash="dash",
                  line_color="#cfcfd6",
                  annotation_text=f"market average {K['retirement_rate']:.0%}",
                  annotation_position="bottom right",
                  annotation_font_color="#cfcfd6")
    fig.update_layout(
        xaxis_title="Share of issued credits that have been retired (%)",
        xaxis_range=[0, 78],
    )
    st.plotly_chart(style(fig, height=400, legend=False), use_container_width=True)
    insight(
        "Retirement rate is a crude proxy for credit quality and demand: credit "
        "types buyers trust get used, the rest accumulate. Agriculture and the "
        "unclassified bucket lag the market average, while fuel-switching clears "
        "fastest. The reading is imperfect — recent issuances haven't had time to "
        "retire — but the persistent overhang is real, and it is the empirical core "
        "of the carbon-credit-quality debate my research sits in."
    )

    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader("Who is retiring the most credits")
        ben = D["beneficiaries"].head(12).sort_values("retired_mt", ascending=True)
        fig = go.Figure(go.Bar(
            x=ben["retired_mt"], y=ben["beneficiary"], orientation="h",
            marker_color=ACCENT1,
        ))
        fig.update_layout(xaxis_title="Million tonnes CO₂e retired")
        st.plotly_chart(style(fig, height=400, legend=False), use_container_width=True)
    with right:
        st.subheader("Largest projects")
        proj = D["projects"].head(8).copy()
        proj["Retired"] = (proj["retired_pct"] * 100).round(0).astype(int).astype(str) + "%"
        proj["Issued"] = proj["issued_mt"].astype(str) + " Mt"
        st.dataframe(
            proj[["name", "country", "Issued", "Retired"]].rename(
                columns={"name": "Project", "country": "Country"}),
            hide_index=True, use_container_width=True, height=400,
        )

    insight(
        "Oil majors and airlines dominate retirements — Shell and Eni alone account "
        "for tens of megatonnes. One name on the leaderboard, Toucan, is a crypto "
        "bridge rather than an end buyer, a reminder that a retirement record is not "
        "always a corporate climate claim. <b>Data-quality note:</b> the registries' "
        "free-text beneficiary fields needed cleaning — “Delta Air Lines” "
        "and “Delta Airlines” arrive as separate entities and were merged "
        "here; many smaller buyers remain un-harmonised. Honest aggregates require "
        "saying so."
    )

# ================= TAB 4: how it's built =================

with tab_how:
    st.subheader("From a 65 MB registry dump to a dashboard that loads instantly")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1:
        branding.step(1, "Source",
                      "CarbonPlan OffsetsDB — a harmonised snapshot of seven "
                      "voluntary registries (Verra, Gold Standard, ACR, CAR, "
                      "Cercarbono, ART, Isometric). ~530k credit transactions.")
    with c2:
        branding.step(2, "Aggregate once",
                      "prep_data.py downloads the raw archive and reduces it to a "
                      "handful of small CSVs — flows by year, by category, by "
                      "country, by registry, top buyers. Each under 2 KB.")
    with c3:
        branding.step(3, "Serve",
                      "The app reads only those artifacts, so it loads instantly "
                      "and deploys on free hosting. Heavy work stays in the "
                      "reproducible pipeline, not the request path.")

    st.write("")
    st.subheader("Read the code")
    st.markdown(
        "Two files, cleanly separated — the analysis pipeline and the presentation.\n\n"
        "| Module | Responsibility |\n"
        "|---|---|\n"
        "| [`prep_data.py`](https://github.com/drishtantleuva/carbon-market-analytics/blob/main/prep_data.py) | Downloads OffsetsDB, harmonises registry labels and beneficiary names, aggregates ~530k transactions into the small artifacts the dashboard reads |\n"
        "| [`app.py`](https://github.com/drishtantleuva/carbon-market-analytics/blob/main/app.py) | The narrative and charts you are reading now |\n"
    )

    st.write("")
    st.subheader("Honest caveats")
    with st.expander("Retirement rate is a proxy, not a verdict"):
        st.markdown(
            "A low retirement rate can mean weak demand, low buyer trust, or simply "
            "that credits were issued too recently to have been used. It is a useful "
            "lens on market behaviour, not a quality score for any individual project."
        )
    with st.expander("Registry data is self-reported and uneven"):
        st.markdown(
            "Project categories, country tags and beneficiary names come straight "
            "from the registries in inconsistent formats. CarbonPlan harmonises much "
            "of it; this project harmonises a little more (registry and category "
            "labels, the Delta duplication). Residual noise remains and is disclosed "
            "rather than hidden."
        )
    with st.expander("Snapshot, not a live feed"):
        st.markdown(
            f"Figures reflect the OffsetsDB snapshot loaded in {K['snapshot']}. "
            "Re-running `prep_data.py --download` refreshes every number and chart "
            "from the latest published data."
        )

    st.caption(
        "Data: [CarbonPlan OffsetsDB](https://carbonplan.org/research/offsets-db) — "
        "compiled from ACR, ART, Cercarbono, CAR, Gold Standard, Isometric and Verra. "
        "Factual registry data; CarbonPlan claims no copyright. Provided as-is."
    )

branding.footer("carbon-market-analytics")
