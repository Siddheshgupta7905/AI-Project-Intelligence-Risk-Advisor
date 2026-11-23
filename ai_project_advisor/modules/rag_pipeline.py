from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ProjectKnowledgeBase:
    """Local retrieval index. TF-IDF is lexical retrieval, not neural embeddings."""
    def __init__(self,chunk_size:int=750,overlap:int=120):
        if chunk_size<100 or overlap<0 or overlap>=chunk_size: raise ValueError("Require chunk_size >= 100 and 0 <= overlap < chunk_size.")
        self.chunk_size,self.overlap=chunk_size,overlap
        self.chunks=[]; self.vectorizer=None; self.matrix=None
    def _chunk_text(self,doc):
        text=doc["text"]; lines=text.splitlines()
        pieces=[]
        if doc["source_file"].lower().endswith((".csv",".xlsx",".xls")):
            batch=[]; size=0
            for line in lines:
                if size+len(line)>self.chunk_size and batch: pieces.append("\\n".join(batch)); batch=[]; size=0
                batch.append(line); size+=len(line)
            if batch:pieces.append("\\n".join(batch))
        else:
            start=0
            while start<len(text):
                end=min(start+self.chunk_size,len(text)); pieces.append(text[start:end].strip())
                if end==len(text):break
                start=end-self.overlap
        return [{"chunk_id":f"{doc['content_hash'][:12]}_{i+1}","source_file":doc["source_file"],"doc_type":doc["doc_type"],"doc_date":doc["doc_date"],"raw_text":p,"formatted_text":f"[Source: {doc['source_file']} | Type: {doc['doc_type']} | Date: {doc['doc_date']} | Chunk {i+1}]\\n{p}"} for i,p in enumerate(pieces) if p]
    def build_index(self,documents):
        self.chunks=[c for d in documents for c in self._chunk_text(d)]
        if not self.chunks:self.vectorizer=self.matrix=None;return 0
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2),stop_words="english",max_features=12000,sublinear_tf=True)
        try:self.matrix=self.vectorizer.fit_transform([c["formatted_text"] for c in self.chunks])
        except ValueError:
            self.vectorizer=TfidfVectorizer(token_pattern=r"(?u)\\b\\w+\\b")
            self.matrix=self.vectorizer.fit_transform([c["formatted_text"] for c in self.chunks])
        return len(self.chunks)
    def retrieve(self,query,top_k=5):
        if not self.chunks or self.matrix is None or not query.strip():return []
        q=self.vectorizer.transform([query]); scores=cosine_similarity(q,self.matrix).ravel()
        order=np.argsort(scores)[::-1][:max(1,top_k)]
        return [{**self.chunks[i],"score":float(scores[i])} for i in order if scores[i]>0]
    def get_full_context(self,max_chars=18000):
        out=[]; total=0
        for c in self.chunks:
            s=c["formatted_text"]
            if total+len(s)>max_chars:break
            out.append(s);total+=len(s)
        return "\\n\\n---\\n\\n".join(out)
