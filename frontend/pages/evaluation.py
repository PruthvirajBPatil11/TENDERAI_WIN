"""
Evaluation page - run evaluation and view verdicts.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the evaluation page."""
    st.title("⚖️ Evaluation Results")
    
    if "tender_id" not in st.session_state or "bidder_id" not in st.session_state:
        st.warning("⚠️ Please upload tender and bidder documents first in the **Upload** page")
        return
    
    tender_id = st.session_state.tender_id
    bidder_id = st.session_state.bidder_id
    
    st.write(f"**Tender ID:** `{tender_id}` | **Bidder ID:** `{bidder_id}`")
    
    # Run evaluation button
    if st.button("🚀 Run Evaluation", key="run_eval"):
        with st.spinner("Running evaluation..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/evaluate/",
                    json={
                        "tender_id": tender_id,
                        "bidder_id": bidder_id
                    },
                    timeout=300  # 5 minutes for evaluation with OCR
                )
                
                if response.status_code == 200:
                    result = response.json()
                    verdicts = result.get("verdicts", [])
                    
                    st.session_state.verdicts = verdicts
                    st.success(f"✓ Evaluation complete! {len(verdicts)} criteria evaluated.")
                else:
                    st.error(f"Error: {response.text}")
            
            except Exception as e:
                st.error(f"Error running evaluation: {str(e)}")
    
    # Display verdicts if available
    if "verdicts" in st.session_state and st.session_state.verdicts:
        verdicts = st.session_state.verdicts
        
        st.subheader("Verdict Summary")
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        pass_count = sum(1 for v in verdicts if v["verdict"] == "PASS")
        fail_count = sum(1 for v in verdicts if v["verdict"] == "FAIL")
        review_count = sum(1 for v in verdicts if v["verdict"] == "MANUAL_REVIEW")
        
        col1.metric("Passed", pass_count)
        col2.metric("Failed", fail_count)
        col3.metric("Manual Review", review_count)
        col4.metric("Total", len(verdicts))
        
        # Verdict breakdown chart
        fig = go.Figure(data=[go.Pie(
            labels=["PASS", "FAIL", "MANUAL_REVIEW"],
            values=[pass_count, fail_count, review_count],
            marker=dict(colors=["#2ecc71", "#e74c3c", "#f39c12"])
        )])
        fig.update_layout(title="Verdict Distribution")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed verdicts table
        st.subheader("Detailed Verdicts")
        
        verdicts_df = pd.DataFrame([
            {
                "Criterion ID": v["criterion_id"],
                "Verdict": v["verdict"],
                "Confidence": f"{v['confidence']:.0%}",
                "Reasoning": v["reasoning"][:60] + "..."
            }
            for v in verdicts
        ])
        
        # Color code the verdict column
        def highlight_verdict(val):
            if val == "PASS":
                return "background-color: #2ecc71; color: white;"
            elif val == "FAIL":
                return "background-color: #e74c3c; color: white;"
            else:
                return "background-color: #f39c12; color: white;"
        
        styled_df = verdicts_df.style.map(highlight_verdict, subset=["Verdict"])
        st.dataframe(styled_df, use_container_width=True)
        
        # Export to report
        st.subheader("Next Steps")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 View JSON Report"):
                try:
                    response = requests.get(
                        f"{API_BASE_URL}/report/{tender_id}/{bidder_id}"
                    )
                    
                    if response.status_code == 200:
                        report = response.json()
                        st.json(report)
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Error fetching report: {str(e)}")
        
        with col2:
            if st.button("📑 Export PDF Report"):
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
