import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import os
API_TOKEN = os.getenv("API_TOKEN")

# -------------------------------
# ⚙️ CONFIGURATION
# -------------------------------
BASE_ID = "mu16td4m2vofa0u"  # ✅ Table ID
VIEW_ID = "vwqd3w3dqtpllu75"  # ✅ View ID
BASE_URL = "https://app.nocodb.com"  # ✅ Hosted NocoDB domain


# -------------------------------
# 🚀 FUNCTIONS
# -------------------------------
def submit_data(base_id, data):
    """Send form data to your NocoDB table"""
    headers = {
        "accept": "application/json",
        "xc-token": API_TOKEN,
        "Content-Type": "application/json"
    }
    url = f"{BASE_URL}/api/v2/tables/{base_id}/records?viewId={VIEW_ID}"
    response = requests.post(url, json=data, headers=headers)
    return response.status_code, response.text


def get_records(base_id):
    """Fetch all records from your NocoDB table"""
    headers = {
        "accept": "application/json",
        "xc-token": API_TOKEN
    }
    url = f"{BASE_URL}/api/v2/tables/{base_id}/records?viewId={VIEW_ID}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get("list", [])
        return pd.DataFrame(data)
    else:
        st.error(f"❌ Failed to load records: {response.text}")
        return pd.DataFrame()


# -------------------------------
# 🧱 STREAMLIT FRONTEND
# -------------------------------
st.set_page_config(page_title="Kirkpatrick Assistant", page_icon="📋", layout="wide")

st.title("📋 Kirkpatrick Assistant — Level 1 Feedback")
st.write("Submit, view, and analyze participant feedback from NocoDB!")

tab1, tab2, tab3 = st.tabs(["📝 Submit Feedback", "📊 View Submissions", "📈 Analytics Dashboard"])

# -------------------------------
# 📝 TAB 1: SUBMIT FORM
# -------------------------------
with tab1:
    with st.form("feedback_form"):
        name = st.text_input("👤 Participant Name")
        satisfaction = st.slider("⭐ Satisfaction Score (1 = Poor, 5 = Excellent)", 1, 5, 3)
        comments = st.text_area("💬 Comments")

        submitted = st.form_submit_button("Submit Feedback")

    if submitted:
        feedback_data = {
            "participant_name": name,
            "satisfaction_score": satisfaction,
            "comments": comments
        }

        st.info("⏳ Submitting your feedback...")
        status_code, response_text = submit_data(BASE_ID, feedback_data)

        if status_code in (200, 201):
            st.success("✅ Feedback submitted successfully!")
        else:
            st.error(f"❌ Submission failed.\n\nResponse: {response_text}")

# -------------------------------
# 📊 TAB 2: VIEW SUBMISSIONS + EXPORT
# -------------------------------
with tab2:
    st.subheader("📈 All Feedback Records")

    with st.expander("🔍 Filter Options"):
        min_score = st.slider("Minimum Satisfaction Score", 1, 5, 1)
        keyword = st.text_input("Search by Name or Comment")

    if st.button("🔄 Refresh Data"):
        df = get_records(BASE_ID)

        if not df.empty:
            df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")
            df = df[df["satisfaction_score"].fillna(0) >= min_score]

            if keyword.strip():
                keyword_lower = keyword.lower()
                df = df[
                    df["participant_name"].fillna("").str.lower().str.contains(keyword_lower)
                    | df["comments"].fillna("").str.lower().str.contains(keyword_lower)
                ]

            df = df[["participant_name", "satisfaction_score", "comments"]].rename(columns={
                "participant_name": "Participant Name",
                "satisfaction_score": "Satisfaction Score",
                "comments": "Comments"
            })

            st.dataframe(df, use_container_width=True)

            # ✅ Export buttons
            st.markdown("### ⬇️ Export Data")
            csv = df.to_csv(index=False).encode("utf-8")
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_data = excel_buffer.getvalue()

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv,
                    file_name="feedback_records.csv",
                    mime="text/csv"
                )
            with col2:
                st.download_button(
                    label="📊 Download as Excel",
                    data=excel_data,
                    file_name="feedback_records.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        else:
            st.warning("No records available yet.")

# -------------------------------
# 📈 TAB 3: ANALYTICS DASHBOARD
# -------------------------------
with tab3:
    st.subheader("📊 Training Feedback Analytics")
    df = get_records(BASE_ID)

    if df.empty:
        st.warning("No data available yet.")
    else:
        df["satisfaction_score"] = pd.to_numeric(df["satisfaction_score"], errors="coerce")

        # --- Average satisfaction
        avg_score = df["satisfaction_score"].mean()
        st.metric("Average Satisfaction Score", f"{avg_score:.2f} / 5")

        # --- Chart: distribution
        st.write("### ⭐ Distribution of Satisfaction Scores")
        counts = df["satisfaction_score"].value_counts().sort_index()

        fig, ax = plt.subplots()
        ax.bar(counts.index, counts.values)
        ax.set_xlabel("Satisfaction Score")
        ax.set_ylabel("Number of Participants")
        ax.set_title("Feedback Distribution")
        st.pyplot(fig)

        # --- Comments preview
        st.write("### 💬 Sample Feedback Comments")
        for _, row in df.dropna(subset=["comments"]).head(5).iterrows():
            st.markdown(f"**{row['participant_name']}** — ⭐ {row['satisfaction_score']}<br>{row['comments']}", unsafe_allow_html=True)
