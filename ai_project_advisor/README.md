# AI Project Intelligence & Risk Advisor

A Streamlit application for ingesting project artifacts, building a local searchable knowledge base, extracting reviewable project signals, generating draft project documentation, and asking evidence-oriented questions.

## Requirements
- Python 3.10 or newer
- Internet access only for installing packages or using optional Gemini/OpenAI APIs

## Windows PowerShell setup
```powershell
cd path\to\ai_project_advisor
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Supported inputs
PDF, DOCX, CSV, TXT, XLSX and XLS. Text-based PDFs are supported; scanned/image-only PDFs require OCR and are reported as having no extractable text.

## Milestone coverage
1. **M1 – Ingestion and knowledge base:** format-specific extraction, source metadata, chunking and local TF-IDF retrieval index.
2. **M2 – Project analysis:** scope/milestone extraction and candidate risk, blocker and action-item signals with source/evidence fields.
3. **M3 – Project intelligence:** draft user stories, heuristic health indicator, evidence-oriented Q&A and insights dashboard.
4. **M4 – Completion:** incremental add-and-index workflow, duplicate-file detection, consolidated analysis, document/chunk explorer, CSV exports and test suite.

## Important implementation boundaries
- Offline retrieval uses TF-IDF lexical similarity. It is a lightweight local retrieval baseline, not a neural embedding model or a hosted vector database.
- Offline agents use deterministic text rules. Their results are candidate signals requiring human verification; they are not autonomous multi-agent reasoning or statistically calibrated delivery forecasts.
- The health score is a transparent heuristic indicator, not a validated prediction.
- User stories are drafts. Acceptance criteria, owners and due dates must be confirmed by project stakeholders when not present in source evidence.
- Gemini/OpenAI modes require the user's own API key. API failures fall back to local deterministic analysis.
- Incremental additions persist for the active Streamlit session. Clearing the session removes the in-memory project state.

## Tests
Run:
```powershell
python -m unittest discover -s tests -v
```
