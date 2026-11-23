import json, re


def call_llm(prompt, system_instruction, provider="Demo Mode (Offline Deterministic)", api_key="", model_name=""):
    if not api_key.strip():
        return ""
    if provider == "Google Gemini":
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key.strip())
        resp = client.models.generate_content(model=model_name.strip() or "gemini-2.5-flash", contents=prompt,
            config=types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.1))
        return resp.text or ""
    if provider == "OpenAI":
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip())
        resp = client.chat.completions.create(model=model_name.strip() or "gpt-4o-mini",
            messages=[{"role":"system","content":system_instruction},{"role":"user","content":prompt}], temperature=0.1)
        return resp.choices[0].message.content or ""
    return ""


def _sentences(text):
    return [re.sub(r"\s+", " ", x).strip(" -•*\t") for x in re.split(r"(?<=[.!?])\s+|\n+", text) if len(x.strip()) > 18]


def _rule_based_analysis(documents):
    deliverables, milestones, risks, blockers, actions, stories = [], [], [], [], [], []
    risk_terms = ("delay", "delayed", "missed", "overdue", "behind schedule", "dependency", "blocked", "blocker", "risk", "failure", "unassigned", "pending", "not started", "issue", "unavailable")
    blocker_terms = ("blocked by", "waiting for", "cannot proceed", "unable to", "access pending", "credential pending", "unresolved")
    action_terms = ("will ", "must ", "should ", "action:", "to do", "need to", "please ", "assign ", "complete ", "provide ", "resolve ", "obtain ")
    scope_terms = ("deliverable", "shall ", "must support", "the system will", "the platform will", "objective", "milestone", "phase ")
    for doc in documents:
        src = doc["source_file"]
        for line in _sentences(doc["text"]):
            low = line.lower()
            if any(t in low for t in scope_terms) and len(line) < 240:
                deliverables.append({"item": line, "source": src, "status": "Extracted – verify"})
            if "milestone" in low or re.search(r"\bphase\s+[0-9ivx]+", low):
                milestones.append({"milestone": line, "source": src})
            if any(t in low for t in risk_terms):
                severity = "High" if any(t in low for t in ("missed", "overdue", "blocked", "critical", "cannot proceed", "severe")) else "Medium"
                risks.append({"risk_id": f"R-{len(risks)+1:02d}", "title": line[:140], "severity": severity,
                    "likelihood": "Requires review", "impact": "Potential schedule, scope, quality or delivery impact; assess with project owner.",
                    "mitigation": "Review evidence, assign an owner, agree a mitigation and due date.", "source": src, "evidence": line})
            if any(t in low for t in blocker_terms):
                blockers.append({"blocker": line, "owner": "Not specified in source", "status": "Potential blocker – verify", "source": src, "evidence": line})
            if any(t in low for t in action_terms) and len(line) < 260:
                actions.append({"action": line, "assignee": "Not specified in source", "priority": "High" if any(t in low for t in ("urgent", "immediately", "critical", "asap")) else "Medium",
                    "due": "Not specified in source", "source": src, "evidence": line})
    def dedup(items, key):
        out, seen = [], set()
        for item in items:
            k = (item.get(key, "").lower(), item.get("source", ""))
            if k not in seen:
                seen.add(k); out.append(item)
        return out
    deliverables = dedup(deliverables, "item")[:30]
    milestones = dedup(milestones, "milestone")[:20]
    risks = dedup(risks, "evidence")[:30]
    blockers = dedup(blockers, "evidence")[:30]
    actions = dedup(actions, "evidence")[:40]
    for i, item in enumerate(deliverables[:12], 1):
        stories.append({"id": f"US-{i:02d}", "role": "Project stakeholder (confirm role)",
            "story": f"As a project stakeholder, I want {item['item'].rstrip('.')} so that the stated project requirement is addressed.",
            "acceptance_criteria": "Derive measurable acceptance criteria with the project owner; not specified in source.",
            "source": item["source"], "status": "Draft – review required"})
    if not deliverables:
        deliverables = [{"item": "No explicit deliverable statements were confidently extracted. Review source documents.",
                         "source": documents[0]["source_file"] if documents else "N/A", "status": "Needs review"}]
    summary = (f"Analyzed {len(documents)} document(s). Identified {len(risks)} potential risk signal(s), "
               f"{len(blockers)} potential blocker(s), and {len(actions)} candidate action item(s). "
               "These are rule-based findings requiring human verification; no calibrated delivery probability is produced.")
    return {"scope": {"deliverables": deliverables, "milestones": milestones, "scope_creep": []}, "risks": risks,
            "blockers": blockers, "action_items": actions, "user_stories": stories, "forecast_summary": summary,
            "analysis_mode": "Offline rule-based; review required"}


def _parse_json(raw):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.I)
    return json.loads(raw)


def run_multi_agent_pipeline(documents, context_text, provider="Demo Mode (Offline Deterministic)", api_key="", model_name=""):
    fallback = _rule_based_analysis(documents)
    if provider == "Demo Mode (Offline Deterministic)" or not api_key.strip():
        return fallback
    schema = ('Return JSON only with keys scope{deliverables:[{item,source,status}],milestones:[{milestone,source}],scope_creep:[{item,reason,source}]}, '
              'risks:[{risk_id,title,severity,likelihood,impact,mitigation,source,evidence}], blockers:[{blocker,owner,status,source,evidence}], '
              'action_items:[{action,assignee,priority,due,source,evidence}], user_stories:[{id,role,story,acceptance_criteria,source,status}], forecast_summary:string. '
              'Use only facts supported by source text. Mark absent owner/date as Not specified in source. Never invent facts or delivery probabilities. Cite source filenames and evidence.')
    try:
        raw = call_llm(schema + "\n\nSOURCE DOCUMENTS:\n" + context_text,
            "You are a cautious project analyst. Distinguish risk, current blocker, dependency and open task. Never invent evidence.", provider, api_key, model_name)
        result = _parse_json(raw)
        for key in ("scope", "risks", "blockers", "action_items", "user_stories", "forecast_summary"):
            if key not in result: raise ValueError(f"Missing response field: {key}")
        result.setdefault("analysis_mode", f"{provider} – LLM-assisted; verify outputs")
        return result
    except Exception as exc:
        fallback["analysis_mode"] = f"Offline fallback after LLM error: {type(exc).__name__}"
        fallback["forecast_summary"] += " LLM response unavailable; deterministic local analysis was used."
        return fallback


def answer_project_question(question, retrieved_chunks, provider="Demo Mode (Offline Deterministic)", api_key="", model_name=""):
    if not retrieved_chunks:
        return "I couldn't find matching content in the indexed project documents. Try a more specific question or upload the relevant artifact."
    context = "\n\n".join(c["formatted_text"] for c in retrieved_chunks)
    if provider != "Demo Mode (Offline Deterministic)" and api_key.strip():
        prompt = f"Answer only from retrieved evidence. If absent, say it is not specified. Cite source filenames.\n\nQUESTION: {question}\n\nEVIDENCE:\n{context}"
        try:
            answer = call_llm(prompt, "You are a grounded project assistant. Do not infer facts beyond evidence.", provider, api_key, model_name)
            if answer.strip(): return answer
        except Exception:
            pass
    excerpts = [f"**{c['source_file']}** ({c['doc_date']}, retrieval score {c['score']:.2f})\n> {c['raw_text'][:650]}" for c in retrieved_chunks[:4]]
    return "I found these relevant passages in the uploaded documents. They are evidence excerpts, not a verified conclusion:\n\n" + "\n\n".join(excerpts)
