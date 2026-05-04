"""
Criterion extraction using Groq LLM with structured JSON output.
"""

import json
import logging
import re
from groq import Groq
from backend.extraction.schemas import Criterion
from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=settings.groq_api_key)


def parse_criteria_blocks(text: str, section_name: str) -> list[Criterion]:
    """Parse delimiter-based criterion blocks (100% reliable, no JSON)."""
    criteria = []
    blocks = text.split("### CRITERION ###")
    
    logger.info(f"Found {len(blocks)} raw blocks (first is header/preamble)")

    for idx, block in enumerate(blocks, 1):
        if not block.strip():
            logger.debug(f"Block {idx}: Empty, skipping")
            continue

        try:
            lines = block.strip().split("\n")
            data = {}

            for line in lines:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                data[key.strip().lower()] = value.strip()

            # DEBUG: Print keys directly to stdout
            print(f"\n[DEBUG Block {idx}] Keys parsed: {list(data.keys())}")
            print(f"[DEBUG Block {idx}] Values: {data}")
            
            # Skip if missing critical fields
            if not data.get("text"):
                logger.warning(f"Block {idx}: No TEXT field, skipping")
                continue

            # Convert string 'null' to actual None
            operator = data.get("operator")
            if operator and operator.lower() == "null":
                operator = None
                
            unit = data.get("unit")
            if unit and unit.lower() == "null":
                unit = None

            # Parse threshold as float if present
            threshold = None
            threshold_str = data.get("threshold")
            if threshold_str and threshold_str.lower() != "null":
                try:
                    threshold = float(threshold_str)
                except (ValueError, TypeError):
                    threshold = None

            criteria.append(Criterion(
                criterion_id=data.get("id", f"C{idx:03d}"),
                text=data.get("text", ""),
                criterion_type=data.get("type", "technical"),
                mandatory=data.get("mandatory", "false").lower() == "true",
                threshold=threshold,
                operator=operator,
                unit=unit,
                evidence_docs=[d.strip() for d in data.get("evidence", "").split(",") if d.strip() and d.strip().lower() != "null"],
                source_section=section_name,
                source_text=data.get("text", "")
            ))
            logger.info(f"Block {idx}: Parsed successfully - {data.get('id')} ({data.get('type')})")

        except Exception as e:
            logger.warning(f"Block {idx}: Parsing failed - {e}")

    return criteria


def extract_criteria(section_text: str, section_name: str) -> list[Criterion]:
    """
    Extract eligibility criteria from a tender section using Groq LLM.
    """

    if not section_text:
        return []

    try:
        messages = [
            {
                "role": "system",
                "content": """You are an expert tender analyst. Your task is to extract EVERY SINGLE eligibility criterion.

Use ONLY this format - NO JSON ALLOWED:

### CRITERION ###
ID: C1
TEXT: Full criterion text exactly as it appears
TYPE: financial|technical|compliance|document|experience|other
MANDATORY: true|false
THRESHOLD: value or null
OPERATOR: >=|<=|==|contains|null
UNIT: crore|lakh|rupee|years|months|other|null
EVIDENCE: doc1, doc2, doc3

INSTRUCTIONS:
1. Find ALL numbered criteria (1., 2., 3., etc.)
2. Find EVERY section mentioning criteria, requirements, or qualifications
3. Extract BOTH mandatory and desirable/optional criteria
4. Each criterion gets its own ### CRITERION ### block
5. Count the criteria and verify you extracted them all
6. If you see 5 criteria, output 5 blocks. If 3, output 3.
7. CRITICAL: Do NOT skip any criteria. Return them all."""
            },
            {
                "role": "user",
                "content": f"""Extract ALL criteria. Count them first, then output each one.

How many numbered criteria do you see in this text?
List them:
1. [name]
2. [name]
etc.

Then output each as ### CRITERION ### block below.

Section Name: {section_name}

Section Text:
{section_text}"""
            }
        ]

        response = client.chat.completions.create(
            model=settings.groq_model,
            temperature=0,
            max_tokens=4000,
            messages=messages
        )

        response_text = response.choices[0].message.content.strip()

        if not response_text:
            logger.warning("Empty response from LLM")
            return []

        # DEBUG: Print raw response
        logger.info("=" * 80)
        logger.info("RAW GROQ RESPONSE:")
        logger.info("=" * 80)
        logger.info(response_text)
        logger.info("=" * 80)
        logger.info(f"### CRITERION ### blocks found: {response_text.count('### CRITERION ###')}")
        logger.info("=" * 80)

        # Parse delimiter-based blocks instead of JSON
        criteria = parse_criteria_blocks(response_text, section_name)

        logger.info(f"Extracted {len(criteria)} criteria from {section_name}")
        return criteria

    except Exception as e:
        logger.error(f"Error extracting criteria from section {section_name}: {e}")
        return []