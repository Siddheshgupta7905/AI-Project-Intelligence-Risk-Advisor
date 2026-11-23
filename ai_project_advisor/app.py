import os, hashlib
import pandas as pd
import streamlit as st
from modules.ingestion import process_uploaded_files, SUPPORTED_EXTENSIONS
from modules.rag_pipeline import ProjectKnowledgeBase
from modules.agents import run_multi_agent_pipeline, answer_project_question
from modules.scoring import calculate_project_health

st.set_page_config(page_title="AI Project Intelligence & Risk Advisor", page_icon="🧭", layout="wide")
st.markdown("""<style>
.stApp{background:#F5F8FC;color:#172B4D} section[data-testid="stSidebar"]{background:#EAF1F8}
.hero{background:linear-gradient(135deg,#087F8C,#065F69);padding:1.35rem 1.6rem;border-radius:12px;margin-bottom:1rem;color:white}
.hero h1,.hero p{color:white!important;margin:0}.hero p{margin-top:.35rem}
.kpi{background:#EAF1F8;border:1px solid #D3E2F0;border-left:5px solid #087F8C;border-radius:10px;padding:1rem}
.kpi small{font-weight:700;text-transform:uppercase}.kpi strong{display:block;font-size:1.7rem;color:#087F8C}
</style>""", unsafe_allow_html=True)

# Persistent session state for incremental uploads during the active session.
for key, default in {"documents": [], "kb": None, "analysis": None, "health": None, "chat_history": [], "file_hashes": set(), "last_error": None}.items():
    if key not in st.session_state: st.session_state[key] = default


def load_samples():
    folder = os.path.join(os.path.dirname(__file__), "sample_project_data")
    items=[]
    if os.path.isdir(folder):
        for name in sorted(os.listdir(folder)):
            path=os.path.join(folder,name)
            if os.path.isfile(path) and os.path.splitext(name)[1].lower() in SUPPORTED_EXTENSIONS:
                with open(path,"rb") as f: items.append({"name":name,"bytes":f.read()})
    return items


def ingest_and_analyze(raw_files, replace=False):
    new_docs=process_uploaded_files(raw_files)
    current=[] if replace else list(st.session_state.documents)
    known=set() if replace else set(st.session_state.file_hashes)
    added=[]; duplicates=[]
    for doc in new_docs:
        digest=doc.get("content_hash") or hashlib.sha256(doc["text"].encode()).hexdigest()
        doc["content_hash"]=digest
        if digest in known:
            duplicates.append(doc["source_file"]); continue
        known.add(digest); added.append(doc)
    combined=current+added
    if not combined: raise ValueError("No readable documents were available to index.")
    kb=ProjectKnowledgeBase()
    chunks=kb.build_index(combined)
    context=kb.get_full_context()
    analysis=run_multi_agent_pipeline(combined,context,provider=provider,api_key=api_key,model_name=model_name)
    health=calculate_project_health(analysis)
    st.session_state.documents=combined; st.session_state.file_hashes=known
    st.session_state.kb=kb; st.session_state.analysis=analysis; st.session_state.health=health
    st.session_state.chat_history=[]
    return len(added),len(duplicates),chunks

with st.sidebar:
    st.header("📂 Project Artifacts")
    uploaded=st.file_uploader("Add project documents",type=["pdf","docx","csv","txt","xlsx","xls"],accept_multiple_files=True)
    c1,c2=st.columns(2)
    with c1: add_clicked=st.button("➕ Add & Analyze",use_container_width=True,disabled=not uploaded)
    with c2: sample_clicked=st.button("Load Sample Data",use_container_width=True)
    if st.button("Clear Project Session",use_container_width=True):
        for k,v in {"documents":[],"kb":None,"analysis":None,"health":None,"chat_history":[],"file_hashes":set(),"last_error":None}.items(): st.session_state[k]=v
        st.rerun()
    st.divider(); st.subheader("⚙️ Intelligence Engine")
    provider=st.selectbox("AI Provider",["Demo Mode (Offline Deterministic)","Google Gemini","OpenAI"])
    api_key=""; model_name=""
    if provider!="Demo Mode (Offline Deterministic)":
        api_key=st.text_input("API Key",type="password")
        model_name=st.text_input("Model Name",value="gemini-2.5-flash" if provider=="Google Gemini" else "gpt-4o-mini")
    st.caption(f"Indexed documents: {len(st.session_state.documents)}")
    for d in st.session_state.documents: st.caption(f"• {d['source_file']}")

if add_clicked:
    try:
        with st.spinner("Adding new documents, updating the index and refreshing analysis…"):
            added,dupes,chunks=ingest_and_analyze(uploaded)
        st.success(f"Added {added} new document(s); skipped {dupes} duplicate(s). Knowledge base now contains {len(st.session_state.documents)} documents and {chunks} chunks.")
    except Exception as e:
        st.error(f"Upload failed: {e}")
if sample_clicked:
    try:
        samples=load_samples()
        if not samples: st.warning("No supported sample documents were found in sample_project_data.")
        else:
            with st.spinner("Loading sample documents and building the project knowledge base…"):
                added,dupes,chunks=ingest_and_analyze(samples)
            st.success(f"Sample load complete: {added} added, {dupes} duplicates skipped, {chunks} chunks indexed.")
    except Exception as e: st.error(f"Sample loading failed: {e}")

