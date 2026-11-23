import json, re
from backend.app.rag.vector_store import search
from backend.app.llm.providers import gemini_chat, openai_chat, openrouter_chat

PROVIDERS = {"gemini": gemini_chat, "openrouter": openrouter_chat, "openai": openai_chat}


def call_llm(messages, preferred=None):
    import os

    first = (
        preferred or os.getenv("LLM_PROVIDER", "gemini")
    ).strip().lower()

    if first not in PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {first}")

    fallback_enabled = (
        os.getenv("LLM_FALLBACK_ENABLED", "false").strip().lower()
        == "true"
    )

    if fallback_enabled:
        order = [first] + [
            p for p in PROVIDERS if p != first
        ]
    else:
        order = [first]

    errors = []

    for name in order:
        try:
            response = PROVIDERS[name](messages)
            return response, name

        except Exception as exc:
            if hasattr(exc, "response") and exc.response is not None:
                detail = (
                    f"HTTP {exc.response.status_code}: "
                    f"{exc.response.text[:1000]}"
                )
            else:
                detail = str(exc)[:1000]

            errors.append(f"{name}: {type(exc).__name__}: {detail}")

    raise RuntimeError(
        "No configured LLM provider succeeded: "
        + "; ".join(errors)
    )


def parse_json(raw):
    match = re.search(r"\{.*\}", raw, re.S)
    return json.loads(match.group(0) if match else raw)

def extract_resume_profile(resume_text: str, role: str) -> dict:
    messages = [
      {"role":"system","content":"Extract a factual candidate profile from the resume. Do not invent details. Return only valid JSON with keys skills (array), technologies (array), projects (array), domains (array), experience_summary (string), role_gaps (array)."},
      {"role":"user","content":f"Target role: {role}\nResume:\n{resume_text[:18000]}"}
    ]
    raw, provider = call_llm(messages)
    profile = parse_json(raw)
    profile["_provider"] = provider
    return profile

def grounded_question(user_id, role, profile, previous_answers, difficulty="medium"):
    skills = ", ".join(profile.get("skills", [])[:12])
    tech = ", ".join(profile.get("technologies", [])[:12])
    focus = f"Target role: {role}. Candidate skills: {skills}. Technologies: {tech}. Difficulty: {difficulty}."
    if previous_answers:
        focus += "\nPrevious answers (avoid repeating; probe relevant gaps):\n" + "\n".join(previous_answers[-3:])
    hits = search(user_id, focus, limit=8, role=role)
    if not hits:
        raise ValueError("No textbook evidence found. Upload and index the assignment's role-specific books first.")
    evidence = [{"id":i,"source":h.get("source","Unknown"),"chunk_index":h.get("chunk_index"),"text":str(h.get("text",""))[:1800]} for i,h in enumerate(hits,1)]
    messages = [
      {"role":"system","content":"You are a rigorous technical interviewer. Generate exactly one non-generic technical interview question grounded in the supplied textbook evidence and tailored to the candidate resume and role. Do not ask about facts absent from evidence. Return ONLY JSON with keys question, topic, difficulty, expected_points (array of 3-5), evidence_ids (array of integer ids), rationale. Use only valid evidence_ids."},
      {"role":"user","content":focus+"\n\nRetrieved textbook evidence:\n"+json.dumps(evidence,ensure_ascii=False)}
    ]
    raw, provider = call_llm(messages)
    data = parse_json(raw)
    valid = {e["id"] for e in evidence}; ids = data.get("evidence_ids", [])
    if not data.get("question") or not ids or not set(ids).issubset(valid):
        raise ValueError("Generated question failed evidence traceability validation.")
    data["provider"] = provider
    data["evidence"] = [e for e in evidence if e["id"] in ids]
    return data

def evaluate_answer(role, question, answer, expected_points):
    messages = [
      {"role":"system","content":"Evaluate the candidate answer fairly against the question and expected points. Return only JSON: score (0-100 integer), strengths (array), gaps (array), feedback (string), follow_up_focus (string). Do not invent facts."},
      {"role":"user","content":json.dumps({"role":role,"question":question,"answer":answer,"expected_points":expected_points})}
    ]
    raw, provider = call_llm(messages)
    result = parse_json(raw); result["provider"] = provider
    return result
