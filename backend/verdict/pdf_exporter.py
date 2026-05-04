"""
PDF export for verdict reports with audit chain verification.
"""

import logging
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, green, red, orange, black, white
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from backend.extraction.schemas import BidderReport
from backend.verdict.audit_logger import get_audit_logger

logger = logging.getLogger(__name__)


def export_pdf(report: BidderReport, output_path: str) -> None:
    """
    Export a bidder report to PDF with audit chain information.
    
    Args:
        report: BidderReport object to export
        output_path: Path where PDF should be saved
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        doc = SimpleDocTemplate(str(output_path), pagesize=letter, topMargin=0.5*inch)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=black,
            spaceAfter=0.3*inch
        )
        story.append(Paragraph("Tender Evaluation Report", title_style))
        
        # Header Info
        header_data = [
            ["Tender ID:", report.tender_id],
            ["Bidder ID:", report.bidder_id],
            ["Overall Verdict:", report.overall_verdict],
            ["Generated:", report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")]
        ]
        header_table = Table(header_data, colWidths=[2*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), HexColor('#f0f0f0')),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Summary
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=11,
            leading=14
        )
        story.append(Paragraph("<b>Summary:</b>", summary_style))
        story.append(Paragraph(report.summary, summary_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Criteria Table
        story.append(Paragraph("<b>Criterion-by-Criterion Evaluation:</b>", summary_style))
        story.append(Spacer(1, 0.1*inch))
        
        criteria_data = [
            ["Criterion", "Verdict", "Confidence", "Source Doc", "Reasoning"]
        ]
        
        for verdict in report.criteria_verdicts:
            criteria_data.append([
                verdict.criterion_id,
                verdict.verdict,
                f"{verdict.confidence:.2%}",
                verdict.source_document,
                verdict.reasoning[:50] + "..." if len(verdict.reasoning) > 50 else verdict.reasoning
            ])
        
        criteria_table = Table(criteria_data, colWidths=[1*inch, 1*inch, 1*inch, 1.5*inch, 1.5*inch])
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#cccccc')),
            ('TEXTCOLOR', (0, 0), (-1, 0), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
        ]))
        story.append(criteria_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Audit Information
        audit_logger = get_audit_logger()
        chain_valid = audit_logger.verify_chain(report.tender_id)
        
        story.append(PageBreak())
        story.append(Paragraph("<b>Audit Trail & Integrity Verification:</b>", summary_style))
        story.append(Spacer(1, 0.1*inch))
        
        audit_status = "✓ Valid" if chain_valid else "✗ Invalid"
        story.append(Paragraph(f"Hash Chain Status: {audit_status}", summary_style))
        
        # Details for each verdict
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("<b>Detailed Verdict Information:</b>", summary_style))
        
        for verdict in report.criteria_verdicts:
            detail_text = f"""
<b>{verdict.criterion_id}</b>: {verdict.verdict}<br/>
Confidence: {verdict.confidence:.2%}<br/>
Reasoning: {verdict.reasoning}<br/>
Evidence: {verdict.evidence_quote[:100]}<br/>
Source: {verdict.source_document} (Page {verdict.source_page})<br/>
Hash: {verdict.hash[:16]}...<br/>
<br/>
"""
            story.append(Paragraph(detail_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        logger.info(f"PDF report exported to {output_path}")
    
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        raise
