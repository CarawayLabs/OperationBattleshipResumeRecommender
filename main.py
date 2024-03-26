from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from typing import Union
import uvicorn
from operation_battleship_common_utilities.OpenAICaller import OpenAICaller

app = FastAPI()

def processResume(resume: UploadFile, email_address: str):
    # Placeholder for the complex processing logic
    # You would replace this with your actual processing code
    print(f"Processing resume for {email_address}")

@app.post("/jobrecommendation")
async def job_recommendation(
    background_tasks: BackgroundTasks,
    email_address: str = Form(...),
    resume: UploadFile = File(...)
):
    background_tasks.add_task(processResume, resume, email_address)
    return {"message": "Received. The processing of the resume has started."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
