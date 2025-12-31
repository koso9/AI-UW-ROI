import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Adoption & Alignment", layout="wide")

# -----------------------------
# Synthetic demo data (role + branch adoption quality)
# -----------------------------
@st.cache_data(show_spinner=False)
def make_adoption_alignment_data(seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)

    # Branches (anonymized but realistic labels)
    branches = ["Branch A", "Branch B", "Branch C", "Branch D", "Branch E", "Branch F", "Branch G", "Branch H"]

    # Roles aligned to your operating model
    roles = ["LOA", "Processing", "Underwriting"]

    # Targets / expected bands (demo-only, directional)
    target_band = {
        "LOA": (45, 70),          # should be high-ish in a mature model
        "Processing": (25, 50),   # exception + readiness support
        "Underwriting": (15, 35), # should trend down as FastPath matures
    }

    # Role-level adoption + quality metrics per branch
    rows = []
    for b in branches:
        volume = int(rng.integers(40, 140))

        # Branch-level "workflow maturity" latent factor
        maturity = rng.uniform(0.2, 0.9)

        for r in roles:
            # Adoption rate varies by maturity and role
            base = {"LOA": 0.55, "Processing": 0.35, "Underwriting": 0.25}[r]
            adoption = np.clip(base + (maturity - 0.5) * 0.35 + rng.normal(0, 0.06), 0.05, 0.95)

            # Adoption quality split:
            # Proper initial run + appropriate rerun + late/missed
            # More mature branches have better quality.
            proper_initial = np.clip(0.55 + (maturity - 0.5) * 0.35 + rng.normal(0, 0.06), 0.15, 0.95)
            appropriate_rerun = np.clip(0.25 + (maturity - 0.5) * 0.25 + rng.normal(0, 0.05), 0.05, 0.70)
            late_or_missed = np.clip(1.0 - (proper_initial * 0.60 + appropriate_rerun * 0.60), 0.05, 0.75)

            # Normalize quality shares to sum to 1.0
            total = proper_initial + appropriate_rerun + late_or_missed
            proper_initial /= total
            appropriate_rerun /= total
            late_or_missed /= total

            rows.append(
                {
                    "Branch": b,
                    "Role": r,
                    "Branch Volume": volume,
                    "AI Utilization %": adoption * 100,
                    "Proper Initial Run %": proper_initial * 100,
                    "Appropriate Re-Run %": appropriate_rerun * 100,
                    "Late / Missed Re-Run %": late_or_missed * 100,
                    "Target Low": target_band[r][0],
                    "Target High": target_band[r][1],
                    "Maturity (hidden)": maturity,
                }
            )

    role_branch = pd.DataFrame(rows)

    # Branch-level overlay data: adoption vs fast-track eligibility proxy
    # We'll use "AI Cleared rate proxy" derived from maturity + noise
    overlay = (
        role_branch.groupby(["Branch"], as_index=False)
        .agg(
            {
                "Branch Volume": "max",
                "AI Utilization %": "mean",
                "Maturity (hidden)": "max",
            }
        )
    )

    overlay["FastPath Eligible % (proxy)"] = (
        np.clip(35 + (overlay["Maturity (hidden)"] - 0.5) * 45 + rng.normal(0, 6, size=len(overlay)), 10, 75)
    )

    return role_branch.drop(columns=["Maturity (hidden)"]), overlay.drop(columns=["Maturity (hidden)"])


role_branch_df, overlay_df = make_adoption_alignment_data()

# -----------------------------
# Page header
# -----------------------------
st.title("Adoption & Capability Alignment")
st.caption("Executive diagnostic — adoption is not just frequency; it’s timing, ownership, and consistency.")

st.write(
    "This page isolates a common reason ROI varies across branches: "
    "**the operating model is not consistently executed by role.**"
)

st.divider()

# =========================
# SECTION 1: Utilization by role with target bands
# =========================
st.subheader("AI Utilization by Role (with Expected Ranges)")

role_summary = (
    role_branch_df.groupby("Role", as_index=False)["AI Utilization %"]
    .mean()
    .sort_values("AI Utilization %", ascending=False)
)

# Add target bands for display
targets = (
    role_branch_df.groupby("Role", as_index=False)[["Target Low", "Target High"]]
    .first()
)
role_summary = role_summary.merge(targets, on="Role", how="left")

fig1 = px.bar(
    role_summary,
    x="AI Utilization %",
    y="Role",
    orientation="h",
    text=role_summary["AI Utilization %"].map(lambda v: f"{v:.0f}%"),
)
fig1.update_layout(height=320, xaxis_title="", yaxis_title="")
fig1.update_traces(textposition="outside")

# Add target band shapes
for _, r in role_summary.iterrows():
    fig1.add_shape(
        type="rect",
        x0=r["Target Low"],
        x1=r["Target High"],
        y0=role_summary.index[role_summary["Role"] == r["Role"]][0] - 0.35,
        y1=role_summary.index[role_summary["Role"] == r["Role"]][0] + 0.35,
        xref="x",
        yref="y",
        line=dict(width=0),
        fillcolor="rgba(0,0,0,0.08)",
        layer="below",
    )

st.plotly_chart(fig1, use_container_width=True)

st.caption("Shaded bands represent directional expected ranges in a mature operating model (demo concept).")

st.divider()

# =========================
# SECTION 2: Branch adoption vs capability mix (overlay)
# =========================
st.subheader("Branch Adoption vs Capability Mix")

fig2 = px.scatter(
    overlay_df,
    x="AI Utilization %",
    y="FastPath Eligible % (proxy)",
    size="Branch Volume",
    hover_name="Branch",
)
fig2.update_layout(height=380, xaxis_title="AI Utilization (%)", yaxis_title="FastPath Eligible (%) — proxy")
st.plotly_chart(fig2, use_container_width=True)

st.info(
    "Branches with similar volume can show very different outcomes based on **role alignment and workflow discipline**, "
    "not effort or staffing alone."
)

st.divider()

# =========================
# SECTION 3: Adoption quality by role (stacked)
# =========================
st.subheader("Adoption Quality by Role (Timing & Re-Run Discipline)")

quality = (
    role_branch_df.groupby("Role", as_index=False)[
        ["Proper Initial Run %", "Appropriate Re-Run %", "Late / Missed Re-Run %"]
    ].mean()
)

quality_long = quality.melt(
    id_vars=["Role"],
    var_name="Quality Component",
    value_name="Percent",
)

fig3 = px.bar(
    quality_long,
    x="Percent",
    y="Role",
    color="Quality Component",
    orientation="h",
    barmode="stack",
    text=quality_long["Percent"].map(lambda v: f"{v:.0f}%"),
)
fig3.update_layout(height=360, xaxis_title="", yaxis_title="", legend_title_text="")
fig3.update_traces(textposition="inside")
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# =========================
# Executive interpretation
# =========================
st.subheader("Executive Interpretation")

st.markdown(
    """
- The organization does not have a *technology* problem.  
- It has a **role alignment and expectation clarity** problem.  
- The fastest ROI typically comes from lifting the bottom half of adopters and tightening re-run discipline — not from changing the model.
"""
)

st.info(
    "Practical next step: set role-level expectations (ownership + SLAs), protect AI-Cleared files with an expedited lane, "
    "and measure adoption quality (timing + re-run cadence) alongside ROI."
)
