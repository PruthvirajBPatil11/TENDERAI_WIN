"""
Criteria review page - review and edit extracted criteria.
"""

import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the criteria review page."""
    st.title("📋 Criteria Review")
    
    if "tender_id" not in st.session_state:
        st.warning("⚠️ Please upload a tender document first in the **Upload** page")
        return
    
    tender_id = st.session_state.tender_id
    st.write(f"**Current Tender ID:** `{tender_id}`")
    
    st.info("""
    Review the extracted criteria below. You can edit them before proceeding with evaluation.
    Click the **Confirm Criteria** button to save any changes.
    """)
    
    # Note: In a production system, you would fetch criteria from the database
    # For now, show a message
    st.subheader("Extracted Criteria")
    st.write("""
    This page allows you to review and edit criteria extracted from the tender.
    
    In the current implementation, criteria are automatically extracted and stored during tender upload.
    To view extracted criteria, go to the **Upload** page after processing a tender.
    
    **Future enhancement:** This page will allow editing of criteria thresholds, types, and requirements.
    """)
