import requests

def test_job_recommendation(email_address: str, resume_filepath: str):
    url = 'https://operation-battleship-resume-7ek53.ondigitalocean.app/jobrecommendation'
    files = {'resume': (resume_filepath, open(resume_filepath, 'rb'), 'application/pdf')}
    data = {'email_address': email_address}  # This will be sent as form data, not as JSON
    
    response = requests.post(url, files=files, data=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

if __name__ == "__main__":
    email_address = "caraway602@gmail.com"
    resume_filepath = r"https://operationbattleship-resumes.nyc3.cdn.digitaloceanspaces.com/MatthewCarawayResume.pdf"
    
    test_job_recommendation(email_address, resume_filepath)
