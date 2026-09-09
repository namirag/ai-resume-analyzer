import os
from openai import OpenAI
from pydantic import BaseModel


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ResumeAnalysis(BaseModel):
    match_score: int
    matching_skills: list[str]
    missing_skills: list[str]
    strengths: list[str]
    recommendations: list[str]
    interview_questions: list[str]


def analyze_resume(resume_text, job_description):

    response = client.responses.parse(
        model="gpt-5-mini",
        input=f"""
Analyze this resume against the job description.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Evaluate the candidate based only on the information provided.
Give a match score from 0 to 100.

Identify:
- Skills that match the job
- Skills missing from the resume
- Resume strengths relevant to the job
- Specific recommendations to improve the resume
- Interview questions relevant to the candidate and job
""",
        text_format=ResumeAnalysis,
    )

    return response.output_parsed