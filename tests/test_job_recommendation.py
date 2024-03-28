import requests

def test_job_recommendation(email_address: str, resume_url: str):
    url = 'https://operation-battleship-resume-7ek53.ondigitalocean.app/recommendation'  # Fixed endpoint
    payload = {
        "email_address": email_address,
        "resume_url": resume_url  # This should be the URL to the resume, not the file path
    }
    
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

if __name__ == "__main__":
    email_address = "caraway602@gmail.com"
    resume_url = "https://operationbattleship-resumes.nyc3.cdn.digitaloceanspaces.com/MatthewCarawayResume.pdf"  # Assuming this is the correct public URL to the resume
    
    test_job_recommendation(email_address, resume_url)
