"""
Report page - view and export reports.
"""

import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the report page."""
    st.title("📄 Report & Audit Trail")
    
    if "tender_id" not in st.session_state or "bidder_id" not in st.session_state:
        st.warning("⚠️ Please complete evaluation first in the **Evaluation** page")
        return
    
    tender_id = st.session_state.tender_id
    bidder_id = st.session_state.bidder_id
    
    st.write(f"**Tender ID:** `{tender_id}` | **Bidder ID:** `{bidder_id}`")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["Report", "Audit Trail", "Export"])
    
    with tab1:
        st.subheader("Evaluation Report")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/report/{tender_id}/{bidder_id}"
            )
            
            if response.status_code == 200:
                report = response.json()
                
                # Overall verdict badge
                overall_verdict = report.get("overall_verdict", "UNKNOWN")
                
                if overall_verdict == "ELIGIBLE":
                    st.success(f"### ✓ Overall Verdict: {overall_verdict}")
                elif overall_verdict == "NOT_ELIGIBLE":
                    st.error(f"### ✗ Overall Verdict: {overall_verdict}")
                else:
                    st.warning(f"### ⚠️ Overall Verdict: {overall_verdict}")
                
                # Summary
                st.write(f"**Summary:** {report.get('summary', '')}")
                
                # Detailed verdicts
                st.subheader("Criterion-by-Criterion Results")
                
                verdicts = report.get("criteria_verdicts", [])
                
                for verdict in verdicts:
                    with st.expander(f"{verdict['criterion_id']}: {verdict['verdict']}"):
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            if verdict['verdict'] == "PASS":
                                st.success(verdict['verdict'])
                            elif verdict['verdict'] == "FAIL":
                                st.error(verdict['verdict'])
                            else:
                                st.warning(verdict['verdict'])
                            
                            st.metric("Confidence", f"{verdict['confidence']:.0%}")
                        
                        with col2:
                            st.write(f"**Reasoning:** {verdict['reasoning']}")
                            if verdict.get('evidence_quote'):
                                st.write(f"**Evidence:** {verdict['evidence_quote']}")
                            st.write(f"**Source:** {verdict.get('source_document', 'unknown')} (Page {verdict.get('source_page', 1)})")
                            
                            if verdict.get('ocr_confidence'):
                                st.write(f"**OCR Confidence:** {verdict['ocr_confidence']:.2%}")
            else:
                st.error(f"Error: {response.text}")
        
        except Exception as e:
            st.error(f"Error fetching report: {str(e)}")
    
    with tab2:
        st.subheader("Immutable Audit Trail")
        
        try:
            response = requests.get(
                f"{API_BASE_URL}/audit/{tender_id}"
            )
            
            if response.status_code == 200:
                audit = response.json()
                
                # Chain verification status
                if audit.get("chain_valid"):
                    st.success("✓ Hash chain integrity verified")
                else:
                    st.error("✗ Hash chain integrity compromised")
                
                # Audit entries
                st.write(f"**Total entries:** {audit.get('entries_count', 0)}")
                
                entries = audit.get("entries", [])
                
                audit_df = pd.DataFrame([
                    {
                        "ID": e["id"],
                        "Bidder": e["bidder_id"],
                        "Criterion": e["criterion_id"],
                        "Verdict": e["verdict"],
                        "Confidence": f"{e['confidence']:.0%}",
                        "Timestamp": e["timestamp"],
                        "Hash": e["hash"]
                    }
                    for e in entries
                ])
                
                st.dataframe(audit_df, use_container_width=True)
            else:
                st.error(f"Error: {response.text}")
        
        except Exception as e:
            st.error(f"Error fetching audit log: {str(e)}")
    
    with tab3:
        st.subheader("Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download PDF Report"):
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/report/{tender_id}/{bidder_id}/pdf"
                    )
                    
                    if response.status_code == 200:
                        st.download_button(
                            label="Download PDF",
                            data=response.content,
                            file_name=f"{tender_id}_{bidder_id}_report.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error exporting PDF: {str(e)}")
        
        with col2:
            if st.button("📊 Download JSON Report"):
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/report/{tender_id}/{bidder_id}"
                    )
                    
                    if response.status_code == 200:
                        import json
                        report_json = json.dumps(response.json(), indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=report_json,
                            file_name=f"{tender_id}_{bidder_id}_report.json",
                            mime="application/json"
                        )
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error exporting JSON: {str(e)}")
