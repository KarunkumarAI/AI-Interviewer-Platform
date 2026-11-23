import json, uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.auth.deps import current_user
from backend.app.db.deps import get_db
from backend.app.db.models import User, InterviewSession, InterviewQuestion, InterviewAnswer, InterviewStatus
from backend.app.documents.extractors import extract
from backend.app.interviews.schemas import InterviewStart, AnswerIn
from backend.app.interviews.service import extract_resume_profile, grounded_question, evaluate_answer

router = APIRouter(prefix="/interviews", tags=["interviews"])
MAX_RESUME_BYTES = 8 * 1024 * 1024

def owned_session(db, user, session_id):
    row = db.scalar(select(InterviewSession).where(InterviewSession.id == session_id, InterviewSession.user_id == user.id))
    if not row: raise HTTPException(404, "Interview session not found")
    return row

def make_question(db, session, profile, previous_answers):
    try:
        data = grounded_question(session.user_id, session.role, profile, previous_answers)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    seq = db.scalar(select(InterviewQuestion).where(InterviewQuestion.session_id == session.id).order_by(InterviewQuestion.sequence.desc()).limit(1))
    number = (seq.sequence + 1) if seq else 1
    q = InterviewQuestion(session_id=session.id, sequence=number, question=data["question"], topic=data.get("topic","General"), difficulty=data.get("difficulty","medium"), expected_points=json.dumps(data.get("expected_points",[])), evidence=json.dumps(data["evidence"]), rationale=data.get("rationale",""), provider=data["provider"])
    db.add(q); db.flush()
    return q

def question_out(q):
    return {"id":str(q.id),"sequence":q.sequence,"question":q.question,"topic":q.topic,"difficulty":q.difficulty,"evidence":json.loads(q.evidence)}

@router.post("/resume/parse")
def parse_resume(file: UploadFile = File(...), user: User = Depends(current_user)):
    name = file.filename or "resume.pdf"
    data = file.file.read(MAX_RESUME_BYTES + 1)
    if len(data) > MAX_RESUME_BYTES: raise HTTPException(413,"Resume exceeds 8 MB limit")
    try:
        text, _ = extract(name, data)
        if len(text.strip()) < 80: raise ValueError("Resume text is too short or unreadable")
        return {"filename":name,"resume_text":text[:30000]}
    except Exception as exc:
        raise HTTPException(422, f"Could not parse resume: {exc}") from exc

@router.post("", status_code=201)
def start_interview(body: InterviewStart, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try: profile = extract_resume_profile(body.resume_text, body.role)
    except Exception as exc: raise HTTPException(502, f"Resume analysis failed: {type(exc).__name__}: {exc}") from exc
    session = InterviewSession(user_id=user.id,candidate_name=body.candidate_name,role=body.role,resume_text=body.resume_text,resume_profile=json.dumps(profile))
    db.add(session); db.flush()
    try: q = make_question(db, session, profile, [])
    except Exception: db.rollback(); raise
    db.commit()
    return {"id":str(session.id),"role":session.role,"status":session.status.value,"profile":profile,"current_question":question_out(q)}

@router.post("/{session_id}/answers", status_code=201)
def submit_answer(session_id: uuid.UUID, body: AnswerIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    session = owned_session(db,user,session_id)
    if session.status == InterviewStatus.COMPLETED: raise HTTPException(409,"Interview is already completed")
    questions = db.scalars(select(InterviewQuestion).where(InterviewQuestion.session_id==session.id).order_by(InterviewQuestion.sequence)).all()
    if not questions: raise HTTPException(409,"No interview question exists")
    current = questions[-1]
    if db.scalar(select(InterviewAnswer).where(InterviewAnswer.question_id==current.id)): raise HTTPException(409,"Answer already submitted")
    try:
        evaluation = evaluate_answer(session.role,current.question,body.answer,json.loads(current.expected_points))
    except Exception as exc: raise HTTPException(502,f"Answer evaluation failed: {type(exc).__name__}") from exc
    answer = InterviewAnswer(question_id=current.id,answer=body.answer,evaluation=json.dumps(evaluation),score=max(0,min(100,int(evaluation.get("score",0)))))
    db.add(answer); db.flush()
    if len(questions) >= 5:
        session.status=InterviewStatus.COMPLETED; next_question=None
    else:
        previous = [a.answer for a in db.scalars(select(InterviewAnswer).join(InterviewQuestion, InterviewAnswer.question_id==InterviewQuestion.id).where(InterviewQuestion.session_id==session.id).order_by(InterviewQuestion.sequence)).all()]
        try: next_question=question_out(make_question(db,session,json.loads(session.resume_profile),previous))
        except Exception as exc: db.rollback(); raise HTTPException(502,f"Next question generation failed: {type(exc).__name__}: {exc}") from exc
    db.commit()
    return {"evaluation":evaluation,"next_question":next_question,"status":session.status.value}

@router.get("/{session_id}/report")
def interview_report(session_id: uuid.UUID,user: User=Depends(current_user),db: Session=Depends(get_db)):
    session=owned_session(db,user,session_id)
    rows=db.execute(select(InterviewQuestion,InterviewAnswer).join(InterviewAnswer,InterviewAnswer.question_id==InterviewQuestion.id,isouter=True).where(InterviewQuestion.session_id==session.id).order_by(InterviewQuestion.sequence)).all()
    items=[]
    for q,a in rows:
        items.append({"sequence":q.sequence,"question":q.question,"topic":q.topic,"difficulty":q.difficulty,"answer":a.answer if a else None,"evaluation":json.loads(a.evaluation) if a else None,"evidence":json.loads(q.evidence)})
    scores=[x["evaluation"]["score"] for x in items if x["evaluation"]]
    return {"id":str(session.id),"role":session.role,"status":session.status.value,"profile":json.loads(session.resume_profile),"questions":items,"average_score":round(sum(scores)/len(scores),1) if scores else None,"answered":len(scores),"total_questions":len(items)}
