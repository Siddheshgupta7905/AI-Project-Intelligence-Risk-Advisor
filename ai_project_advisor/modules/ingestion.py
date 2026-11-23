import io, os, re
from typing import Any, Dict, List
import pandas as pd
import fitz
from docx import Document

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt", ".xlsx", ".xls"}

def infer_doc_type(filename: str) -> str:
    n=filename.lower()
    if any(x in n for x in ("proposal","srs","scope","requirement")): return "Project Proposal / Specification"
    if any(x in n for x in ("meeting","notes","sync","minutes")): return "Meeting Notes"
    if any(x in n for x in ("task","tracker","backlog")) or n.endswith(".csv"): return "Task Tracker"
    if any(x in n for x in ("progress","update","report","status")): return "Progress Report"
    return "Project Document"

def infer_doc_date(filename: str, text: str) -> str:
    pats=[r"(?:Reporting Date|Document Date|Date)\\s*[:\\-]\\s*([A-Za-z]+\\s+\\d{1,2},?\\s+\\d{4})",
          r"(?:Reporting Date|Document Date|Date)\\s*[:\\-]\\s*(\\d{4}-\\d{2}-\\d{2})",
          r"(20\\d{2}-\\d{2}-\\d{2})"]
    for p in pats:
        m=re.search(p,text[:1500],re.I)
        if m:return m.group(1)
    return "Unspecified"

def parse_pdf(b:bytes)->str:
    with fitz.open(stream=b,filetype="pdf") as pdf:
        return "\\n\\n".join(f"[Page {i+1}]\\n{p.get_text('text').strip()}" for i,p in enumerate(pdf) if p.get_text("text").strip())

def parse_docx(b:bytes)->str:
    d=Document(io.BytesIO(b)); out=[p.text.strip() for p in d.paragraphs if p.text.strip()]
    for ti,t in enumerate(d.tables,1):
        out.append(f"[Table {ti}]")
        for row in t.rows: out.append(" | ".join(c.text.strip() for c in row.cells))
    return "\\n".join(out)

def parse_csv(b:bytes)->str:
    df=pd.read_csv(io.BytesIO(b), keep_default_na=False)
    return "\\n".join("Record -> "+"; ".join(f"{c}: {row[c]}" for c in df.columns) for _,row in df.iterrows()) or "CSV contains headers but no data rows.\\nColumns: "+", ".join(df.columns)

def parse_excel(b:bytes)->str:
    sheets=pd.read_excel(io.BytesIO(b),sheet_name=None)
    blocks=[]
    for name,df in sheets.items():
        blocks.append(f"[Worksheet: {name}]")
        if df.empty: blocks.append("No data rows.")
        else:
            df=df.fillna("")
            blocks.extend("Record -> "+"; ".join(f"{c}: {row[c]}" for c in df.columns) for _,row in df.iterrows())
    return "\\n".join(blocks)

def parse_txt(b:bytes)->str:return b.decode("utf-8-sig",errors="replace").strip()

def process_uploaded_files(uploaded_files:List[Any])->List[Dict[str,Any]]:
    docs=[]
    for item in uploaded_files:
        name=item["name"] if isinstance(item,dict) else item.name
        data=item["bytes"] if isinstance(item,dict) else item.getvalue()
        ext=os.path.splitext(name)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS: raise ValueError(f"Unsupported file type: {name}")
        parsers={".pdf":parse_pdf,".docx":parse_docx,".csv":parse_csv,".txt":parse_txt,".xlsx":parse_excel,".xls":parse_excel}
        try:text=parsers[ext](data)
        except Exception as e: raise ValueError(f"Could not read {name}: {e}") from e
        if not text.strip(): raise ValueError(f"No extractable text found in {name}. Scanned PDFs may require OCR.")
        docs.append({"source_file":name,"doc_type":infer_doc_type(name),"doc_date":infer_doc_date(name,text),"text":text,"char_count":len(text),"content_hash":__import__("hashlib").sha256(data).hexdigest()})
    return docs
