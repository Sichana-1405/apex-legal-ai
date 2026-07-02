# Main Streamlit entrance script

import streamlit as st

st.set_page_config(
    page_title="Apex Legal AI",
    page_icon="⚖️",
    layout="wide",
)

st.title("Apex Legal AI - Harassment Investigation Workspace")

# Navigation Routing & Sidebar
page = st.sidebar.selectbox("Navigation", ["Overview & Upload", "Analysis Dashboard", "Case Report & Approval"])

st.info("System initialized. Upload a case CSV file in the 'Overview & Upload' page to begin.")
