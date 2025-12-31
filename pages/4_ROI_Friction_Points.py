import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="ROI Friction Points", layout="wide")

# -----------------------------
# Synthetic diagnostics (intentionally simple + directional)
# -----------------------------
@st.cache_data(show_spinner=False)
def make_friction_data(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    data = [
        {
            "Friction Area": "Duplicate Manual Review",
            "Description": "AI output is re-reviewed manually due to low trust or unclear policy.",
            "Impact": "Adds days and underwriter touches",
            "Estimated Frequency": rng.uniform(0.45, 0.65),
        },
        {
            "Friction Area": "Unclear Ownership / SLAs",
            "Description": "No defined owner for clearing AI-driven requirements.",
            "Impact": "Files stall between teams",
            "Estimated Frequency": rng.uniform(0.35, 0.55),
        },
        {
            "Friction Area": "No FastPath Lane",
            "Description": "AI-Cleared files routed through standard underwriting queues.",
            "Impact": "Cleared files lose time advantage",
            "Estimated Frequency": rng.uniform(0.50, 0.70),
        },
        {
            "Friction Area": "Late AI Execution",
            "Description": "AI runs after processing instead of earlier in the lifecycle.",
            "Impact": "Limits downstream benefit",
            "Estimated Frequency": rng.uniform(0.25, 0.45),
        },
    ]

    df = pd.DataFrame(data)
    df["Estimated Frequency (%)"] = (df["Estimated Frequency"] * 100).round(0)
    return df.drop(columns=["Estimated Frequency"])


friction_df = make_friction_data()

# -----------------------------
# Page header
# -----------------------------
st.title("Where ROI Breaks")
st.caption("Executive diagnostic — why strong AI decisions don’t always translate into faster or cheaper outcomes.")

st.write(
    """
This page explains a common pattern seen in early AI underwriting deployments:
**decision quality improves first; measurable ROI follows only after workflow alignment.**
"""
)

st.divider()

# -----------------------------
# Friction frequency chart
# -----------------------------
st.subheader("Most Common Barriers to Realizing ROI")

fig = px.bar(
    friction_df,
    x="Estimated Frequency (%)",
    y="Friction Area",
    orientation="h",
    text=friction_df["Estimated Frequency (%)"].map(lambda v: f"{int(v)}%"),
)

fig.update_layout(
    height=340,
    xaxis_title="Estimated % of Files Affected",
    yaxis_title="",
)
fig.update_traces(textposition="outside")

st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------
# Diagnostic table
# -----------------------------
st.subheader("What’s Happening Operationally")

display_df = friction_df[
    ["Friction Area", "Description", "Impact"]
]

st.dataframe(display_df, use_container_width=True, hide_index=True)

st.divider()

# -----------------------------
# Executive interpretation
# -----------------------------
st.subheader("Executive Interpretation")

st.markdown(
    """
- **AI underwriting can be accurate and still fail to deliver ROI**.
- The gap is rarely the model — it is the **operating system around the model**.
- Without explicit workflow changes, AI decisions are forced back into legacy paths.
"""
)

st.info(
    "Key insight: ROI unlocks when leadership treats AI underwriting as a **workflow redesign problem**, not just a technology install."
)

st.divider()

# -----------------------------
# Bridge to action (Page 5 setup)
# -----------------------------
st.subheader("What This Sets Up")

st.markdown(
    """
The next step is not more reporting.

It is to:
- Define **ownership** for AI-driven actions
- Protect AI-Cleared files with a **FastPath**
- Align incentives and SLAs to the new decision flow

These changes are measurable, repeatable, and form the foundation for sustained ROI.
"""
)
