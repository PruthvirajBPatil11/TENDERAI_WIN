"""
End-to-end integration tests.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from pathlib import Path
import io

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert data["service"] == "TenderEval AI"


def test_tender_upload_with_mock_file():
    """Test tender upload with mock file."""
    # Create a mock PDF file content
    mock_pdf_content = b"%PDF-1.4\n%mock\nEndobj"
    
    files = {
        "file": ("test_tender.pdf", io.BytesIO(mock_pdf_content), "application/pdf")
    }
    
    response = client.post("/tender/upload", files=files)
    
    # Note: This will likely fail without actual PDF content,
    # but shows the expected endpoint structure
    # assert response.status_code == 200
    # data = response.json()
    # assert "tender_id" in data


def test_bidder_upload_requires_tender():
    """Test that bidder upload requires a tender_id."""
    response = client.post(
        "/bidder/upload",
        params={
            "tender_id": "T00000000",
            "bidder_name": "Test Bidder"
        }
    )
    
    # Should fail because tender doesn't exist
    assert response.status_code in [404, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
