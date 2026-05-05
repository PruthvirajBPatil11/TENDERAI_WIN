"""
Upload page - upload tender and bidder documents.
"""

import streamlit as st
import requests
import pandas as pd

API_BASE_URL = "http://localhost:8000"


def render():
    """Render the upload page."""
    st.title("📤 Document Upload")
    
    # Tender upload section
    st.header("1. Upload Tender Document")
    
    tender_file = st.file_uploader(
        "Select tender document (PDF, DOCX, Image)",
        type=["pdf", "docx", "png", "jpg", "jpeg", "gif"],
        key="tender_upload"
    )
    
    if tender_file and st.button("Process Tender", key="process_tender"):
        with st.spinner("Processing tender document..."):
            try:
                # Upload tender
                files = {"file": tender_file}
                response = requests.post(
                    f"{API_BASE_URL}/tender/upload",
                    files=files,
                    timeout=300  # 5 minutes for OCR processing
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tender_id = result.get("tender_id")
                    
                    st.success(f"✓ Tender processed! ID: `{tender_id}`")
                    
                    # Store tender_id in session
                    st.session_state.tender_id = tender_id
                    
                    # Display extracted criteria
                    st.subheader("Extracted Criteria")
                    
                    criteria = result.get("criteria", [])
                    
                    if criteria:
                        criteria_df = pd.DataFrame([
                            {
                                "ID": c["id"],
                                "Criterion": c["text"][:60] + "...",
                                "Type": c["type"],
                                "Mandatory": "Yes" if c["mandatory"] else "No",
                                "Threshold": c.get("threshold", "N/A")
                            }
                            for c in criteria
                        ])
                        
                        st.dataframe(criteria_df, use_container_width=True)
                        st.info(f"Total criteria extracted: {len(criteria)}")
                    else:
                        st.warning("No criteria found in tender document")
                else:
                    st.error(f"Error: {response.text}")
            
            except Exception as e:
                st.error(f"Error processing tender: {str(e)}")
    
    st.divider()
    
    # Bidder upload section
    st.header("2. Upload Bidder Documents")
    
    # Check if tender has been uploaded
    if "tender_id" not in st.session_state:
        st.warning("⚠️ Please upload and process a tender document first")
    else:
        tender_id = st.session_state.tender_id
        
        st.write(f"**Current Tender ID:** `{tender_id}`")
        
        bidder_name = st.text_input(
            "Bidder Name",
            placeholder="Enter the name of the bidding company"
        )
        
        bidder_files = st.file_uploader(
            "Select bidder documents (multiple files allowed)",
            type=["pdf", "docx", "png", "jpg", "jpeg", "gif"],
            accept_multiple_files=True,
            key="bidder_upload"
        )
        
        if bidder_name and bidder_files and st.button("Upload Bidder Documents", key="upload_bidder"):
            with st.spinner("Uploading bidder documents..."):
                try:
                    # Upload bidder files
                    files = [("files", f) for f in bidder_files]
                    data = {
                        "tender_id": tender_id,
                        "bidder_name": bidder_name
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/bidder/upload",
                        files=files,
                        data=data,
                        timeout=300  # 5 minutes for OCR processing
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        bidder_id = result.get("bidder_id")
                        
                        st.success(f"✓ Bidder documents uploaded! ID: `{bidder_id}`")
                        
                        # Store bidder_id in session
                        st.session_state.bidder_id = bidder_id
                        
                        # Display upload results
                        st.subheader("Upload Results")
                        
                        files_result = result.get("files", [])
                        for file_result in files_result:
                            if file_result.get("status") == "uploaded":
                                st.success(f"✓ {file_result['filename']} ({file_result['doc_type']})")
                            else:
                                st.error(f"✗ {file_result['filename']}: {file_result.get('error', 'Unknown error')}")
                        
                        st.info(f"Ready for evaluation. Next, go to **Evaluation** to run the matching pipeline.")
                    else:
                        st.error(f"Error: {response.text}")
                
                except Exception as e:
                    st.error(f"Error uploading bidder documents: {str(e)}")
