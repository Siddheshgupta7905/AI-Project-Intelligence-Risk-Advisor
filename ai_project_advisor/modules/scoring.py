def calculate_project_health(analysis):
    scope = analysis.get("scope", {}); risks = analysis.get("risks", []); blockers = analysis.get("blockers", [])
    deliverables = len(scope.get("deliverables", [])); creep = len(scope.get("scope_creep", []))
    high = sum(str(r.get("severity", "")).lower() == "high" for r in risks)
    medium = sum(str(r.get("severity", "")).lower() == "medium" for r in risks)
    active = sum("resolved" not in str(b.get("status", "")).lower() for b in blockers)
    scope_score = max(0, 35 - (15 if deliverables == 0 else 0) - min(20, creep * 8))
    timeline_score = max(0, 35 - min(30, high * 7 + medium * 3))
    execution_score = max(0, 30 - min(30, active * 6))
    total = round(scope_score + timeline_score + execution_score)
    label = "Healthy" if total >= 75 else "At Risk" if total >= 50 else "Critical"
    color = "#087F8C" if total >= 75 else "#D97706" if total >= 50 else "#DC2626"
    return {"total_score": total, "status_label": label, "status_color": color,
        "dimensions": {"Scope Clarity": {"score": scope_score, "max": 35, "pct": round(scope_score/35*100)},
                       "Timeline Risk": {"score": timeline_score, "max": 35, "pct": round(timeline_score/35*100)},
                       "Blockers & Execution": {"score": execution_score, "max": 30, "pct": round(execution_score/30*100)}},
        "counts": {"deliverables": deliverables, "scope_creep": creep, "high_risks": high, "active_blockers": active},
        "method": "Heuristic indicator based on extracted counts; not a validated delivery forecast."}
