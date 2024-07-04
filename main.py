import newrelic.agent
import os

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv('.env')

# Initialize New Relic agent
newrelic.agent.initialize('newrelic.ini')

import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
from ResumeProcessor.JobRecomendation import main as job_recommendation_main

import json
import time
import pandas as pd
from ResumeProcessor.LlmResumeProcessor import LlmResumeProcessor
from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main
from ResumeProcessor.RecommendedJobsEmailer import main as recomended_jobs_reporter_main

numberOfJobsForRecomendation = 1000
numberOfJobsForReportGeneration = 5

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
        recomended_jobs_reporter_main(email_address, recommendedJobsDf, recomendedJobsAsJobIdList, candidateName)
        finish_time = time.time()
        total_time_in_seconds = finish_time - start_time
        logging.debug(f"Finished email send. Recomendation Process has completed")
        logging.info(f"Recomendation has complete. Time required: {total_time_in_seconds}")
    except requests.RequestException as e:
        print(f"Error downloading the PDF: {e}")
    except Exception as e:
        print(f"Error processing the PDF: {e}")

@app.post("/recommendation")
async def recommendation_endpoint(request: RecommendationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(jobRecommendation, request.email_address, request.resume_url)
    return {"message": "Recommendation process started successfully"}
