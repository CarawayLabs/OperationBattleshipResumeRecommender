import requests
from pdfminer.high_level import extract_text
from io import BytesIO
from ResumeProcessor.JobRecomendation import main as job_recommendation_main


def test_job_recommendation_rest_api(email_address: str, resume_url: str):
    #url = 'https://operation-battleship-resume-7ek53.ondigitalocean.app/recommendation'  # Prod endpoint
    url = 'http://127.0.0.1:8000/recommendation' # Local endpoint
    payload = {
        "email_address": email_address,
        "resume_url": resume_url  # This should be the URL to the resume, not the file path
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

def test_job_recomendation_module(resume_url, numberOfJobs):

    response = requests.get(resume_url)
    response.raise_for_status()  # Raise an HTTPError for bad responses

    # Convert the downloaded content into a BytesIO object for pdfminer to read
    pdf_file = BytesIO(response.content)

    # Extract text from the PDF file
    resume_as_string = extract_text(pdf_file)

    csvOfJobs = job_recommendation_main(resume_as_string, numberOfJobs)

    return

if __name__ == "__main__":
    email_address = "caraway602@gmail.com"
    resume_url = "https://operationbattleship-resumes.nyc3.cdn.digitaloceanspaces.com/MatthewCarawayResume.pdf"  # Assuming this is the correct public URL to the resume
    
    #test_job_recommendation_rest_api(email_address, resume_url)

    test_job_recomendation_module(resume_url, 5)

    
