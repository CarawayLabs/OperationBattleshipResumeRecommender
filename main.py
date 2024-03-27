import logging
from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from pydantic import BaseModel
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

app = FastAPI()

class JobRecommendationRequest(BaseModel):
    email_address: str

async def process_resume(resume: UploadFile, email_address: str):
    try:
        # Save the file to a temporary location first
        with open(resume.filename, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)
        logging.info(f"Processing resume {resume.filename} for {email_address}")
        # Add your processing code here
    except Exception as e:
        logging.error(f"Error processing resume {resume.filename} for {email_address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/jobrecommendation/")
async def job_recommendation(request: JobRecommendationRequest, background_tasks: BackgroundTasks, resume: UploadFile = File(...)):
    try:
        background_tasks.add_task(process_resume, resume, request.email_address)
        return {"message": "Received", "email": request.email_address}
    except Exception as e:
        logging.error(f"Error in job_recommendation for {request.email_address}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    logging.info("Root endpoint called")
    return {"message": "Hello World"}
