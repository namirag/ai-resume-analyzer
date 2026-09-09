import io
from fastapi import FastAPI, UploadFile, File, HTTPException

from database import Base, engine
from models import Resume, JobDescriptionCreate, Analysis
from ai_service import analyze_resume
import json
from pydantic import BaseModel
from pypdf import PdfReader
from docx import Document
from database import SessionLocal


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Analyzer",
    description="A FastAPI application for analyzing resumes using AI.",
    version="1.0.0"
)

class JobDescriptionCreate(BaseModel):
    title: str
    description: str

@app.get("/")
def root():
    return {"message": "AI resume analyzer is running"}

@app.post("/resume/upload")
async def upload_resume(file: UploadFile = File(...)):
    file_data = await file.read()

    if file.filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_data))

        text = ""
        for page in reader.pages:
            text += (page.extract_text() or "").replace("\x00", "")

    elif file.filename.lower().endswith(".docx"):
        document = Document(io.BytesIO(file_data))

        text = ""
        for paragraph in document.paragraphs:
            text += paragraph.text + "\n"

    else:
        raise HTTPException(
        status_code=400,
        detail="Only PDF and DOCX files are supported"
    )

    db = SessionLocal()

    resume = Resume(
        filename=file.filename,
        extracted_text=text
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)
    db.close()

    return {
        "id": resume.id,
        "filename": resume.filename,
        "content_type": file.content_type,
        "message": "Resume uploaded and saved successfully",
        "text": text
    }
    
@app.get("/resume/{resume_id}")
def get_resume(resume_id: int):
    db = SessionLocal()

    resume = db.query(Resume).filter(Resume.id == resume_id).first()

    db.close()

    if not resume:
        raise HTTPException(
        status_code=404,
        detail="Resume not found"
    )

    return {
        "id": resume.id,
        "filename": resume.filename,
        "extracted_text": resume.extracted_text,
        "created_at": resume.created_at
    }

@app.post("/job")
def create_job(job: JobDescriptionCreate):
    db = SessionLocal()

    new_job = JobDescription(
        title=job.title,
        description=job.description
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    db.close()

    return {
        "id": new_job.id,
        "title": new_job.title,
        "message": "Job description saved successfully"
    }

@app.get("/match/{resume_id}/{job_id}")
def analyze_resume_match(resume_id: int, job_id: int):
    db = SessionLocal()

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

    if not resume:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Resume not found"
        )

    if not job:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Job description not found"
        )

    existing_analysis = (
        db.query(Analysis)
        .filter(
            Analysis.resume_id == resume_id,
            Analysis.job_id == job_id
        )
        .order_by(Analysis.created_at.desc())
        .first()
    )

    if existing_analysis:
        result = {
        "analysis_id": existing_analysis.id,
        "resume_id": resume.id,
        "job_id": job.id,
        "job_title": job.title,
        "analysis": {
            "match_score": existing_analysis.match_score,
            "matching_skills": json.loads(existing_analysis.matching_skills),
            "missing_skills": json.loads(existing_analysis.missing_skills),
            "strengths": json.loads(existing_analysis.strengths),
            "recommendations": json.loads(existing_analysis.recommendations),
            "interview_questions": json.loads(existing_analysis.interview_questions)
        },
        "message": "Existing analysis retrieved from database"
    }

    db.close()

    return result
    
    analysis = analyze_resume(
        resume.extracted_text,
        job.description
    )

    analysis_record = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        match_score=analysis.match_score,
        matching_skills=json.dumps(analysis.matching_skills),
        missing_skills=json.dumps(analysis.missing_skills),
        strengths=json.dumps(analysis.strengths),
        recommendations=json.dumps(analysis.recommendations),
        interview_questions=json.dumps(analysis.interview_questions)
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)

    result = {
        "analysis_id": analysis_record.id,
        "resume_id": resume.id,
        "job_id": job.id,
        "job_title": job.title,
        "analysis": analysis.model_dump()
    }

    db.close()

    return result

@app.get("/analysis/{analysis_id}")
def get_analysis(analysis_id: int):
    db = SessionLocal()

    analysis = (
        db.query(Analysis)
        .filter(Analysis.id == analysis_id)
        .first()
    )

    if not analysis:
        db.close()
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    result = {
        "analysis_id": analysis.id,
        "resume_id": analysis.resume_id,
        "job_id": analysis.job_id,
        "match_score": analysis.match_score,
        "matching_skills": json.loads(analysis.matching_skills),
        "missing_skills": json.loads(analysis.missing_skills),
        "strengths": json.loads(analysis.strengths),
        "recommendations": json.loads(analysis.recommendations),
        "interview_questions": json.loads(analysis.interview_questions),
        "created_at": analysis.created_at
    }

    db.close()

    return result