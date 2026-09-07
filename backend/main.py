from fastapi import FastAPI

app = FastAPI(title="AI resume analyzer", description="A FastAPI application for analyzing resumes using AI.", version="1.0.0")

@app.get("/")
def root():
    return {"message": "AI resume analyzer is running"}