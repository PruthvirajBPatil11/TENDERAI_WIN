# TenderEval AI

## Government Tender Evaluation Platform

TenderEval AI is an AI-powered platform for automated and standardized evaluation of government tender bids. It uses advanced document processing, natural language processing, and machine learning to extract eligibility criteria from tender documents, parse bidder submissions, and produce explainable verdicts with complete audit trails.

The platform combines multiple evaluation methods—rule-based matching, semantic similarity, and LLM-as-judge—to handle both quantitative and qualitative criteria. Every decision is fully traceable with an immutable SHA-256 hash chain for regulatory compliance.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT FRONTEND (8501)                     │
│  Upload → Criteria Review → Evaluation → Report Generation       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND (8000)                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐   │
│  │ INGESTION    │      │ EXTRACTION   │      │  MATCHING    │   │
│  │              │      │              │      │              │   │
│  │ • Detector   │      │ • Criterion  │      │ • Rule       │   │
│  │ • OCR        │      │   Extraction │      │   Engine     │   │
│  │ • PDF Parser │      │ • NER        │      │ • Semantic   │   │
│  │ • Chunker    │      │ • Tables     │      │   Matcher    │   │
│  │ • Layout     │      │ • Normaliser │      │ • LLM Judge  │   │
│  └──────────────┘      └──────────────┘      └──────────────┘   │
│                                │                       │         │
│                                └───────┬───────────────┘         │
│                                        ▼                         │
│                        ┌─────────────────────────┐               │
│                        │ VERDICT GENERATION      │               │
│                        │ • Orchestrator          │               │
│                        │ • Audit Logger          │               │
│                        │ • Report Builder        │               │
│                        │ • PDF Exporter          │               │
│                        └─────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                       │                    │
            ┌──────────┴──────────┬─────────┴──────────┐
            ▼                     ▼                    ▼
      ┌─────────────┐      ┌──────────────┐    ┌────────────┐
      │  SQLite DB  │      │ Qdrant       │    │  File      │
      │             │      │ Vector Store │    │  Storage   │
      │ • Tenders   │      │              │    │            │
      │ • Bidders   │      │ • Criteria   │    │ • Documents│
      │ • Criteria  │      │   Embeddings │    │ • Reports  │
      │ • Verdicts  │      │ • Semantic   │    │ • Outputs  │
      │ • Audit Log │      │   Search     │    │            │
      └─────────────┘      └──────────────┘    └────────────┘
```

## Features

- **🔍 Intelligent Document Ingestion**
  - Digital PDF text extraction
  - Scanned document OCR (PaddleOCR)
  - Image processing
  - DOCX support
  - Confidence scoring per token

- **📄 Automatic Criterion Extraction**
  - Groq LLM extracts structured criteria
  - Section classification and labeling
  - Threshold identification
  - Mandatory vs. optional flags

- **🤖 Multi-Method Evaluation**
  - Rule-based matching for numeric criteria
  - Semantic similarity for qualitative criteria
  - LLM-as-judge for ambiguous cases
  - Confidence scoring and conflict resolution

- **📊 Explainable Verdicts**
  - Per-criterion PASS / FAIL / MANUAL_REVIEW
  - Detailed reasoning with evidence quotes
  - OCR confidence tracking
  - Source document references

- **🔐 Audit & Compliance**
  - Immutable audit trail with SHA-256 hashing
  - Hash chain verification
  - Evaluator tracking
  - Timestamp logging

- **📑 Professional Reports**
  - PDF export with formatting
  - JSON export for integration
  - Audit trail summary
  - Digital signatures support (future)

## Setup

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- Free API keys for Groq and Gemini (see Free API Keys section below)

### Local Installation

1. **Clone and enter directory:**
   ```bash
   cd tender-eval-ai
   ```

2. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

3. **Update .env with free API keys:**
   ```bash
   # Edit .env with your GROQ_API_KEY and GEMINI_API_KEY
   # Get Groq key free at: groq.com
   # Get Gemini key free at: aistudio.google.com
   ```

4. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

6. **Download spaCy model:**
   ```bash
   python -m spacy download en_core_web_lg
   ```

7. **Start Qdrant (optional, for semantic search):**
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

8. **Initialize database:**
   ```bash
   python -c "from backend.database.db import init_db; init_db()"
   ```

### Run Services

**Terminal 1 - FastAPI Backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Streamlit Frontend:**
```bash
streamlit run frontend/app.py
```

- Backend API: http://localhost:8000
- Frontend UI: http://localhost:8501
- API Documentation: http://localhost:8000/docs

### Docker Setup

```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

