# Streamlit Ingestion/Upload View

import streamlit as st

def render_upload():
    st.header("Upload Case Comments Dataset")
    st.file_uploader("Upload raw CSV file", type=["csv"])
