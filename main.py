import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
from ResumeProcessor.JobRecomendation import main as job_recommendation_main

import os
from dotenv import load_dotenv
import requests
import pandas as pd
from pdfminer.high_level import extract_text

from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main
from ResumeProcessor.RecommendedJobsEmailer import main as recomended_jobs_reporter_main

numberOfJobsForRecomendation = 50
numberOfJobsForReportGeneration = 5

load_dotenv('.env')
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')


app = FastAPI()

# Define the request model
class RecommendationRequest(BaseModel):
    email_address: str
    resume_url: str


async def download_pdf(resume_url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(resume_url)
        response.raise_for_status()
        return BytesIO(response.content)

async def jobRecommendation(email_address: str, resume_url: str):

    try:

        logging.debug(f"Begin Job Recomendation for email: {email_address}.")
        logging.debug(f"Resume url is located at: {resume_url}.")

        pdf_file = await download_pdf(resume_url)
        resume_as_string = extract_text(pdf_file)

        recommendedJobsDf = job_recommendation_main(resume_as_string, numberOfJobsForRecomendation)
        logging.debug(f"Completed the job recomendation step: {resume_url}.")


        recomendedJobs = recommendedJobsDf["job_posting_id"].head(numberOfJobsForReportGeneration).tolist()

        recomendedJobsAsJobIdList = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobs)

        #Persist Job Recomendation to DB

        #Email Job Recomendation
        messageID = recomended_jobs_reporter_main(email_address, recommendedJobsDf, recomendedJobsAsJobIdList)
        logging.debug(f"Finished email send: {messageID}.")


    except requests.RequestException as e:
        print(f"Error downloading the PDF: {e}")
    except Exception as e:
        print(f"Error processing the PDF: {e}")

@app.post("/recommendation")
async def recommendation_endpoint(request: RecommendationRequest, background_tasks: BackgroundTasks):
    """
    Endpoint to receive email address and resume URL, and start a background job for processing.
    """
    # Kick off the background task without waiting for it to complete
    background_tasks.add_task(jobRecommendation, request.email_address, request.resume_url)
    
    # Return a response immediately to the client
    return {"message": "Recommendation process started successfully"}