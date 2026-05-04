"""
FastAPI dependency providers.
"""

from backend.database.db import get_db
from backend.database.models import Tender, Bidder


async def get_tender_db(tender_id: str):
    """Get tender from database."""
    db = get_db()
    tender = db.query(Tender).filter(Tender.id == tender_id).first()
    return tender


async def get_bidder_db(bidder_id: str):
    """Get bidder from database."""
    db = get_db()
    bidder = db.query(Bidder).filter(Bidder.id == bidder_id).first()
    return bidder
