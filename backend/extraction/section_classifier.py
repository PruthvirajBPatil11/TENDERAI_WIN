"""
Section classifier - identifies which sections are eligibility sections using Groq.
"""

import logging
from groq import Groq
from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize Groq client
client = Groq(api_key=settings.groq_api_key)


def classify_sections(chunks: list[dict]) -> list[dict]:
    """
    Classify document sections and identify which are eligibility sections.

    Hybrid approach:
    1. Strong keyword match → direct classification
    2. Weak match → LLM
    3. LLM failure → fallback keyword scan on text
    """

    # Keywords that MUST be in section name to classify as eligibility
    eligibility_keywords = [
        "eligibility",
        "qualification",
        "criteria",
        "eligible bidder"
    ]
    
    # Keywords that indicate NON-eligibility sections
    non_eligibility_keywords = [
        "technical requirement",
        "financial requirement",
        "general condition",
        "scope of work",
        "terms and condition"
    ]

    for chunk in chunks:
        section_name = chunk.get("section_name", "").lower()
        text = chunk.get("text", "").lower()

        # 🔹 STEP 1: Check for non-eligibility sections first (negative match)
        is_non_eligibility = any(kw in section_name for kw in non_eligibility_keywords)
        if is_non_eligibility:
            chunk["is_eligibility_section"] = False
            logger.debug(f"[NON-ELIGIBILITY] '{chunk.get('section_name')}' → other")
            continue

        # 🔹 STEP 2: Strong keyword match (fast + reliable)
        keyword_hits = sum(1 for kw in eligibility_keywords if kw in section_name)

        if keyword_hits >= 1:
            chunk["is_eligibility_section"] = True
            logger.debug(f"[KEYWORD] '{chunk.get('section_name')}' → eligibility")
            continue

        # 🔹 STEP 3: Try LLM only if needed
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,  # ⚠️ MUST be updated in config
                max_tokens=10,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Classify this tender section.

Answer ONLY 'yes' or 'no'.

Is it about eligibility criteria, bidder qualification, or requirements for bidders to participate?

Section Name: {chunk.get('section_name')}
Section Text: {text[:400]}"""
                    }
                ]
            )

            response_text = response.choices[0].message.content.lower().strip()
            is_eligibility = response_text.startswith("yes")

            chunk["is_eligibility_section"] = is_eligibility

            logger.debug(
                f"[LLM] '{chunk.get('section_name')}' → {'eligibility' if is_eligibility else 'other'}"
            )

        except Exception as e:
            # 🔴 STEP 4: Fallback if LLM fails
            logger.warning(f"Groq LLM failed: {e}")

            fallback_match = any(kw in text for kw in eligibility_keywords)

            chunk["is_eligibility_section"] = fallback_match

            logger.debug(
                f"[FALLBACK] '{chunk.get('section_name')}' → {'eligibility' if fallback_match else 'other'}"
            )

    return chunks