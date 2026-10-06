import os
import re
import json
import shutil
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend.models import (
    Company, JobRequirement, Skill, Candidate, ResumeUpload,
    PersonalDetail, Education, Experience, ExtractedResumeData,
    Certification, ResumeSkill, ResumeMatchingSession,
    MatchingAnalysis, SkillMatchResult, MockQuestion, CandidateAnswer, Performance
)
from backend.services.parser import extract_text_from_file
from backend.services.nlp_extractor import extract_resume_information
from backend.services.matcher import calculate_match_analysis, parse_skills_list
from backend.services.assessment import (
    generate_mock_questions_for_candidate,
    evaluate_single_answer,
    compile_overall_performance
)

# Initialize Database
init_db()

app = FastAPI(
    title="AI Resume Screening & Candidate Assessment System",
    description="From Any Document Upload to Final Evaluation – Smart Hiring Made Simple",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_resumes")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)

# ----------------- PYDANTIC SCHEMAS -----------------

class CompanyCreate(BaseModel):
    company_name: str
    industry: Optional[str] = "Technology"
    website: Optional[str] = ""
    description: Optional[str] = ""

class JobRequirementCreate(BaseModel):
    company_id: int
    job_title: str
    required_skills: List[str]
    optional_skills: Optional[List[str]] = []
    education: Optional[str] = "Bachelor's Degree in Computer Science or related"
    experience: Optional[str] = "2+ years"
    job_description: Optional[str] = ""

class AnswerSubmissionItem(BaseModel):
    question_id: int
    answer: str

class AssessmentSubmitPayload(BaseModel):
    candidate_id: int
    matching_id: Optional[int] = None
    answers: List[AnswerSubmissionItem]

# ----------------- API ROUTES -----------------

# 1. Company Endpoints
@app.get("/api/companies")
def get_companies(db: Session = Depends(get_db)):
    companies = db.query(Company).all()
    return [
        {
            "id": c.CompanyID,
            "company_name": c.CompanyName,
            "industry": c.Industry,
            "website": c.Website,
            "description": c.Description,
            "jobs_count": len(c.job_requirements)
        }
        for c in companies
    ]

@app.post("/api/companies")
def create_company(data: CompanyCreate, db: Session = Depends(get_db)):
    existing = db.query(Company).filter(Company.CompanyName == data.company_name).first()
    if existing:
        return {"id": existing.CompanyID, "company_name": existing.CompanyName, "message": "Company already exists"}
    
    comp = Company(
        CompanyName=data.company_name,
        Industry=data.industry,
        Website=data.website,
        Description=data.description
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)
    return {"id": comp.CompanyID, "company_name": comp.CompanyName, "status": "created"}

# 2. Job Requirement Endpoints
@app.get("/api/jobs")
def get_jobs(db: Session = Depends(get_db)):
    jobs = db.query(JobRequirement).all()
    res = []
    for j in jobs:
        res.append({
            "id": j.RequirementID,
            "company_id": j.CompanyID,
            "company_name": j.company.CompanyName if j.company else "Unknown Company",
            "job_title": j.JobTitle,
            "required_skills": parse_skills_list(j.RequiredSkills),
            "optional_skills": parse_skills_list(j.OptionalSkills),
            "education": j.Education,
            "experience": j.Experience,
            "job_description": j.JobDescription,
            "created_at": j.CreatedAt.isoformat() if j.CreatedAt else None
        })
    return res

@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    j = db.query(JobRequirement).filter(JobRequirement.RequirementID == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job requirement not found")
    return {
        "id": j.RequirementID,
        "company_id": j.CompanyID,
        "company_name": j.company.CompanyName if j.company else "",
        "job_title": j.JobTitle,
        "required_skills": parse_skills_list(j.RequiredSkills),
        "optional_skills": parse_skills_list(j.OptionalSkills),
        "education": j.Education,
        "experience": j.Experience,
        "job_description": j.JobDescription
    }

@app.post("/api/jobs")
def create_job(data: JobRequirementCreate, db: Session = Depends(get_db)):
    job = JobRequirement(
        CompanyID=data.company_id,
        JobTitle=data.job_title,
        RequiredSkills=json.dumps(data.required_skills),
        OptionalSkills=json.dumps(data.optional_skills),
        Education=data.education,
        Experience=data.experience,
        JobDescription=data.job_description
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return {"id": job.RequirementID, "job_title": job.JobTitle, "status": "created"}

# 3. Master Skills
@app.get("/api/skills")
def get_master_skills(db: Session = Depends(get_db)):
    skills = db.query(Skill).all()
    return [{"id": s.SkillID, "name": s.SkillName, "type": s.SkillType} for s in skills]

# 4. Resume Upload & Extraction
ALLOWED_EXTENSIONS = {
    ".pdf", ".docx", ".doc", ".txt", ".rtf", ".odt",
    ".csv", ".pptx", ".ppt", ".xlsx", ".xls", ".html",
    ".jpg", ".jpeg", ".png", ".webp"
}

@app.post("/api/upload-resume")
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str = Form(""),
    candidate_email: str = Form(""),
    candidate_phone: str = Form(""),
    db: Session = Depends(get_db)
):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{ext}'. Supported formats: PDF, DOCX, TXT, RTF, ODT, CSV, PPTX, XLSX, HTML, PNG, JPG"
        )

    # Save file to uploads folder
    safe_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', file.filename)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    target_filename = f"{timestamp}_{safe_name}"
    target_path = os.path.join(UPLOAD_DIR, target_filename)

    file_bytes = await file.read()
    file_size = len(file_bytes)

    # File size limit (15 MB)
    if file_size > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds maximum allowed size of 15MB.")

    with open(target_path, "wb") as f:
        f.write(file_bytes)

    # Parse document text
    raw_text = extract_text_from_file(target_path, safe_name)
    if not raw_text.strip():
        raw_text = f"Candidate Resume Document: {safe_name}\nContact: {candidate_name} {candidate_email}"

    # Extract NLP information
    extracted = extract_resume_information(raw_text, safe_name)

    # Determine final candidate name & email
    final_name = candidate_name.strip() or extracted["personal_details"]["name"] or "Candidate"
    final_email = candidate_email.strip() or extracted["personal_details"]["email"] or f"candidate_{timestamp}@example.com"
    final_phone = candidate_phone.strip() or extracted["personal_details"]["phone"] or "+1 (555) 000-0000"

    # Find or create Candidate
    candidate = db.query(Candidate).filter(Candidate.Email == final_email).first()
    if not candidate:
        candidate = Candidate(
            Name=final_name,
            Email=final_email,
            Phone=final_phone
        )
        db.add(candidate)
        db.flush()
    else:
        # Update name if previously generic
        if candidate.Name == "Candidate" and final_name != "Candidate":
            candidate.Name = final_name

    # Create ResumeUpload record
    upload_rec = ResumeUpload(
        CandidateID=candidate.CandidateID,
        FileType=ext.lstrip("."),
        FilePath=f"uploads/{target_filename}",
        OriginalFilename=file.filename,
        FileSize=file_size
    )
    db.add(upload_rec)
    db.flush()

    # Create PersonalDetail record
    p_info = extracted["personal_details"]
    pers_detail = PersonalDetail(
        CandidateID=candidate.CandidateID,
        UploadID=upload_rec.UploadID,
        Name=final_name,
        Email=final_email,
        Phone=final_phone,
        Degree=p_info.get("degree", "Bachelor of Science"),
        Location=p_info.get("location", "United States"),
        LinkedIn=p_info.get("linkedin", ""),
        GitHub=p_info.get("github", "")
    )
    db.add(pers_detail)

    # Create Educations
    for edu in extracted.get("education", []):
        db.add(Education(
            CandidateID=candidate.CandidateID,
            UploadID=upload_rec.UploadID,
            Degree=edu.get("degree", "Bachelor of Science"),
            School=edu.get("school", "University"),
            GraduationYear=str(edu.get("graduation_year", "2021")),
            FieldOfStudy=edu.get("field_of_study", "Computer Science")
        ))

    # Create Experiences
    for exp in extracted.get("experience", []):
        db.add(Experience(
            CandidateID=candidate.CandidateID,
            UploadID=upload_rec.UploadID,
            JobTitle=exp.get("job_title", "Software Engineer"),
            Company=exp.get("company", "Tech Company"),
            Duration=exp.get("duration", "2021 - Present"),
            ExperienceYears=float(exp.get("experience_years", 2.0)),
            WorkExperience=exp.get("work_experience", "")
        ))

    # Create Certifications
    for cert in extracted.get("certifications", []):
        db.add(Certification(
            CandidateID=candidate.CandidateID,
            UploadID=upload_rec.UploadID,
            Skill=cert.get("skill", ""),
            CertName=cert.get("cert_name", "Professional Certification"),
            Issuer=cert.get("issuer", ""),
            Year=cert.get("year", "2023")
        ))

    # Create ExtractedResumeData
    extracted_rec = ExtractedResumeData(
        UploadID=upload_rec.UploadID,
        RawText=raw_text,
        ParsedJSON=json.dumps(extracted)
    )
    db.add(extracted_rec)
    db.flush()

    # Create ResumeSkills
    all_extracted_skills = extracted.get("all_skills", [])
    for sk_name in all_extracted_skills:
        db.add(ResumeSkill(
            UploadID=upload_rec.UploadID,
            ExtractionID=extracted_rec.ExtractionID,
            SkillName=sk_name,
            Proficiency="Advanced" if any(sk_name == s.get("skill_name") and s.get("proficiency") == "Advanced" for s in extracted.get("technical_skills", [])) else "Intermediate",
            YearsExperience=float(extracted.get("total_experience_years", 2.0))
        ))

    db.commit()

    return {
        "status": "success",
        "candidate_id": candidate.CandidateID,
        "upload_id": upload_rec.UploadID,
        "candidate_name": final_name,
        "candidate_email": final_email,
        "filename": file.filename,
        "extracted_data": extracted,
        "raw_text_preview": raw_text[:500] + ("..." if len(raw_text) > 500 else "")
    }

# 5. Extraction View Endpoint
@app.get("/api/extract/{upload_id}")
def get_extracted_data(upload_id: int, db: Session = Depends(get_db)):
    upload = db.query(ResumeUpload).filter(ResumeUpload.UploadID == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found")

    ext_data = upload.extracted_data
    parsed = json.loads(ext_data.ParsedJSON) if ext_data and ext_data.ParsedJSON else {}

    return {
        "candidate_id": upload.CandidateID,
        "upload_id": upload.UploadID,
        "filename": upload.OriginalFilename,
        "file_type": upload.FileType,
        "upload_date": upload.Date.isoformat() if upload.Date else None,
        "raw_text": ext_data.RawText if ext_data else "",
        "extracted_data": parsed
    }

# 6. Matching & Skill Gap Analysis
@app.post("/api/match/{upload_id}/{job_id}")
def run_resume_matching(upload_id: int, job_id: int, db: Session = Depends(get_db)):
    upload = db.query(ResumeUpload).filter(ResumeUpload.UploadID == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload record not found")

    job = db.query(JobRequirement).filter(JobRequirement.RequirementID == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job requirement not found")

    # Get extracted data
    ext_data = upload.extracted_data
    parsed = json.loads(ext_data.ParsedJSON) if ext_data and ext_data.ParsedJSON else {}

    # Run matching calculation
    job_dict = {
        "job_title": job.JobTitle,
        "required_skills": job.RequiredSkills,
        "optional_skills": job.OptionalSkills,
        "experience": job.Experience,
        "education": job.Education
    }
    analysis_result = calculate_match_analysis(parsed, job_dict)

    # Check for existing matching session or create new
    session_rec = db.query(ResumeMatchingSession).filter(
        ResumeMatchingSession.UploadID == upload_id,
        ResumeMatchingSession.RequirementID == job_id
    ).first()

    if not session_rec:
        session_rec = ResumeMatchingSession(
            UploadID=upload_id,
            RequirementID=job_id
        )
        db.add(session_rec)
        db.flush()

    # Update or create MatchingAnalysis
    analysis_rec = db.query(MatchingAnalysis).filter(MatchingAnalysis.MatchingID == session_rec.MatchingID).first()
    if not analysis_rec:
        analysis_rec = MatchingAnalysis(
            MatchingID=session_rec.MatchingID,
            MatchPercentage=analysis_result["match_percentage"],
            SkillGapDetails=json.dumps(analysis_result["skill_gap_details"]),
            Explanation=analysis_result["explanation"],
            Strengths=json.dumps(analysis_result["strengths"]),
            ImprovementAreas=json.dumps(analysis_result["improvement_areas"])
        )
        db.add(analysis_rec)
    else:
        analysis_rec.MatchPercentage = analysis_result["match_percentage"]
        analysis_rec.SkillGapDetails = json.dumps(analysis_result["skill_gap_details"])
        analysis_rec.Explanation = analysis_result["explanation"]
        analysis_rec.Strengths = json.dumps(analysis_result["strengths"])
        analysis_rec.ImprovementAreas = json.dumps(analysis_result["improvement_areas"])

    # Clear old and store SkillMatchResults
    db.query(SkillMatchResult).filter(SkillMatchResult.MatchingID == session_rec.MatchingID).delete()
    for item in analysis_result["skill_results"]:
        db.add(SkillMatchResult(
            MatchingID=session_rec.MatchingID,
            SkillName=item["skill_name"],
            MatchStatus=item["status"],
            MatchScore=item["score"]
        ))

    db.commit()

    return {
        "matching_id": session_rec.MatchingID,
        "upload_id": upload_id,
        "candidate_id": upload.CandidateID,
        "job_id": job.RequirementID,
        "job_title": job.JobTitle,
        "company_name": job.company.CompanyName if job.company else "",
        "match_percentage": analysis_result["match_percentage"],
        "matching_skills": analysis_result["matching_skills"],
        "missing_skills": analysis_result["missing_skills"],
        "optional_matched": analysis_result["optional_matched"],
        "strengths": analysis_result["strengths"],
        "explanation": analysis_result["explanation"],
        "improvement_areas": analysis_result["improvement_areas"],
        "skill_gap_details": analysis_result["skill_gap_details"]
    }

# 7. Mock Questions Generation (CRITICAL: BASED ON CANDIDATE'S EXTRACTED SKILLS)
@app.get("/api/assessment/questions/{candidate_id}")
def get_mock_questions(
    candidate_id: int,
    matching_id: Optional[int] = None,
    force_regenerate: bool = False,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.CandidateID == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # If questions already exist and not forced, return existing
    existing = db.query(MockQuestion).filter(MockQuestion.CandidateID == candidate_id).all()
    if existing and not force_regenerate:
        return [
            {
                "question_id": q.QuestionID,
                "candidate_id": q.CandidateID,
                "skill_name": q.SkillName,
                "question": q.Question,
                "question_type": q.QuestionType,
                "difficulty": q.Difficulty,
                "sample_answer_hint": q.SampleAnswerHint
            }
            for q in existing
        ]

    # Retrieve candidate's extracted skills
    extracted_skills = []
    latest_upload = db.query(ResumeUpload).filter(ResumeUpload.CandidateID == candidate_id).order_by(ResumeUpload.UploadID.desc()).first()
    if latest_upload and latest_upload.extracted_data:
        parsed = json.loads(latest_upload.extracted_data.ParsedJSON)
        extracted_skills = parsed.get("all_skills", [])

    if not extracted_skills:
        # Fallback to resume_skills table
        r_skills = db.query(ResumeSkill).filter(ResumeSkill.UploadID == (latest_upload.UploadID if latest_upload else 0)).all()
        extracted_skills = [s.SkillName for s in r_skills]

    # Generate 4-6 questions based on candidate's extracted skills
    generated = generate_mock_questions_for_candidate(
        extracted_skills=extracted_skills,
        candidate_id=candidate_id,
        matching_id=matching_id,
        desired_count=5
    )

    # Delete existing if regenerating
    if existing and force_regenerate:
        db.query(MockQuestion).filter(MockQuestion.CandidateID == candidate_id).delete()

    created_questions = []
    for g in generated:
        q_obj = MockQuestion(
            CandidateID=candidate_id,
            MatchingID=matching_id,
            SkillName=g["skill_name"],
            Question=g["question"],
            QuestionType=g["question_type"],
            Difficulty=g["difficulty"],
            SampleAnswerHint=g["sample_answer_hint"]
        )
        db.add(q_obj)
        db.flush()
        created_questions.append({
            "question_id": q_obj.QuestionID,
            "candidate_id": q_obj.CandidateID,
            "skill_name": q_obj.SkillName,
            "question": q_obj.Question,
            "question_type": q_obj.QuestionType,
            "difficulty": q_obj.Difficulty,
            "sample_answer_hint": q_obj.SampleAnswerHint
        })

    db.commit()
    return created_questions

# 8. Submit Candidate Answers & Evaluation
@app.post("/api/assessment/submit")
def submit_candidate_answers(payload: AssessmentSubmitPayload, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.CandidateID == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    evaluated_answers = []

    for item in payload.answers:
        q_obj = db.query(MockQuestion).filter(MockQuestion.QuestionID == item.question_id).first()
        if not q_obj:
            continue

        # Evaluate answer using AI + rule-based rubric
        eval_result = evaluate_single_answer(
            question_text=q_obj.Question,
            skill_name=q_obj.SkillName,
            answer_text=item.answer,
            hint=q_obj.SampleAnswerHint or ""
        )

        # Store or update CandidateAnswer
        ans_rec = db.query(CandidateAnswer).filter(
            CandidateAnswer.QuestionID == item.question_id,
            CandidateAnswer.CandidateID == payload.candidate_id
        ).first()

        if not ans_rec:
            ans_rec = CandidateAnswer(
                QuestionID=item.question_id,
                CandidateID=payload.candidate_id,
                Answer=item.answer,
                Score=eval_result["score"],
                Feedback=eval_result["feedback"],
                CorrectnessRelevance=eval_result["correctness_relevance"],
                ImprovementSuggestions=eval_result["improvement_suggestions"]
            )
            db.add(ans_rec)
        else:
            ans_rec.Answer = item.answer
            ans_rec.Score = eval_result["score"]
            ans_rec.Feedback = eval_result["feedback"]
            ans_rec.CorrectnessRelevance = eval_result["correctness_relevance"]
            ans_rec.ImprovementSuggestions = eval_result["improvement_suggestions"]

        evaluated_answers.append({
            "question_id": q_obj.QuestionID,
            "skill_name": q_obj.SkillName,
            "question": q_obj.Question,
            "answer": item.answer,
            "score": eval_result["score"],
            "feedback": eval_result["feedback"],
            "correctness_relevance": eval_result["correctness_relevance"],
            "improvement_suggestions": eval_result["improvement_suggestions"]
        })

    # Compile overall performance scorecard
    perf_summary = compile_overall_performance(
        question_evaluations=evaluated_answers,
        candidate_id=payload.candidate_id,
        matching_id=payload.matching_id
    )

    # Store or update Performance record
    perf_rec = db.query(Performance).filter(Performance.CandidateID == payload.candidate_id).first()
    if not perf_rec:
        perf_rec = Performance(
            CandidateID=payload.candidate_id,
            MatchingID=payload.matching_id,
            TotalScore=perf_summary["total_score"],
            MaximumScore=perf_summary["maximum_score"],
            PercentageScore=perf_summary["percentage_score"],
            OverallPerformance=perf_summary["overall_performance"],
            StrongAreas=json.dumps(perf_summary["strong_areas"]),
            ImprovementAreas=json.dumps(perf_summary["improvement_areas"]),
            PerformanceAnalysis=perf_summary["performance_analysis"]
        )
        db.add(perf_rec)
    else:
        perf_rec.MatchingID = payload.matching_id
        perf_rec.TotalScore = perf_summary["total_score"]
        perf_rec.MaximumScore = perf_summary["maximum_score"]
        perf_rec.PercentageScore = perf_summary["percentage_score"]
        perf_rec.OverallPerformance = perf_summary["overall_performance"]
        perf_rec.StrongAreas = json.dumps(perf_summary["strong_areas"])
        perf_rec.ImprovementAreas = json.dumps(perf_summary["improvement_areas"])
        perf_rec.PerformanceAnalysis = perf_summary["performance_analysis"]

    db.commit()

    return {
        "status": "evaluated",
        "candidate_id": payload.candidate_id,
        "evaluated_answers": evaluated_answers,
        "performance": perf_summary
    }

# 9. Full Candidate 360° Profile
@app.get("/api/candidate-profile/{candidate_id}")
def get_candidate_profile(candidate_id: int, db: Session = Depends(get_db)):
    cand = db.query(Candidate).filter(Candidate.CandidateID == candidate_id).first()
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")

    upload = db.query(ResumeUpload).filter(ResumeUpload.CandidateID == candidate_id).order_by(ResumeUpload.UploadID.desc()).first()

    # Personal details
    pers = cand.personal_details[0] if cand.personal_details else None
    educations = [
        {
            "degree": e.Degree,
            "school": e.School,
            "graduation_year": e.GraduationYear,
            "field_of_study": e.FieldOfStudy
        }
        for e in cand.educations
    ]
    experiences = [
        {
            "job_title": exp.JobTitle,
            "company": exp.Company,
            "duration": exp.Duration,
            "experience_years": exp.ExperienceYears,
            "work_experience": exp.WorkExperience
        }
        for exp in cand.experiences
    ]
    certifications = [
        {
            "cert_name": c.CertName,
            "skill": c.Skill,
            "issuer": c.Issuer,
            "year": c.Year
        }
        for c in cand.certifications
    ]

    # Extracted skills
    parsed_json = {}
    if upload and upload.extracted_data and upload.extracted_data.ParsedJSON:
        try:
            parsed_json = json.loads(upload.extracted_data.ParsedJSON)
        except Exception:
            pass

    technical_skills = parsed_json.get("technical_skills", [])
    soft_skills = parsed_json.get("soft_skills", [])
    all_skills = parsed_json.get("all_skills", [s.SkillName for s in upload.resume_skills] if upload else [])

    # Matching Analysis
    matching_info = None
    latest_session = None
    if upload and upload.matching_sessions:
        latest_session = upload.matching_sessions[-1]
    elif db.query(ResumeMatchingSession).first():
        # Match with candidate's questions matching_id if any
        first_q = db.query(MockQuestion).filter(MockQuestion.CandidateID == candidate_id, MockQuestion.MatchingID != None).first()
        if first_q:
            latest_session = db.query(ResumeMatchingSession).filter(ResumeMatchingSession.MatchingID == first_q.MatchingID).first()

    if latest_session and latest_session.analysis:
        analysis = latest_session.analysis
        gap_details = json.loads(analysis.SkillGapDetails) if analysis.SkillGapDetails else {}
        strengths = json.loads(analysis.Strengths) if analysis.Strengths else []
        improvements = json.loads(analysis.ImprovementAreas) if analysis.ImprovementAreas else []

        matching_info = {
            "matching_id": latest_session.MatchingID,
            "job_id": latest_session.RequirementID,
            "job_title": latest_session.job_requirement.JobTitle if latest_session.job_requirement else "Target Position",
            "company_name": latest_session.job_requirement.company.CompanyName if latest_session.job_requirement and latest_session.job_requirement.company else "Company",
            "match_percentage": analysis.MatchPercentage,
            "matching_skills": gap_details.get("matching_skills", []),
            "missing_skills": gap_details.get("missing_skills", []),
            "optional_matched": gap_details.get("optional_matched", []),
            "explanation": analysis.Explanation,
            "strengths": strengths,
            "improvement_areas": improvements,
            "skill_gap_details": gap_details
        }

    # Questions and Answers
    qa_list = []
    questions = db.query(MockQuestion).filter(MockQuestion.CandidateID == candidate_id).all()
    for q in questions:
        ans = db.query(CandidateAnswer).filter(
            CandidateAnswer.QuestionID == q.QuestionID,
            CandidateAnswer.CandidateID == candidate_id
        ).first()

        qa_list.append({
            "question_id": q.QuestionID,
            "skill_name": q.SkillName,
            "question": q.Question,
            "question_type": q.QuestionType,
            "difficulty": q.Difficulty,
            "answer": ans.Answer if ans else "Not answered yet",
            "score": ans.Score if ans else 0.0,
            "feedback": ans.Feedback if ans else "Awaiting submission",
            "correctness_relevance": ans.CorrectnessRelevance if ans else "",
            "improvement_suggestions": ans.ImprovementSuggestions if ans else ""
        })

    # Performance
    perf = cand.performances[-1] if cand.performances else None
    performance_data = None
    if perf:
        performance_data = {
            "total_score": perf.TotalScore,
            "maximum_score": perf.MaximumScore,
            "percentage_score": perf.PercentageScore,
            "overall_performance": perf.OverallPerformance,
            "strong_areas": json.loads(perf.StrongAreas) if perf.StrongAreas else [],
            "improvement_areas": json.loads(perf.ImprovementAreas) if perf.ImprovementAreas else [],
            "performance_analysis": perf.PerformanceAnalysis
        }

    return {
        "candidate_id": cand.CandidateID,
        "name": cand.Name,
        "email": cand.Email,
        "phone": cand.Phone,
        "location": pers.Location if pers else "United States",
        "linkedin": pers.LinkedIn if pers else "",
        "github": pers.GitHub if pers else "",
        "degree": pers.Degree if pers else (educations[0]["degree"] if educations else "Bachelor of Science"),
        "resume_filename": upload.OriginalFilename if upload else "resume.pdf",
        "resume_file_url": f"/{upload.FilePath}" if upload and upload.FilePath else "",
        "education": educations,
        "experience": experiences,
        "certifications": certifications,
        "technical_skills": technical_skills,
        "soft_skills": soft_skills,
        "all_skills": all_skills,
        "matching": matching_info,
        "assessment_qa": qa_list,
        "performance": performance_data
    }

# 10. Recruiter Dashboard Endpoints
@app.get("/api/dashboard/candidates")
def get_dashboard_candidates(
    search: Optional[str] = Query(None),
    job_id: Optional[int] = Query(None),
    min_match: Optional[float] = Query(None),
    sort_by: Optional[str] = Query("match_percentage"),  # match_percentage, assessment_score, name, date
    db: Session = Depends(get_db)
):
    candidates = db.query(Candidate).all()
    results = []

    for c in candidates:
        upload = db.query(ResumeUpload).filter(ResumeUpload.CandidateID == c.CandidateID).order_by(ResumeUpload.UploadID.desc()).first()

        # Latest matching
        match_session = None
        if upload and upload.matching_sessions:
            match_session = upload.matching_sessions[-1]

        job_title = "Unassigned"
        company_name = "-"
        match_pct = 0.0
        matching_skills = []
        missing_skills = []

        if match_session and match_session.analysis:
            job_title = match_session.job_requirement.JobTitle if match_session.job_requirement else "General"
            company_name = match_session.job_requirement.company.CompanyName if match_session.job_requirement and match_session.job_requirement.company else "-"
            match_pct = match_session.analysis.MatchPercentage
            gap_json = json.loads(match_session.analysis.SkillGapDetails) if match_session.analysis.SkillGapDetails else {}
            matching_skills = [m.get("skill") if isinstance(m, dict) else m for m in gap_json.get("matching_skills", [])]
            missing_skills = [m.get("skill") if isinstance(m, dict) else m for m in gap_json.get("missing_skills", [])]

        perf = c.performances[-1] if c.performances else None
        assessment_score = perf.TotalScore if perf else 0.0
        max_score = perf.MaximumScore if perf else 50.0
        performance_tier = perf.OverallPerformance if perf else "Pending"

        item = {
            "candidate_id": c.CandidateID,
            "upload_id": upload.UploadID if upload else None,
            "name": c.Name,
            "email": c.Email,
            "phone": c.Phone,
            "job_applied_for": job_title,
            "company_name": company_name,
            "match_percentage": match_pct,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "assessment_score": assessment_score,
            "maximum_score": max_score,
            "score_percentage": round((assessment_score / max(1.0, max_score)) * 100.0, 1) if perf else 0.0,
            "performance": performance_tier,
            "created_at": c.CreatedAt.isoformat() if c.CreatedAt else None
        }

        # Filtering logic
        if search:
            search_l = search.lower()
            in_name = search_l in c.Name.lower()
            in_email = search_l in c.Email.lower()
            in_job = search_l in job_title.lower()
            in_skills = any(search_l in s.lower() for s in matching_skills + missing_skills)
            if not (in_name or in_email or in_job or in_skills):
                continue

        if job_id and match_session and match_session.RequirementID != job_id:
            continue

        if min_match is not None and match_pct < min_match:
            continue

        results.append(item)

    # Sorting
    if sort_by == "match_percentage":
        results.sort(key=lambda x: x["match_percentage"], reverse=True)
    elif sort_by == "assessment_score":
        results.sort(key=lambda x: x["assessment_score"], reverse=True)
    elif sort_by == "name":
        results.sort(key=lambda x: x["name"])
    elif sort_by == "date":
        results.sort(key=lambda x: x["created_at"] or "", reverse=True)

    return results

@app.get("/api/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_candidates = db.query(Candidate).count()
    total_jobs = db.query(JobRequirement).count()
    analyses = db.query(MatchingAnalysis).all()
    avg_match = round(sum(a.MatchPercentage for a in analyses) / max(1, len(analyses)), 1) if analyses else 0.0

    performances = db.query(Performance).all()
    avg_score = round(sum(p.PercentageScore for p in performances) / max(1, len(performances)), 1) if performances else 0.0
    shortlisted = sum(1 for p in performances if p.OverallPerformance in ["Exceptional", "Strong Hire"])

    return {
        "total_candidates": total_candidates,
        "total_jobs": total_jobs,
        "average_match_percentage": avg_match,
        "average_assessment_score": avg_score,
        "shortlisted_candidates": shortlisted
    }

# 11. Sample Resumes Preset Endpoint for 1-Click Testing
@app.get("/api/sample-resumes")
def list_sample_resumes():
    samples = []
    if os.path.exists(SAMPLE_DIR):
        for f in os.listdir(SAMPLE_DIR):
            if f.endswith((".txt", ".pdf", ".docx")):
                samples.append({
                    "filename": f,
                    "title": f.replace("_", " ").replace(".txt", "").replace(".pdf", "").replace(".docx", ""),
                    "path": f"sample_resumes/{f}"
                })
    return samples

@app.post("/api/sample-resumes/load/{filename}")
def load_sample_resume(filename: str, db: Session = Depends(get_db)):
    file_path = os.path.join(SAMPLE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Sample resume not found")

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        raw_text = f.read()

    extracted = extract_resume_information(raw_text, filename)
    name = extracted["personal_details"]["name"]
    email = extracted["personal_details"]["email"]
    phone = extracted["personal_details"]["phone"]

    cand = db.query(Candidate).filter(Candidate.Email == email).first()
    if not cand:
        cand = Candidate(Name=name, Email=email, Phone=phone)
        db.add(cand)
        db.flush()

    upload = ResumeUpload(
        CandidateID=cand.CandidateID,
        FileType="txt",
        FilePath=f"sample_resumes/{filename}",
        OriginalFilename=filename,
        FileSize=os.path.getsize(file_path)
    )
    db.add(upload)
    db.flush()

    ext_rec = ExtractedResumeData(
        UploadID=upload.UploadID,
        RawText=raw_text,
        ParsedJSON=json.dumps(extracted)
    )
    db.add(ext_rec)
    db.flush()

    for sk_name in extracted.get("all_skills", []):
        db.add(ResumeSkill(
            UploadID=upload.UploadID,
            ExtractionID=ext_rec.ExtractionID,
            SkillName=sk_name,
            Proficiency="Advanced",
            YearsExperience=float(extracted.get("total_experience_years", 3.0))
        ))

    db.commit()

    return {
        "status": "loaded",
        "candidate_id": cand.CandidateID,
        "upload_id": upload.UploadID,
        "candidate_name": name,
        "extracted_data": extracted
    }

# 12. Mount Static Files
if os.path.exists(UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
if os.path.exists(SAMPLE_DIR):
    app.mount("/sample_resumes", StaticFiles(directory=SAMPLE_DIR), name="sample_resumes")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