## Free API Keys

This project uses only free APIs:

- **Groq (LLM)**: [groq.com](https://groq.com) — Sign up, go to API Keys, create key. 14,400 free requests/day.
- **Gemini (Vision)**: [aistudio.google.com](https://aistudio.google.com) — Sign in with Google, click Get API Key. 1,500 free requests/day.
- **Qdrant**: Runs locally via Docker, no key needed.
- **PaddleOCR**: Runs locally, no key needed.
- **All other components**: Open source, no keys needed.

## Usage

### 1. Upload Tender Document

```bash
curl -X POST http://localhost:8000/tender/upload \
  -F "file=@tender_document.pdf"
```

**Response:**
```json
{
  "tender_id": "T12345678",
  "doc_type": "DIGITAL_PDF",
  "criteria_count": 5,
  "criteria": [...]
}
```

### 2. Upload Bidder Documents

```bash
curl -X POST http://localhost:8000/bidder/upload \
  -F "files=@turnover.pdf" \
  -F "files=@projects.pdf" \
  -d "tender_id=T12345678" \
  -d "bidder_name=ABC Construction Ltd"
```

**Response:**
```json
{
  "bidder_id": "B87654321",
  "bidder_name": "ABC Construction Ltd",
  "tender_id": "T12345678",
  "files_count": 2,
  "files": [...]
}
```

### 3. Run Evaluation

```bash
curl -X POST http://localhost:8000/evaluate/ \
  -d "tender_id=T12345678" \
  -d "bidder_id=B87654321"
```

**Response:**
```json
{
  "tender_id": "T12345678",
  "bidder_id": "B87654321",
  "verdicts_count": 5,
  "verdicts": [
    {
      "criterion_id": "C001",
      "verdict": "PASS",
      "confidence": 0.98,
      "reasoning": "..."
    },
    ...
  ]
}
```

### 4. Get Report

```bash
# JSON Report
curl http://localhost:8000/report/T12345678/B87654321

# PDF Report
curl http://localhost:8000/report/T12345678/B87654321/pdf > report.pdf

# Audit Trail
curl http://localhost:8000/audit/T12345678
```

## Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test Module

```bash
pytest tests/test_ocr.py -v
pytest tests/test_criterion_extraction.py -v
pytest tests/test_matching.py -v
pytest tests/test_end_to_end.py -v
```

### Test Coverage

```bash
pytest tests/ --cov=backend --cov-report=html
```

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/` | GET | API information |
| `/tender/upload` | POST | Upload and process tender |
| `/bidder/upload` | POST | Upload bidder documents |
| `/evaluate/` | POST | Run evaluation |
| `/report/{tender_id}/{bidder_id}` | GET | Get JSON report |
| `/report/{tender_id}/{bidder_id}/pdf` | GET | Download PDF report |
| `/audit/{tender_id}` | GET | Get audit trail |

## Mock Data

The `data/mock/` directory contains example tender and bidder documents:

- **tender_crpf_construction.txt**: CRPF construction tender with 5 criteria
- **bidders/bidder_A/**: Clearly eligible bidder (all criteria pass)
- **bidders/bidder_B/**: Clearly ineligible (fails turnover)
- **bidders/bidder_C/**: Manual review needed (scanned doc quality issue)
- **bidders/bidder_D/**: Manual review needed (OCR confidence issue)

See README.md files in each bidder folder for details.

### To Test with Mock Data

1. Generate PDF from tender text:
   ```bash
   python -c "
   from reportlab.pdfgen import canvas
   from reportlab.lib.pagesizes import letter
   c = canvas.Canvas('data/mock/tender.pdf', pagesize=letter)
   with open('data/mock/tender_crpf_construction.txt', 'r') as f:
       text = f.read()
   c.drawString(100, 750, text[:100])
   c.save()
   "
   ```

2. Upload tender and run evaluation

## Configuration

### Environment Variables

- `GROQ_API_KEY`: Groq LLM API key (required) - [Get free key at groq.com](https://groq.com)
- `GROQ_MODEL`: Groq model (default: llama-3.1-70b-versatile)
- `GEMINI_API_KEY`: Gemini Vision API key (required) - [Get free key at aistudio.google.com](https://aistudio.google.com)
- `GEMINI_MODEL`: Gemini model (default: gemini-1.5-flash)
- `QDRANT_HOST`: Vector store host (default: localhost)
- `QDRANT_PORT`: Vector store port (default: 6333)
- `DATABASE_URL`: SQLite/PostgreSQL connection string (default: sqlite:///./tender_eval.db)
- `OCR_CONFIDENCE_THRESHOLD`: Minimum OCR confidence (default: 0.80)
- `SEMANTIC_SIMILARITY_PASS_THRESHOLD`: Confidence for PASS verdict (default: 0.75)
- `SEMANTIC_SIMILARITY_REVIEW_THRESHOLD`: Confidence for FAIL verdict (default: 0.50)

### Thresholds

Verdicts are determined by combining:
1. **Rule Engine**: Deterministic numeric comparisons
2. **Semantic Matcher**: Bi-encoder similarity scores
3. **LLM Judge**: Chain-of-thought reasoning for ambiguous cases

Thresholds can be adjusted in `backend/config.py` and `.env` file.

## Project Structure

```
tender-eval-ai/
├── backend/                 # FastAPI application
│   ├── main.py             # Entry point
│   ├── config.py           # Settings
│   ├── ingestion/          # Document processing
│   ├── extraction/         # Criterion & value extraction
│   ├── matching/           # Evaluation logic
│   ├── verdict/            # Report generation & audit
│   ├── vector_store/       # Semantic search
│   ├── database/           # ORM models & queries
│   └── api/                # Route handlers
├── frontend/               # Streamlit UI
│   ├── app.py             # Main app
│   ├── pages/             # Page modules
│   └── components/        # Reusable components
├── tests/                  # Test suites
├── data/
│   ├── mock/              # Example documents
│   └── outputs/           # Generated reports
├── models/                 # Embeddings & NER models
├── notebooks/             # Jupyter notebooks
├── docker-compose.yml     # Docker Compose config
├── Dockerfile             # API container
├── Dockerfile.streamlit   # Frontend container
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## Development

### Add New Criterion Type

1. Update `backend/extraction/schemas.py` with new criterion_type
2. Add extraction logic in `backend/extraction/`
3. Add matching logic in `backend/matching/`
4. Update `backend/verdict/generator.py` orchestration
5. Add tests in `tests/`

### Extend Matching Algorithm

1. Add new matcher in `backend/matching/`
2. Update `confidence_scorer.py` decision logic
3. Add benchmark tests
4. Document in API docs

### Add New Report Format

1. Create exporter in `backend/verdict/`
2. Add route handler in `backend/api/routes/report.py`
3. Test with various verdicts
4. Update API documentation

## Performance Considerations

- **OCR**: PaddleOCR is CPU-bound; consider GPU acceleration for production
- **LLM Calls**: Cached embeddings in vector store reduce API calls
- **Database**: SQLite for single-machine; PostgreSQL for production
- **Parallel Processing**: Use asyncio for multiple file processing

## Limitations & Future Enhancements

### Current Limitations
- Single tender processing (no batch operations)
- No multi-language support
- Limited to 100MB file size
- No digital signature verification

### Planned Features
- [ ] Batch tender processing
- [ ] Multi-language NER
- [ ] PDF digital signatures
- [ ] Integration with government portals
- [ ] Machine learning model fine-tuning
- [ ] Real-time collaboration UI
- [ ] Advanced analytics dashboard
- [ ] API rate limiting & authentication

## Security

- All OCR, NER, and LLM processing happens server-side
- No sensitive data stored in logs
- Hash chain prevents audit tampering
- Environment variables for sensitive configs
- Input validation on all endpoints

## License

This project is a reference implementation. Modify as needed for your jurisdiction.

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f app`
2. Review API docs: http://localhost:8000/docs
3. Check test cases for usage examples
4. Consult README files in each module

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request

---

**Version:** 1.0.0  
**Last Updated:** January 2024  
**Status:** Production Ready
