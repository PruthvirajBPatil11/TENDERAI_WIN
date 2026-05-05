"""
Pydantic models for criterion, bidder values, and verdicts.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime


class Criterion(BaseModel):
    """Represents a single eligibility criterion extracted from a tender document."""
    
    criterion_id: str = Field(..., description="Unique identifier for this criterion")
    text: str = Field(..., description="Full text of the criterion")
    criterion_type: Literal["financial", "technical", "compliance", "document", "experience", "other"] = Field(
        ..., description="Type of criterion"
    )
    mandatory: bool = Field(..., description="Whether this criterion is mandatory")
    threshold: Optional[float] = Field(None, description="Numeric threshold if applicable")
    operator: Optional[Literal[">=", "<=", "==", "contains", ">=N_in_M_years"]] = Field(
        None, description="Comparison operator for threshold"
    )
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., 'crore', 'years')")
    evidence_docs: list[str] = Field(default_factory=list, description="Document types needed as evidence")
    source_section: str = Field(..., description="Section name where this criterion appears")
    source_text: str = Field(..., description="Original text snippet from tender")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "criterion_id": "C001",
                "text": "Minimum annual turnover of ₹5 crore",
                "criterion_type": "financial",
                "mandatory": True,
                "threshold": 50000000.0,
                "operator": ">=",
                "unit": "INR",
                "evidence_docs": ["turnover_certificate", "financial_statements"],
                "source_section": "Eligibility Criteria",
                "source_text": "Minimum annual turnover of ₹5 crore for each of the last 3 financial years"
            }
        }


class BidderValue(BaseModel):
    """Represents an extracted value from a bidder's submission document."""
    
    criterion_id: str = Field(..., description="ID of the criterion being evaluated")
    bidder_id: str = Field(..., description="ID of the bidder")
    extracted_value: str = Field(..., description="Raw extracted value as text")
    normalised_value: Optional[float] = Field(None, description="Normalised numeric value")
    source_document: str = Field(..., description="Document file name where value was found")
    source_page: int = Field(..., description="Page number in document")
    extraction_method: str = Field(..., description="Method used (ocr, nlp, manual, etc.)")
    ocr_confidence: Optional[float] = Field(None, description="OCR confidence score (0-1)")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "criterion_id": "C001",
                "bidder_id": "B001",
                "extracted_value": "₹8.2 crore",
                "normalised_value": 82000000.0,
                "source_document": "turnover_certificate.pdf",
                "source_page": 1,
                "extraction_method": "ocr",
                "ocr_confidence": 0.95
            }
        }


class Verdict(BaseModel):
    """Represents the evaluation verdict for a criterion against a bidder."""
    
    criterion_id: str = Field(..., description="ID of the criterion")
    bidder_id: str = Field(..., description="ID of the bidder")
    verdict: Literal["PASS", "FAIL", "MANUAL_REVIEW"] = Field(..., description="The verdict")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    reasoning: str = Field(..., description="Explanation of the verdict")
    evidence_quote: Optional[str] = Field(None, description="Quote from supporting document")
    source_document: str = Field(..., description="Document where evidence was found")
    source_page: int = Field(..., description="Page number in document")
    ocr_confidence: Optional[float] = Field(None, description="OCR confidence of the evidence")
    ambiguity_reason: Optional[str] = Field(None, description="Reason for manual review if applicable")
    hash: Optional[str] = Field(None, description="SHA-256 hash of this verdict for audit trail")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "criterion_id": "C001",
                "bidder_id": "B001",
                "verdict": "PASS",
                "confidence": 0.95,
                "reasoning": "Extracted turnover of ₹8.2 crore meets minimum requirement of ₹5 crore",
                "evidence_quote": "Annual turnover: ₹8.2 crore",
                "source_document": "turnover_certificate.pdf",
                "source_page": 1,
                "ocr_confidence": 0.95,
                "ambiguity_reason": None,
                "hash": "abc123def456..."
            }
        }


class BidderReport(BaseModel):
    """Complete evaluation report for a bidder against all criteria."""
    
    bidder_id: str = Field(..., description="ID of the bidder")
    tender_id: str = Field(..., description="ID of the tender")
    overall_verdict: Literal["ELIGIBLE", "NOT_ELIGIBLE", "MANUAL_REVIEW"] = Field(
        ..., description="Overall eligibility verdict"
    )
    criteria_verdicts: list[Verdict] = Field(..., description="Verdicts for all criteria")
    summary: str = Field(..., description="Plain-English summary of the report")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Report generation timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "bidder_id": "B001",
                "tender_id": "T001",
                "overall_verdict": "ELIGIBLE",
                "criteria_verdicts": [],
                "summary": "Bidder meets all mandatory criteria and is eligible.",
                "created_at": "2024-01-15T10:30:00"
            }
        }
