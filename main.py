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
import json
import time
from dotenv import load_dotenv
import requests
import pandas as pd
from pdfminer.high_level import extract_text

from ResumeProcessor.LlmResumeProcessor import LlmResumeProcessor
from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main
from ResumeProcessor.RecommendedJobsEmailer import main as recomended_jobs_reporter_main

numberOfJobsForRecomendation = 1000
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

        # Begin the timer
        start_time = time.time()

        logging.debug(f"Begin Job Recomendation for email: {email_address}.")
        logging.debug(f"Resume url is located at: {resume_url}.")

        pdfFile = await download_pdf(resume_url)
        resumeAsString = extract_text(pdfFile)

        llmResumeProcessor = LlmResumeProcessor()
        resumeAsJson = llmResumeProcessor.parseResume(resumeAsString)
        resumeAsJson = json.loads(resumeAsJson)

        candidateName = resumeAsJson["Name"]

        recommendedJobsDf = job_recommendation_main(resumeAsJson, numberOfJobsForRecomendation, resumeAsString)
        logging.debug(f"Completed the job recomendation step: {resume_url}.")

        topRecomendedJobs = recommendedJobsDf["job_posting_id"].head(numberOfJobsForReportGeneration).tolist()

        recomendedJobsAsJobIdList = custom_report_generator_main(candidateName, resumeAsString, topRecomendedJobs)

        #TODO: Persist Job Recomendation to DB

        #Email Job Recomendation
        recomended_jobs_reporter_main(email_address, recommendedJobsDf, recomendedJobsAsJobIdList, candidateName)
        
        # Stop the timer and calculate total time taken.
        finish_time = time.time()
        total_time_in_seconds = finish_time - start_time
        logging.debug(f"Finished email send. Recomendation Process has completed")
        logging.INFO(f"Recomendation has complete. Time required: {total_time_in_seconds}")


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