import requests
import ssl

def test_job_recommendation(email_address: str, resume_filepath: str):
    url = 'https://operation-battleship-resume-7ek53.ondigitalocean.app/jobrecommendation'  # Adjust the URL if your API is hosted elsewhere
    files = {'resume': (resume_filepath, open(resume_filepath, 'rb'), 'application/pdf')}
    data = {'email_address': email_address}

    print("SSL library version:", ssl.OPENSSL_VERSION)
   
    response = requests.post(url, files=files, data=data, verify=False)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

if __name__ == "__main__":
    email_address = "caraway602@gmail.com"
    resume_filepath = r"C:\\Users\\caraw\\Downloads\\MatthewCarawayResume.pdf"  # Raw string for filepath
    
    test_job_recommendation(email_address, resume_filepath)
