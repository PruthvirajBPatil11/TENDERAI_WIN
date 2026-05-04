"""
Tests for OCR and document processing.
"""

import pytest
from pathlib import Path
from backend.ingestion.detector import detect_doc_type
from backend.extraction.value_normaliser import normalise_currency, normalise_date, is_date_valid
from datetime import datetime, timedelta


def test_detect_digital_pdf(tmp_path):
    """Test digital PDF detection."""
    # Create a mock digital PDF with substantial text
    # For testing, we'll use a text-based detection
    # In real tests, you'd use actual PDF files
    
    # Skip for now as we need actual test files
    pass


def test_detect_scanned_pdf(tmp_path):
    """Test scanned PDF detection."""
    # Skip for now
    pass


# Currency normalization tests
def test_normalise_currency_crore():
    """Test ₹X crore format."""
    result = normalise_currency("₹5 crore")
    assert result == 50000000.0


def test_normalise_currency_lakh():
    """Test X lakh format."""
    result = normalise_currency("52.35 lakh")
    assert result == 5235000.0


def test_normalise_currency_crore_full():
    """Test ₹X,XX,XX,XXX format."""
    result = normalise_currency("₹5,23,45,000")
    assert result == 52345000.0


def test_normalise_currency_inr():
    """Test INR X format."""
    result = normalise_currency("INR 5000000")
    assert result == 5000000.0


def test_normalise_currency_cr_abbreviation():
    """Test 5 Cr format."""
    result = normalise_currency("5 Cr")
    assert result == 50000000.0


def test_normalise_currency_lac():
    """Test X lac format."""
    result = normalise_currency("500 L")
    assert result == 50000000.0


def test_normalise_currency_decimal_crore():
    """Test 5.23 crore format."""
    result = normalise_currency("5.23 crore")
    assert result == 52300000.0


def test_normalise_currency_rs_notation():
    """Test Rs. X format."""
    result = normalise_currency("Rs. 5,23,45,000")
    assert result == 52345000.0


def test_normalise_currency_invalid():
    """Test invalid currency format."""
    result = normalise_currency("invalid")
    assert result is None


# Date normalization tests
def test_normalise_date_ddmmyyyy():
    """Test DD/MM/YYYY format."""
    result = normalise_date("15/01/2024")
    assert result == "2024-01-15"


def test_normalise_date_ddmmyyyy_dash():
    """Test DD-MM-YYYY format."""
    result = normalise_date("15-01-2024")
    assert result == "2024-01-15"


def test_normalise_date_month_name():
    """Test Month DD YYYY format."""
    result = normalise_date("January 15 2024")
    assert result == "2024-01-15"


def test_normalise_date_invalid():
    """Test invalid date."""
    result = normalise_date("invalid")
    assert result is None


# Date validity tests
def test_is_date_valid_future():
    """Test future date validation."""
    future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert is_date_valid(future_date) is True


def test_is_date_valid_past():
    """Test past date validation."""
    past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    assert is_date_valid(past_date) is False


def test_is_date_valid_today():
    """Test today's date validation."""
    today = datetime.now().strftime("%Y-%m-%d")
    assert is_date_valid(today) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
