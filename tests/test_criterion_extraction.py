"""
Tests for criterion extraction using Groq LLM.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from backend.extraction.criterion_extractor import extract_criteria


# Mock tender text with 5 criteria
MOCK_TENDER_TEXT = """
ELIGIBILITY CRITERIA

1. Minimum annual turnover of ₹5 crore for each of the last 3 financial years (mandatory)

2. At least 3 similar construction projects completed in the last 5 years each valued at ₹1 crore or more (mandatory)

3. Valid GST registration certificate (mandatory)

4. ISO 9001:2015 certification currently valid (mandatory)

5. Experience working with Central Government or Defence organisations (desirable, not mandatory)
"""


@patch('backend.extraction.criterion_extractor.client')
def test_extract_criteria_count(mock_client):
    """Test that extract_criteria returns exactly 5 criteria."""
    
    # Mock response with 5 criteria in JSON
    criteria_json = json.dumps([
        {
            "criterion_id": "C001",
            "text": "Minimum annual turnover of ₹5 crore for each of the last 3 financial years",
            "criterion_type": "financial",
            "mandatory": True,
            "threshold": 50000000.0,
            "operator": ">=",
            "unit": "INR",
            "evidence_docs": ["turnover_certificate"],
            "source_section": "Eligibility Criteria",
            "source_text": "Minimum annual turnover of ₹5 crore for each of the last 3 financial years (mandatory)"
        },
        {
            "criterion_id": "C002",
            "text": "At least 3 similar construction projects completed in the last 5 years each valued at ₹1 crore or more",
            "criterion_type": "technical",
            "mandatory": True,
            "threshold": 3,
            "operator": ">=",
            "unit": "count",
            "evidence_docs": ["project_completion_certificate"],
            "source_section": "Eligibility Criteria",
            "source_text": "At least 3 similar construction projects completed in the last 5 years"
        },
        {
            "criterion_id": "C003",
            "text": "Valid GST registration certificate",
            "criterion_type": "document",
            "mandatory": True,
            "threshold": None,
            "operator": None,
            "unit": None,
            "evidence_docs": ["gst_certificate"],
            "source_section": "Eligibility Criteria",
            "source_text": "Valid GST registration certificate (mandatory)"
        },
        {
            "criterion_id": "C004",
            "text": "ISO 9001:2015 certification currently valid",
            "criterion_type": "compliance",
            "mandatory": True,
            "threshold": None,
            "operator": None,
            "unit": None,
            "evidence_docs": ["iso_certificate"],
            "source_section": "Eligibility Criteria",
            "source_text": "ISO 9001:2015 certification currently valid (mandatory)"
        },
        {
            "criterion_id": "C005",
            "text": "Experience working with Central Government or Defence organisations",
            "criterion_type": "technical",
            "mandatory": False,
            "threshold": None,
            "operator": None,
            "unit": None,
            "evidence_docs": ["experience_letter"],
            "source_section": "Eligibility Criteria",
            "source_text": "Experience working with Central Government or Defence organisations (desirable, not mandatory)"
        }
    ])
    
    # Mock Groq response structure: message.choices[0].message.content
    mock_response = MagicMock()
    mock_response.choices[0].message.content = criteria_json
    mock_client.chat.completions.create.return_value = mock_response
    
    # Extract criteria
    criteria = extract_criteria(MOCK_TENDER_TEXT, "Eligibility Criteria")
    
    # Assertions
    assert len(criteria) == 5, f"Expected 5 criteria, got {len(criteria)}"


@patch('backend.extraction.criterion_extractor.client')
def test_extract_criteria_mandatory_flags(mock_client):
    """Test that mandatory flags are correct."""
    
    criteria_json = json.dumps([
        {
            "criterion_id": "C001",
            "text": "Criterion 1",
            "criterion_type": "financial",
            "mandatory": True,
            "threshold": 5000000,
            "operator": ">=",
            "unit": "INR",
            "evidence_docs": [],
            "source_section": "Test",
            "source_text": "Test"
        },
        {
            "criterion_id": "C002",
            "text": "Criterion 2",
            "criterion_type": "technical",
            "mandatory": True,
            "threshold": 1,
            "operator": ">=",
            "unit": "count",
            "evidence_docs": [],
            "source_section": "Test",
            "source_text": "Test"
        },
        {
            "criterion_id": "C005",
            "text": "Criterion 5",
            "criterion_type": "technical",
            "mandatory": False,
            "threshold": None,
            "operator": None,
            "unit": None,
            "evidence_docs": [],
            "source_section": "Test",
            "source_text": "Test"
        }
    ])
    
    # Mock Groq response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = criteria_json
    mock_client.chat.completions.create.return_value = mock_response
    
    criteria = extract_criteria(MOCK_TENDER_TEXT, "Eligibility Criteria")
    
    # Check mandatory flags
    assert criteria[0].mandatory is True
    assert criteria[1].mandatory is True
    assert criteria[2].mandatory is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

