import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="AI Underwriting Performance", layout="wide")

# -----------------------------
# Synthetic demo dataset (v1)
# -----------------------------
@st.cache_data(show_spinner=False)
def make_demo_data(n: int = 800, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # Base dates
    start = np.datetime64("2025-08-01")
    app_day_offsets = rng.integers(0, 120, size=n)
    application_date = start + app_day_offsets.astype("timedelta64[D]")

    # Eligibility + adoption
    eligible = rng.random(n) < 0.70  # 70% eligible
    ran = eligible & (rng.random(n) < 0.30)  # 30% of eligible ran

    # Decision distribution (only meaningful if ran)
    # Target dist: Cleared 36.2, Conditional 56.5, Suspended 6.0, Declined 1.3
    decisions = np.array(["Non-AI"] * n, dtype=object)
    probs = np.array([0.362, 0.565, 0.060, 0.013])
    labels = np.array(["Cleared", "Conditional", "Suspended", "Declined"])

    ran_idx = np.where(ran)[0]
    draw = rng.choice(labels, size=len(ran_idx), p=probs)
    decisions[ran_idx] = draw

    # Cycle time (days to close / CTC)
    # Base non-AI median ~45, AI cohorts similar for early deployment (workflow friction)
    base = rng.normal(loc=45, scale=10, size=n).clip(18, 90)

    # Small cohort tweaks (kept small intentionally to reflect "friction blocks gains")
    adj = np.zeros(n)
    adj[(decisions == "Cleared")] += rng.normal(0.0, 1.5, size=(decisions == "Cleared").sum())
    adj[(decisions == "Conditional")] += rng.normal(1.0, 1.5, size=(decisions == "Conditional").sum())
    adj[(decisions == "Suspended")] += rng.normal(4.0, 2.0, size=(decisions == "Suspended").sum())
    adj[(decisions == "Declined")] += rng.normal(6.0, 2.0, size=(decisions == "Declined").sum())

    days_to_ctc = (base + adj).round().astype(int)

    # Pull-through (funded rate)
    # Make AI-ran slightly higher than non-AI but not huge
    funded_prob = np.full(n, 0.35)  # baseline
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

    # For exec display, treat cycle-time based on funded loans only
    df["funded_days_to_ctc"] = np.where(df["funded"], df["days_to_ctc"], np.nan)

    return df


df = make_demo_data()

# -----------------------------
# Page header
# -----------------------------
st.title("AI Underwriting Performance")
st.caption("Executive demo — synthetic data (realistic distributions).")

# -----------------------------
# KPI row
# -----------------------------
ai_run = df[df["ai_ran"]]
non_ai = df[~df["ai_ran"]]
eligible = df[df["eligible"]]

adoption = float(eligible["ai_ran"].mean()) if len(eligible) else 0.0
eligible_not_run = int((eligible["ai_ran"] == False).sum()) if len(eligible) else 0

pull_ai = float(ai_run["funded"].mean()) if len(ai_run) else 0.0
pull_non = float(non_ai["funded"].mean()) if len(non_ai) else 0.0

med_ai = float(np.nanmedian(ai_run["funded_days_to_ctc"])) if len(ai_run) else np.nan
med_non = float(np.nanmedian(non_ai["funded_days_to_ctc"])) if len(non_ai) else np.nan

c1, c2, c3 = st.columns(3)

with c1:
    if np.isnan(med_ai) or np.isnan(med_non):
        st.metric("Cycle-time (Median, Funded)", "—")
    else:
        st.metric(
            "Cycle-time (Median, Funded)",
            f"{int(med_ai)} days (AI-ran)",
            f"{int(med_ai - med_non)} vs Non-AI",
            delta_color="inverse",
        )

with c2:
    st.metric(
        "Pull-through (Funded Rate)",
        f"{pull_ai*100:.1f}% (AI-ran)",
        f"{(pull_ai - pull_non)*100:.1f}% vs Non-AI",
        delta_color="inverse",
    )

with c3:
    st.metric(
        "AI Adoption (Eligible → Ran)",
        f"{adoption*100:.0f}%",
        f"{eligible_not_run:,} eligible not run",
        delta_color="off",
    )

st.divider()

# -----------------------------
# Decision distribution (AI-ran only)
# -----------------------------
st.subheader("AI Underwriting Decision Distribution (Run-Only Loans)")

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
fig.update_layout(height=340, xaxis_title="", yaxis_title="")
fig.update_traces(textposition="outside")
st.plotly_chart(fig, use_container_width=True)

st.write(
    "This distribution is typical of early AI underwriting deployments. "
    "In mature workflows, **Cleared** rates tend to rise meaningfully once readiness, ownership, and routing are established."
)

st.divider()

# -----------------------------
# Simple comparison chart (Cycle-time + Pull-through)
# -----------------------------
st.subheader("Performance Snapshot (AI-ran vs Non-AI)")

snap = pd.DataFrame(
    [
        {"Metric": "Cycle-time (Median, Funded)", "Cohort": "AI-ran", "Value": med_ai},
        {"Metric": "Cycle-time (Median, Funded)", "Cohort": "Non-AI", "Value": med_non},
        {"Metric": "Pull-through (%)", "Cohort": "AI-ran", "Value": pull_ai * 100},
        {"Metric": "Pull-through (%)", "Cohort": "Non-AI", "Value": pull_non * 100},
    ]
)

snap["Value"] = snap["Value"].round(1)

fig2 = px.bar(snap, x="Metric", y="Value", color="Cohort", barmode="group", text_auto=True)
fig2.update_layout(height=380, legend_title_text="", yaxis_title="")
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# Executive takeaway
# -----------------------------
st.subheader("Executive Takeaway")
st.write(
    "AI decision quality can be strong while measurable speed gains remain muted. "
    "When cycle-time doesn’t improve, the cause is usually workflow friction: duplicate review, unclear ownership, and lack of a FastPath lane."
)
