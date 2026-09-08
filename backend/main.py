import io
from fastapi import FastAPI, UploadFile, File

from database import Base, engine
from models import Resume, JobDescription
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
def get_match_data(resume_id: int, job_id: int):
    db = SessionLocal()

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()

    db.close()

    if not resume:
        return {"error": "Resume not found"}

    if not job:
        return {"error": "Job description not found"}

    return {
        "resume_id": resume.id,
        "resume_filename": resume.filename,
        "resume_text": resume.extracted_text,
        "job_id": job.id,
        "job_title": job.title,
        "job_description": job.description
    }