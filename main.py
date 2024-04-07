import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
from ResumeProcessor.JobRecomendation import main as job_recommendation_main


import requests
import pandas as pd
from pdfminer.high_level import extract_text

from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main

numberOfJobsForRecomendation = 5
numberOfJobsForReportGeneration = 5

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s:%(name)s:%(funcName)s: %(message)s')
logger = logging.getLogger(__name__)

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

        pdf_file = await download_pdf(resume_url)
        resume_as_string = extract_text(pdf_file)

        print(f"Number of characters in the resume: {len(resume_as_string)}")

        # Print the first 50 characters of the resume
        first_50_chars = resume_as_string[:50]
        print(f"First 50 characters of the resume: {first_50_chars}")

        csvOfJobs = job_recommendation_main(resume_as_string, numberOfJobsForRecomendation)

        recomendedJobs = csvOfJobs["job_posting_id"].head(numberOfJobsForReportGeneration).tolist()

        listOfReportUrls = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobs)

        #Persist Job Recomendation to DB

        #Email Job Recomendation




        

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

@app.get("/")
async def root():
    logging.info("Root endpoint called")
    return {"message": "Hello World"}