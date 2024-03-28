from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import logging
import requests
from io import BytesIO
from pdfminer.high_level import extract_text
from ResumeProcessor.JobRecomendation import main as job_recommendation_main

number_of_jobs = 5

app = FastAPI()

# Define the request model
class RecommendationRequest(BaseModel):
    email_address: str
    resume_url: str

def jobRecommendation(email_address: str, resume_url: str):
    """
    Placeholder function to simulate processing the resume and sending job recommendations.
    Implement your actual processing logic here.
    """

    print(f"Processing resume from {resume_url} for {email_address}")
    # Simulate a time-consuming task
    # You can replace this with actual logic to process the resume and send recommendations
    # time.sleep() should not be used in asynchronous functions, it's just for demonstration here
    import time
    time.sleep(5)
    print(f"Finished processing for {email_address}")


    try:
        # Download the PDF file
        response = requests.get(resume_url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Convert the downloaded content into a BytesIO object for pdfminer to read
        pdf_file = BytesIO(response.content)

        # Extract text from the PDF file
        resume_as_string = extract_text(pdf_file)

        # Print the number of characters in the resume
        print(f"Number of characters in the resume: {len(resume_as_string)}")

        # Print the first 50 characters of the resume
        first_50_chars = resume_as_string[:50]
        print(f"First 50 characters of the resume: {first_50_chars}")

        csvOfJobs = job_recommendation_main(resume_as_string, number_of_jobs)

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