import requests
import pandas as pd
from pdfminer.high_level import extract_text
from io import BytesIO
from ResumeProcessor.JobRecomendation import main as job_recommendation_main
from ResumeProcessor.CustomReportGenerator import main as custom_report_generator_main
from ResumeProcessor.RecommendedJobsEmailer import main as email_main

def test_job_recommendation_rest_api(email_address: str, resume_url: str):
    # Need to execute this command to start the server: uvicorn main:app --reload
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

    csvOfJobs.to_csv("testInput/recomendedJobs.csv")

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

def test_email_module():

    emailAddress = "matthew@carawaylabs.com"
    recommendedJobsDf = pd.read_csv("testInput/recomendedJobs.csv")
    listOfReportUrls = ['https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AIProductManager_JobReport1.html',
                        'https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AIProductManager_JobReport2.html', 
                        'https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AIProductManager_JobReport3.html', 
                        'https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AIProductManager_JobReport4.html', 
                        'https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AIProductManager_JobReport5.html', 
                        'https://operationbattleship-resumes.nyc3.digitaloceanspaces.com/MatthewCaraway_AdjacentRolesReport.html'
                        ]
    

    email_main(emailAddress, recommendedJobsDf, listOfReportUrls)

    return

def test_recomendation_and_report_modules(resume_url, numberOfJobsToRecomend, numberOfReportsToGenerate):

    resume_as_string = getResumeAsString(resume_url)

    csvOfJobs = job_recommendation_main(resume_as_string, numberOfJobsToRecomend)

    csvOfJobs.to_csv("testInput/recomendedJobs.csv")

    recomendedJobs = csvOfJobs["job_posting_id"].head(numberOfReportsToGenerate).tolist()

    listOfReportUrls = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobs)

    return listOfReportUrls

def test_recomendation_reports_and_email_modules(resume_url, numberOfJobsToRecomend, emailAddress):

    resume_as_string = getResumeAsString(resume_url)
    
    #Step 1 is to get the list of recomendations
    recommendedJobsDf = job_recommendation_main(resume_as_string, numberOfJobsToRecomend)
    
    #Step 2 is to provide reports for the top jobs. 
    recomendedJobsAsJobIdList = recommendedJobsDf["job_posting_id"].head(numberOfReportsToGenerate).tolist()
    listOfReportUrls = custom_report_generator_main("Matthew Caraway", resume_as_string, recomendedJobsAsJobIdList)

    #Step 3 is to send the email to the user. 
    email_main(emailAddress, recommendedJobsDf, listOfReportUrls)

    return

def getResumeAsString(resume_url):

    response = requests.get(resume_url)
    response.raise_for_status()  # Raise an HTTPError for bad responses

    # Convert the downloaded content into a BytesIO object for pdfminer to read
    pdf_file = BytesIO(response.content)

    # Extract text from the PDF file
    resume_as_string = extract_text(pdf_file)

    return resume_as_string

if __name__ == "__main__":
    
    #Key variables required for the recomendation system. 
    emailAddress = "matthew@carawaylabs.com"
    resume_url = "https://operationbattleship-resumes.nyc3.cdn.digitaloceanspaces.com/MatthewCarawayResume.pdf"
    numberOfJobsToRecomend = 25
    numberOfReportsToGenerate = 5

    test_job_recommendation_rest_api(emailAddress, resume_url)

    #test_job_recomendation_module(resume_url, 5)

    #test_report_generation_module(resume_url)

   # test_recomendation_and_report_modules(resume_url, numberOfJobsToRecomend, numberOfReportsToGenerate)

    #test_email_module()

    #test_recomendation_reports_and_email_modules(resume_url, numberOfJobsToRecomend, emailAddress)

    
