from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from pydantic import BaseModel
import shutil

app = FastAPI()

class JobRecommendationRequest(BaseModel):
    email_address: str

async def process_resume(resume: UploadFile, email_address: str):
    # Placeholder for your complex processing logic
    # Save the file to a temporary location first
    with open(resume.filename, "wb") as buffer:
        shutil.copyfileobj(resume.file, buffer)
    print(f"Processing resume {resume.filename} for {email_address}")
    # Add your processing code here

@app.post("/jobrecommendation/")
async def job_recommendation(request: JobRecommendationRequest, background_tasks: BackgroundTasks, resume: UploadFile = File(...)):
    background_tasks.add_task(process_resume, resume, request.email_address)
    return {"message": "Received", "email": request.email_address}
