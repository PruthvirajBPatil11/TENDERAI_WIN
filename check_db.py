import os
from pathlib import Path

# Load env
env_file = Path('.env')
if env_file.exists():
    with open('.env') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ[k.strip()] = v.strip()

try:
    from backend.database.db import SessionLocal
    from backend.database import models

    db = SessionLocal()
    docs = db.query(models.BidderDocument).all()
    print(f'Total docs in DB: {len(docs)}')
    for d in docs:
        text_len = len(d.extracted_text or "")
        print(f'  {d.filename}: ocr_confidence={d.ocr_confidence}, text_len={text_len}')
    db.close()
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
