import io, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from modules.ingestion import process_uploaded_files
from modules.rag_pipeline import ProjectKnowledgeBase
from modules.agents import run_multi_agent_pipeline, answer_project_question
from modules.scoring import calculate_project_health

class CoreTests(unittest.TestCase):
    def test_txt_ingestion(self):
        docs=process_uploaded_files([{"name":"meeting_notes.txt","bytes":b"Date: 2026-11-18\\nThe project milestone is delayed because staging access is pending."}])
        self.assertEqual(len(docs),1); self.assertIn("delayed",docs[0]["text"])
    def test_incremental_index_rebuild(self):
        docs=process_uploaded_files([{"name":"a.txt","bytes":b"The platform will provide document search and project reporting."}])
        kb=ProjectKnowledgeBase(); self.assertGreater(kb.build_index(docs),0)
        docs2=docs+process_uploaded_files([{"name":"b.txt","bytes":b"A new meeting note records an unresolved deployment dependency."}])
        self.assertGreater(kb.build_index(docs2),1)
        self.assertEqual({c['source_file'] for c in kb.chunks},{"a.txt","b.txt"})
    def test_retrieval_and_grounded_answer(self):
        docs=process_uploaded_files([{"name":"status.txt","bytes":b"The deployment is blocked while cloud credentials are pending."}])
        kb=ProjectKnowledgeBase();kb.build_index(docs); hits=kb.retrieve("cloud credentials blocked",3)
        self.assertTrue(hits); self.assertIn("status.txt",answer_project_question("deployment",hits))
    def test_analysis_schema_and_health_bounds(self):
        docs=process_uploaded_files([{"name":"plan.txt","bytes":b"The system will support project document uploads. The deployment is delayed because access is pending. The team must resolve access."}])
        a=run_multi_agent_pipeline(docs,"", "Demo Mode (Offline Deterministic)")
        for key in ("scope","risks","blockers","action_items","user_stories","forecast_summary"): self.assertIn(key,a)
        h=calculate_project_health(a); self.assertGreaterEqual(h['total_score'],0);self.assertLessEqual(h['total_score'],100)
    def test_duplicate_hash(self):
        a=process_uploaded_files([{"name":"same.txt","bytes":b"same content"}])[0]
        b=process_uploaded_files([{"name":"renamed.txt","bytes":b"same content"}])[0]
        self.assertEqual(a['content_hash'],b['content_hash'])

if __name__=="__main__":unittest.main()
