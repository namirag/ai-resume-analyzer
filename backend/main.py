import io
import json
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine, SessionLocal
from models import Resume, JobDescription, Analysis
from ai_service import analyze_resume
from pydantic import BaseModel
from pypdf import PdfReader
from docx import Document


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Resume Analyzer",
    description="A FastAPI application for analyzing resumes using AI.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        return {
            "error": "Only PDF and DOCX files are supported"
        }

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
        return {
            "error": "Resume not found"
        }

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

    # Analyze resume using AI
    analysis = analyze_resume(
        resume.extracted_text,
        job.description
    )

    # Save analysis to PostgreSQL
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