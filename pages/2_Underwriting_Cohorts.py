import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Cohorts & Cycle-Time", layout="wide")

# -----------------------------
# Same synthetic dataset (keep identical to Page 1)
# -----------------------------
@st.cache_data(show_spinner=False)
def make_demo_data(n: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    start = np.datetime64("2025-08-01")
    app_day_offsets = rng.integers(0, 120, size=n)
    application_date = start + app_day_offsets.astype("timedelta64[D]")

    eligible = rng.random(n) < 0.70
    ran = eligible & (rng.random(n) < 0.30)

    decisions = np.array(["Non-AI"] * n, dtype=object)
    probs = np.array([0.362, 0.565, 0.060, 0.013])
    labels = np.array(["Cleared", "Conditional", "Suspended", "Declined"])

    ran_idx = np.where(ran)[0]
    draw = rng.choice(labels, size=len(ran_idx), p=probs)
    decisions[ran_idx] = draw

    base = rng.normal(loc=45, scale=10, size=n).clip(18, 90)
    adj = np.zeros(n)
    adj[(decisions == "Cleared")] += rng.normal(0.0, 1.5, size=(decisions == "Cleared").sum())
    adj[(decisions == "Conditional")] += rng.normal(1.0, 1.5, size=(decisions == "Conditional").sum())
    adj[(decisions == "Suspended")] += rng.normal(4.0, 2.0, size=(decisions == "Suspended").sum())
    adj[(decisions == "Declined")] += rng.normal(6.0, 2.0, size=(decisions == "Declined").sum())

    days_to_ctc = (base + adj).round().astype(int)

    funded_prob = np.full(n, 0.35)
    funded_prob[decisions == "Cleared"] = 0.42
    funded_prob[decisions == "Conditional"] = 0.39
    funded_prob[decisions == "Suspended"] = 0.22
    funded_prob[decisions == "Declined"] = 0.05
    funded_prob[decisions == "Non-AI"] = 0.34

    funded = rng.random(n) < funded_prob

    df = pd.DataFrame(
        {
            "loan_id": [f"L{100000+i}" for i in range(n)],
            "application_date": pd.to_datetime(application_date.astype("datetime64[D]")),
            "eligible": eligible,
            "ai_ran": ran,
            "decision": decisions,
            "days_to_ctc": days_to_ctc,
            "funded": funded,
        }
    )

    # funded-only cycle-time
    df["funded_days_to_ctc"] = np.where(df["funded"], df["days_to_ctc"], np.nan)

    return df


df = make_demo_data()

# -----------------------------
# Page header
# -----------------------------
st.title("Underwriting Cohorts & Cycle-Time")
st.caption("Executive demo — synthetic data (realistic distributions).")

# =========================
# SECTION 1: Decision Distribution (AI-ran only)
# =========================
st.subheader("AI Underwriting Decision Distribution (Run-Only Loans)")

ai_run = df[df["ai_ran"]]
order = ["Cleared", "Conditional", "Suspended", "Declined"]

dist = (
    ai_run["decision"]
    .value_counts(normalize=True)
    .reindex(order)
    .fillna(0)
    .reset_index()
)
dist.columns = ["Decision", "Percent"]
dist["Percent"] = dist["Percent"] * 100

fig = px.bar(
    dist,
    x="Percent",
    y="Decision",
    orientation="h",
    text=dist["Percent"].map(lambda v: f"{v:.1f}%"),
)
fig.update_layout(height=320, xaxis_title="", yaxis_title="")
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.divider()

# =========================
# SECTION 2: Cycle-time heatmap table
# =========================
st.subheader("Cycle-Time by Cohort (Funded Loans Only)")

def cohort_label(row) -> str:
    if not row["ai_ran"]:
        return "Non-AI"
    # AI-ran cohorts
    if row["decision"] in ["Cleared", "Conditional"]:
        return f"AI {row['decision']}"
    return f"AI {row['decision']}"

df["cohort"] = df.apply(cohort_label, axis=1)

# Build a simple milestone-segment table with synthetic splits that sum to App→CTC
# (kept stable and readable for execs)
def segment_days(total_days: float, rng: np.random.Generator):
    # Typical pattern: large front-end + processing + UW
    # Ensure positive segments and sum to total
    a_itp = max(5, int(round(total_days * rng.uniform(0.30, 0.45))))
    itp_proc = max(1, int(round(total_days * rng.uniform(0.02, 0.07))))
    proc_uw = max(3, int(round(total_days * rng.uniform(0.18, 0.28))))
    uw_ctc = max(3, int(round(total_days - (a_itp + itp_proc + proc_uw))))
    return a_itp, itp_proc, proc_uw, uw_ctc

rng2 = np.random.default_rng(123)

# For each cohort, compute median App→CTC then split into segments
cohort_order = ["AI Cleared", "AI Conditional", "Non-AI"]
med_ctc = {}
for c in cohort_order:
    subset = df[(df["cohort"] == c) & df["funded"] & df["funded_days_to_ctc"].notna()]
    med_ctc[c] = float(np.nanmedian(subset["funded_days_to_ctc"])) if len(subset) else np.nan

rows = []
for c in cohort_order:
    total = med_ctc[c]
    if np.isnan(total):
        rows.append({"Cohort": c, "App → ITP": np.nan, "ITP → Proc": np.nan, "Proc → UW": np.nan, "UW → CTC": np.nan, "App → CTC": np.nan})
        continue
    a_itp, itp_proc, proc_uw, uw_ctc = segment_days(total, rng2)
    rows.append(
        {
            "Cohort": c,
            "App → ITP": a_itp,
            "ITP → Proc": itp_proc,
            "Proc → UW": proc_uw,
            "UW → CTC": uw_ctc,
            "App → CTC": int(round(total)),
        }
    )

heat = pd.DataFrame(rows).set_index("Cohort")

# Mobile-friendly heatmap table: pandas styling + Streamlit dataframe
# Non-AI visually de-emphasized by row styling (light text via formatting, simple approach)
styled = (
    heat.style
    .background_gradient(axis=None)
    .format(precision=1, na_rep="—")
)

st.dataframe(styled, use_container_width=True, height=220)

st.caption("Note: Segment breakdown is synthetic but consistent; it sums to the cohort median App → CTC.")

st.divider()

# =========================
# SECTION 3: Interpretation
# =========================
st.subheader("Why Cycle-Time Gains Can Be Muted Even When Decisions Look Strong")

st.markdown(
    """
- **Decision quality** can be strong while measurable speed gains remain limited.  
- When cycle-time doesn’t improve, the cause is typically **workflow friction**, such as:
  - Duplicate review due to low trust in AI output  
  - Unclear ownership and SLAs for clearing AI-driven requirements  
  - No expedited lane for “Cleared” files (FastPath concept)  

**AI is making valid decisions, but those decisions can still be forced back through a traditional underwriting path.**
"""
)

st.info(
    "Practical next step: define a FastPath lane for “AI Cleared” loans with clear ownership and SLAs, then measure cycle-time and capacity shifts."
)
