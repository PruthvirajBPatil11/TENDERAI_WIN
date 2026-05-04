"""
Streamlit multi-page application for TenderEval AI.
"""

import streamlit as st
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="TenderEval AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("TenderEval AI")
st.sidebar.write("Government Tender Evaluation Platform")

page = st.sidebar.radio(
    "Navigation",
    ["Home", "Upload", "Criteria Review", "Evaluation", "Report"],
    index=0
)

# Home page
if page == "Home":
    st.title("🏛️ TenderEval AI")
    st.write("""
    ### Government Tender Evaluation Platform
    
    This platform uses AI to automate and standardize the evaluation of government tender bids.
    
    **Key Features:**
    - 📄 Intelligent document ingestion (PDFs, scans, images, DOCX)
    - 🔍 Automatic criterion extraction from tender documents
    - 🤖 AI-powered eligibility matching using multiple evaluation methods
    - 📊 Explainable verdicts with confidence scores
    - 🔐 Immutable audit trail with SHA-256 hash chain
    - 📑 Professional PDF reports with detailed reasoning
    
    **Getting Started:**
    1. Go to **Upload** to add a tender document
    2. Upload bidder submission documents
    3. Run evaluation to get verdicts
    4. Review results and export reports
    """)
    
    st.info("""
    **System Status:** ✓ All services operational
    
    API: http://localhost:8000
    """)

# Import page modules
elif page == "Upload":
    from pages import upload
    upload.render()

elif page == "Criteria Review":
    from pages import criteria
    criteria.render()

elif page == "Evaluation":
    from pages import evaluation
    evaluation.render()

elif page == "Report":
    from pages import report
    report.render()