st.markdown('<div class="hero"><h1>🧭 AI Project Intelligence & Risk Advisor</h1><p>Document ingestion • Retrieval • Scope and risk insights • Action tracking • Project Q&A</p></div>',unsafe_allow_html=True)
if not st.session_state.analysis:
    st.info("Upload project artifacts or load the bundled sample dataset to begin. New uploads are appended to the current session knowledge base; identical files are skipped.")
    st.stop()
analysis=st.session_state.analysis; health=st.session_state.health
st.caption(f"Analysis mode: {analysis.get('analysis_mode','Not specified')} | {health.get('method','')}")
cols=st.columns(4)
metrics=[("Project Health",f"{health['total_score']}/100",health['status_label']),("High Risks",health['counts']['high_risks'],f"{len(analysis.get('risks',[]))} potential signals"),("Active / Potential Blockers",health['counts']['active_blockers'],f"{len(analysis.get('action_items',[]))} candidate actions"),("Deliverables",health['counts']['deliverables'],f"{health['counts']['scope_creep']} scope alerts")]
for col,(label,value,sub) in zip(cols,metrics):
    with col: st.markdown(f'<div class="kpi"><small>{label}</small><strong>{value}</strong>{sub}</div>',unsafe_allow_html=True)
st.info(analysis.get("forecast_summary","No summary available."))

T1,T2,T3,T4,T5=st.tabs(["📊 Health & Scope","⚠️ Risks & Blockers","📝 Generated Docs","💬 Assistant","🔍 Knowledge Base"])
with T1:
    left,right=st.columns([1,1.4])
    with left:
        st.subheader("Project Health Breakdown")
        for name,val in health["dimensions"].items(): st.write(f"**{name}:** {val['score']}/{val['max']} ({val['pct']}%)"); st.progress(val['pct']/100)
        st.caption(health.get("method",""))
        st.subheader("Scope Change Signals")
        for item in analysis.get("scope",{}).get("scope_creep",[]): st.warning(f"{item.get('item')} — {item.get('reason')} ({item.get('source')})")
        if not analysis.get("scope",{}).get("scope_creep"): st.info("No explicit scope-creep finding was produced. This does not prove that scope is unchanged.")
    with right:
        st.subheader("Extracted Deliverables"); df=pd.DataFrame(analysis.get("scope",{}).get("deliverables",[]))
        if not df.empty: st.dataframe(df,use_container_width=True,hide_index=True)
        st.subheader("Milestones"); df=pd.DataFrame(analysis.get("scope",{}).get("milestones",[]))
        if not df.empty: st.dataframe(df,use_container_width=True,hide_index=True)
with T2:
    st.subheader("Potential Risks — review against source evidence")
    df=pd.DataFrame(analysis.get("risks",[]))
    if not df.empty: st.dataframe(df,use_container_width=True,hide_index=True)
    else: st.info("No risk signals were extracted from the current documents.")
    a,b=st.columns(2)
    with a:
        st.subheader("Blockers / Dependencies"); df=pd.DataFrame(analysis.get("blockers",[]))
        if not df.empty: st.dataframe(df,use_container_width=True,hide_index=True)
        else: st.info("No blocker signals were extracted.")
    with b:
        st.subheader("Candidate Action Items"); df=pd.DataFrame(analysis.get("action_items",[]))
        if not df.empty: st.dataframe(df,use_container_width=True,hide_index=True)
        else: st.info("No action-item signals were extracted.")
with T3:
    st.subheader("Generated Project Documentation")
    st.caption("Generated user stories are drafts. Review and approve them before using them as project commitments.")
    for label,key,filename in [("User Stories","user_stories","user_stories.csv"),("Risk Register","risks","risk_register.csv"),("Action Items","action_items","action_items.csv")]:
        df=pd.DataFrame(analysis.get(key,[]))
        st.markdown(f"**{label}**")
        if not df.empty:
            st.dataframe(df,use_container_width=True,hide_index=True)
            st.download_button(f"Download {label} CSV",df.to_csv(index=False).encode("utf-8-sig"),filename,"text/csv",key=f"download_{key}")
        else: st.info(f"No {label.lower()} were generated.")
with T4:
    st.subheader("Grounded Project Assistant")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])
    question=st.chat_input("Ask about project scope, risks, blockers, deliverables or schedule…")
    if question:
        st.session_state.chat_history.append({"role":"user","content":question})
        with st.chat_message("user"): st.markdown(question)
        retrieved=st.session_state.kb.retrieve(question,top_k=5)
        answer=answer_project_question(question,retrieved,provider,api_key,model_name)
        st.session_state.chat_history.append({"role":"assistant","content":answer})
        with st.chat_message("assistant"):
            st.markdown(answer)
            if retrieved:
                with st.expander("Retrieved evidence"): 
                    for chunk in retrieved: st.markdown(f"**{chunk['source_file']}** · score {chunk['score']:.3f}"); st.code(chunk['raw_text'])
with T5:
    st.subheader("Indexed Documents & Chunk Explorer")
    st.write(f"**{len(st.session_state.documents)} documents · {len(st.session_state.kb.chunks)} chunks**")
    for doc in st.session_state.documents:
        with st.expander(f"{doc['source_file']} · {doc['doc_type']} · {doc['doc_date']}"):
            st.caption(f"{doc['char_count']:,} extracted characters")
            st.text(doc['text'][:20000])
    st.markdown("**Search indexed evidence**")
    query=st.text_input("Enter keywords or a question",key="kb_search")
    if query:
        for chunk in st.session_state.kb.retrieve(query,top_k=8):
            st.markdown(f"**{chunk['source_file']}** · relevance {chunk['score']:.3f}")
            st.write(chunk['raw_text'])
