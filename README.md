# AI Project Intelligence & Risk Advisor

An AI-powered project intelligence platform built with **Python** and **Streamlit**. It transforms scattered project artifacts—proposals, SRS documents, meeting notes, sprint updates, and task trackers—into a unified, queryable knowledge base that extracts project scope, identifies risks and blockers, generates missing documentation, and scores overall project health.

---

## Problem Statement & Objective

Software teams and student project groups often struggle with incomplete planning, missed deadlines, and undetected risks because critical insights are buried across multiple unstructured files. **AI Project Intelligence & Risk Advisor** replaces reactive problem-solving with proactive project intelligence by ingesting varied project artifacts and providing automated analysis, documentation generation, and evidence-grounded Q&A.

---

## Key Modules & Capabilities

- **Document Ingestion & Knowledge Base:** Parses `PDF`, `DOCX`, `CSV`, `TXT`, `XLSX`, and `XLS` files with duplicate-file detection and incremental upload support.
- **RAG Retrieval Pipeline:** Chunks extracted text with source metadata and builds a local **TF-IDF + Cosine Similarity** retrieval index.
- **Scope & Deliverable Extraction:** Identifies project objectives, milestones, timelines, and responsibilities.
- **Risk Detection & Delivery Forecasting:** Highlights schedule risks, dependency gaps, and delivery challenges grounded in uploaded content.
- **Blocker & Action Item Identification:** Extracts pending decisions, unresolved blockers, and assigned action items from meeting notes and status updates.
- **Documentation Generation:** Produces draft user stories, risk registers, and structured action item lists with CSV export support.
- **Project Health Scoring:** Computes an overall health score with a dimension-wise breakdown (scope clarity, timeline risk, and blocker count).
- **Grounded Conversational Assistant:** Answers natural-language project queries (*"Are we on track?"*, *"What are our biggest risks?"*) strictly from uploaded evidence (supports offline deterministic mode as well as optional **Google Gemini** and **OpenAI** APIs).
- **Insights & Risk Summary Dashboard:** Visualizes project health, extracted scope, risks, blockers, and indexed document chunks in one interface.

---

## Development Milestones

- **Milestone 1 (Weeks 1–2):** System architecture design, multi-format document ingestion (`PDF`, `DOCX`, `CSV`, `TXT`), text chunking, and local retrieval indexing.
- **Milestone 2 (Weeks 3–4):** Implementation and validation of Scope/Deliverable, Risk/Forecasting, and Blocker/Action Item extraction modules.
- **Milestone 3 (Weeks 5–6):** Automated documentation generation (user stories, risk register), dimension-wise project health scoring, and grounded conversational Q&A assistant.
- **Milestone 4 (Weeks 7–8):** Unified insights dashboard, incremental document uploads, end-to-end testing, and technical documentation.

---

## Tech Stack

- **Frontend:** Streamlit
- **Data Processing & Retrieval:** Pandas, NumPy, Scikit-learn (TF-IDF, Cosine Similarity)
- **Document Parsing:** PyMuPDF (`fitz`), `python-docx`, OpenPyXL, `xlrd`
- **Optional LLM Integration:** Google Gemini API, OpenAI API

---

## Project Structure

```text
AI-Project-Intelligence-Risk-Advisor/
├── ai_project_advisor/
│   ├── .streamlit/
│   │   └── config.toml                  # Streamlit theme and server configuration
│   ├── modules/
│   │   ├── ingestion.py                 # Multi-format file parsing and metadata extraction
│   │   ├── rag_pipeline.py              # Text chunking and TF-IDF retrieval indexing
│   │   ├── agents.py                    # Scope, risk, blocker, documentation, and Q&A logic
│   │   └── scoring.py                   # Dimension-wise heuristic health scoring
│   ├── sample_project_data/             # Sample proposal, sprint notes, tracker, and report
│   ├── app.py                           # Main Streamlit application
│   └── requirements.txt                 # Python dependencies
└── README.md
```

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com
cd AI-Project-Intelligence-Risk-Advisor/ai_project_advisor
```

### 2. Create and activate a virtual environment
**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Run the application
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## Usage

1. **Upload Artifacts:** Upload project documents via the sidebar or load the built-in files from `sample_project_data/`.
2. **Explore Analysis:** Review extracted scope, milestones, risks, blockers, draft user stories, and the health score breakdown across the dashboard.
3. **Query the Assistant:** Ask questions in the **Grounded Project Assistant** tab. Optionally add a **Google Gemini** or **OpenAI** API key in the sidebar for LLM-synthesized answers; otherwise, the app runs fully offline using deterministic rules.

---

## Implementation Notes

- **Offline Mode:** Uses local TF-IDF lexical retrieval and deterministic rules; extracted risks, draft stories, and health scores are decision-support aids requiring stakeholder verification.
- **PDF Support:** Supports text-based PDFs only (scanned/image-only PDFs require external OCR).
- **Session Persistence:** Uploaded files and indexes persist in memory during the active Streamlit session.

---

*Developed as part of the Infosys Springboard Virtual Internship 7.0.*
