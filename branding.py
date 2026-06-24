"""Visual identity for the Carbon Market Analytics dashboard.

Design language: warm editorial / data journalism. Parchment paper, a Fraunces
serif masthead, forest-green and clay accents — the look of an FT graphics piece
or an Our World in Data article, where the writing and the charts carry equal
weight.
"""

import streamlit as st

INK = "#2c2f28"
FOREST = "#1e6f52"
CLAY = "#c8851f"
MUTED = "#6b6d63"
PAPER = "#f4f1e8"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="st-"], [data-testid="stMarkdownContainer"], input, button, select {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
[data-testid="stAppViewContainer"] { background: #f4f1e8; }

h1 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 600 !important;
  font-size: 2.9rem !important;
  line-height: 1.05;
  letter-spacing: -0.015em;
  color: #23261f !important;
}
h2, h3 {
  font-family: 'Fraunces', Georgia, serif !important;
  font-weight: 600 !important;
  color: #23261f !important;
}

/* metric cards — like stat boxes in a print graphic, with a top accent rule */
[data-testid="stMetric"] {
  background: #fbf9f2;
  border: 1px solid #e0d9c6;
  border-top: 3px solid #1e6f52;
  border-radius: 4px;
  padding: 14px 18px;
}
[data-testid="stMetricLabel"] { color: #6b6d63 !important; }
[data-testid="stMetricValue"] {
  color: #23261f !important; font-family: 'Fraunces', serif; font-weight: 600;
}

[data-testid="stSidebar"] { background: #efeadd; border-right: 1px solid #ddd5c2; }

[data-testid="stTabs"] button[role="tab"] { font-weight: 600; color: #6b6d63; }
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] { color: #1e6f52; }
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }

div[data-testid="stExpander"] {
  border: 1px solid #e0d9c6; border-radius: 4px; background: #fbf9f2;
}
.stButton button {
  border-radius: 4px; border: 1px solid #c7bfa9; background: #fbf9f2; color: #1e6f52;
}
.stButton button:hover { border-color: #1e6f52; }

/* editorial masthead: a hairline rule above a letterspaced kicker */
.masthead-rule { height: 1px; background: #2c2f28; width: 100%; margin-bottom: 10px; opacity: 0.5; }
.eyebrow {
  text-transform: uppercase; letter-spacing: 0.2em;
  font-size: 0.72rem; color: #c8851f; font-weight: 600; margin-bottom: 4px;
}

.dl-step {
  background: #fbf9f2; border: 1px solid #e0d9c6; border-radius: 4px;
  padding: 18px; height: 100%;
}
.dl-step b { color: #1e6f52; font-family: 'Fraunces', serif; font-size: 1.05rem; }
.dl-step .n {
  display: inline-block; font-family: 'Fraunces', serif; font-size: 1.6rem;
  color: #c8851f; font-weight: 700; margin-bottom: 4px;
}

table { font-size: 0.92rem; }
a { color: #1e6f52; }
</style>
"""


def inject():
    st.markdown(CSS, unsafe_allow_html=True)


def eyebrow(text: str):
    st.markdown(
        f'<div class="masthead-rule"></div><p class="eyebrow">{text}</p>',
        unsafe_allow_html=True,
    )


def step(n, title, body):
    st.markdown(
        f'<div class="dl-step"><span class="n">{n:02d}</span><br/>'
        f'<b>{title}</b><br/><span style="color:#5c5e54;font-size:0.92rem">{body}</span></div>',
        unsafe_allow_html=True,
    )


def footer(repo: str):
    st.divider()
    st.markdown(
        f'<p style="color:#7a7c70;font-size:0.85rem">Built by '
        f'<a href="https://drishtantleuva.github.io" target="_blank">'
        f'<b style="font-family:\'Fraunces\',Georgia,serif">Drishtant Leuva</b></a> '
        f'— Data Scientist · Risk, ESG &amp; Explainable AI &nbsp;·&nbsp; '
        f'<a href="https://github.com/drishtantleuva/{repo}" target="_blank">Source on GitHub</a> '
        f'&nbsp;·&nbsp; <a href="https://www.linkedin.com/in/drishtant-leuva/" '
        f'target="_blank">LinkedIn</a></p>',
        unsafe_allow_html=True,
    )
