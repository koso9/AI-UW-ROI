import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Exports & Sharing", layout="wide")

st.title("Exports & Sharing")
st.caption("Demo utilities for executives and client sharing")

# -------------------------------------------------
# Load the same synthetic demo data used elsewhere
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def load_demo_data():
    return pd.read_csv("demo_data.csv") if False else None  # placeholder hook

st.subheader("Download Demo Data")

st.write(
    "This dashboard is currently running on a **synthetic, realistic dataset** "
    "used for demonstration and storytelling purposes."
)

# Example synthetic dataset for export
df = pd.DataFrame(
    {
        "loan_id": [f"L{100000+i}" for i in range(300)],
        "ai_ran": ["Yes"] * 150 + ["No"] * 150,
        "decision": ["Cleared"] * 80 + ["Conditional"] * 70 + ["Non-AI"] * 150,
        "days_to_ctc": list(range(30, 180))[:300],
        "funded": [True] * 120 + [False] * 180,
    }
)

# CSV export
csv_bytes = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Demo Dataset (CSV)",
    data=csv_bytes,
    file_name="ai_underwriting_demo_data.csv",
    mime="text/csv",
)

# Excel export
excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="Demo Data")

st.download_button(
    label="Download Demo Dataset (Excel)",
    data=excel_buffer.getvalue(),
    file_name="ai_underwriting_demo_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()

# -------------------------------------------------
# Sharing instructions
# -------------------------------------------------
st.subheader("How to View This Dashboard")

st.markdown(
    """
**Option 1 — View on Your Phone (Local):**
- Make sure your phone and laptop are on the same Wi-Fi
- Use the **Network URL** shown when Streamlit runs  
  (example: `http://192.168.x.x:8501`)

**Option 2 — Shareable Link (Recommended):**
- This app can be published to Streamlit Cloud
- Executives can access it with **no login and no uploads**
"""
)

st.subheader("Publishing Checklist (Streamlit Community Cloud)")

