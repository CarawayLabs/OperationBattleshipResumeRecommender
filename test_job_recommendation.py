import requests
import pandas as pd
from pdfminer.high_level import extract_text
from io import BytesIO
from ResumeProcessor.JobRecomendation import main as job_recommendation_main
from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main

def test_job_recommendation_rest_api(email_address: str, resume_url: str):
    #url = 'https://operation-battleship-resume-7ek53.ondigitalocean.app/recommendation'  # Prod endpoint
    url = 'http://127.0.0.1:8000/recommendation' # Local endpoint
    payload = {
        "email_address": email_address,
        "resume_url": resume_url  # This should be the URL to the resume
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

def test_job_recomendation_module(resume_url, numberOfJobs):

    resume_as_string = getResumeAsString(resume_url)

    csvOfJobs = job_recommendation_main(resume_as_string, numberOfJobs)

    csvOfJobs.to_csv("recomendedJobs.csv")

    return

def test_report_generation_module(resume_url):


    resume_as_string = getResumeAsString(resume_url)

    recomendedJobs = [
        "9c3c221b-6cf1-4507-aac1-4b42bde93347",
        "e16e1e1d-d625-4724-a1c1-c9a488f80d8f",
        "464f5547-eadc-43da-bdf3-540deeecd989",
        "2413fac9-f883-4b74-b956-eac7b6f93627",
        "334b917f-d8a9-42b3-b76d-de48aaf2fa37",
        "5f8e871d-e13a-4c27-b5dd-ea9724ac5b08",
        "da343bb7-01fc-4719-8b61-7467c5e52020"
    ]

    listOfReportUrls = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobs)

    return listOfReportUrls

def combineRecomendationAndReports(resume_url, numberOfJobsToRecomend, numberOfReportsToGenerate):

    resume_as_string = getResumeAsString(resume_url)

    csvOfJobs = job_recommendation_main(resume_as_string, numberOfJobsToRecomend)

    csvOfJobs.to_csv("recomendedJobs.csv")

    recomendedJobs = csvOfJobs["job_posting_id"].head(numberOfReportsToGenerate).tolist()

    listOfReportUrls = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobs)

    return listOfReportUrls

def getResumeAsString(resume_url):

    response = requests.get(resume_url)
    response.raise_for_status()  # Raise an HTTPError for bad responses

    # Convert the downloaded content into a BytesIO object for pdfminer to read
    pdf_file = BytesIO(response.content)

    # Extract text from the PDF file
    resume_as_string = extract_text(pdf_file)

    return resume_as_string

if __name__ == "__main__":
    email_address = "caraway602@gmail.com"
    resume_url = "https://operationbattleship-resumes.nyc3.cdn.digitaloceanspaces.com/MatthewCarawayResume.pdf"  # Assuming this is the correct public URL to the resume
    
    #test_job_recommendation_rest_api(email_address, resume_url)


    #test_job_recomendation_module(resume_url, 5)

    #test_report_generation_module(resume_url)

    numberOfJobsToRecomend = 25
    numberOfReportsToGenerate = 5
    combineRecomendationAndReports(resume_url, numberOfJobsToRecomend, numberOfReportsToGenerate)

    
