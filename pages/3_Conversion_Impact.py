import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Conversion Impact", layout="wide")

# -----------------------------
# Synthetic demo dataset (MUST match Pages 1–2)
# -----------------------------
@st.cache_data(show_spinner=False)
def make_demo_data(n: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    eligible = rng.random(n) < 0.70
    ran = eligible & (rng.random(n) < 0.30)

    decisions = np.array(["Non-AI"] * n, dtype=object)
    probs = np.array([0.362, 0.565, 0.060, 0.013])
    labels = np.array(["Cleared", "Conditional", "Suspended", "Declined"])

    ran_idx = np.where(ran)[0]
    decisions[ran_idx] = rng.choice(labels, size=len(ran_idx), p=probs)

    funded_prob = np.full(n, 0.35)
    funded_prob[decisions == "Cleared"] = 0.42
    funded_prob[decisions == "Conditional"] = 0.39
    funded_prob[decisions == "Suspended"] = 0.22
    funded_prob[decisions == "Declined"] = 0.05
    funded_prob[decisions == "Non-AI"] = 0.34

    funded = rng.random(n) < funded_prob

    return pd.DataFrame(
        {
            "eligible": eligible,
            "ai_ran": ran,
            "decision": decisions,
            "funded": funded,
        }
    )

df = make_demo_data()

# -----------------------------
# Page header
# -----------------------------
st.title("Conversion & Pull-Through Impact")
st.caption("Executive demo — synthetic data (directional, CFO-relevant).")

# -----------------------------
# Cohort labeling
# -----------------------------
def cohort_label(row):
    if not row["ai_ran"]:
        return "Non-AI"
    return f"AI {row['decision']}"

df["cohort"] = df.apply(cohort_label, axis=1)

# Focus cohorts
cohort_order = ["AI Cleared", "AI Conditional", "AI Suspended", "AI Declined", "Non-AI"]

# -----------------------------
# Pull-through by cohort
# -----------------------------
pull = (
    df.groupby("cohort")["funded"]
    .mean()
    .reindex(cohort_order)
    .dropna()
    .reset_index()
)

pull["funded_rate"] = pull["funded"] * 100

fig = px.bar(
    pull,
    x="funded_rate",
    y="cohort",
    orientation="h",
    text=pull["funded_rate"].map(lambda v: f"{v:.1f}%"),
)

fig.update_layout(
    height=360,
    xaxis_title="Funded Rate (%)",
    yaxis_title="",
)
fig.update_traces(textposition="outside")

st.subheader("Pull-Through Rate by Underwriting Cohort")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# -----------------------------
# Funnel view (Applications → Funded)
# -----------------------------
st.subheader("Application-to-Funding Funnel (Directional)")

funnel_rows = []
for c in ["AI Cleared", "AI Conditional", "Non-AI"]:
    subset = df[df["cohort"] == c]
    funnel_rows.append(
        {
            "Cohort": c,
            "Applications": len(subset),
            "Funded": int(subset["funded"].sum()),
        }
    )

funnel = pd.DataFrame(funnel_rows)
funnel["Conversion %"] = (funnel["Funded"] / funnel["Applications"] * 100).round(1)

fig2 = px.bar(
    funnel,
    x="Cohort",
    y="Conversion %",
    text=funnel["Conversion %"].map(lambda v: f"{v:.1f}%"),
)

fig2.update_layout(height=320, yaxis_title="Funded Rate (%)")
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# -----------------------------
# CFO framing (ranges, not promises)
# -----------------------------
st.subheader("Why This Matters Financially")

st.markdown(
    """
- **Conversion lift compounds fast** at scale — even small improvements matter.
- AI-Cleared files consistently outperform Non-AI in funded outcomes.
- The largest gap is not decision accuracy — it is **operational follow-through**.
"""
)

st.info(
    "Directional takeaway: improving AI adoption and protecting AI-Cleared files from rework "
    "can drive measurable funded-volume lift without increasing application volume."
)

st.caption(
    "Financial impact intentionally shown as directional. Dollar modeling depends on lender margin, loan size, and product mix."
)
