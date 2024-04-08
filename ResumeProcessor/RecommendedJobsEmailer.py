"""
Purpose:
Once we've created a list of jobs to recommend and the reports for the top selected jobs,
we need to email the reports back to our users.
"""

import logging
import sys
import os
import pandas as pd
import requests
import tempfile
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64

load_dotenv('.env')

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to download service account JSON from URL
def download_service_account_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        # Create a temporary file to store service account JSON
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as tmp:
            tmp.write(response.text)
        return path
    else:
        raise Exception(f"Failed to download service account file: {response.status_code}")

# Decide whether to use a local service account file or download it
SERVICE_ACCOUNT_PATH = os.getenv('SERVICE_ACCOUNT_PATH', None)
SERVICE_ACCOUNT_URL = os.getenv('SERVICE_ACCOUNT_URL', None)

if SERVICE_ACCOUNT_PATH and os.path.exists(SERVICE_ACCOUNT_PATH):
    SERVICE_ACCOUNT_FILE_PATH = SERVICE_ACCOUNT_PATH
    logging.info("Using local service account file.")
elif SERVICE_ACCOUNT_URL:
    SERVICE_ACCOUNT_FILE_PATH = download_service_account_json(SERVICE_ACCOUNT_URL)
    logging.info("Downloaded service account file from URL.")
else:
    raise EnvironmentError("Neither a local SERVICE_ACCOUNT_PATH nor a SERVICE_ACCOUNT_URL is properly configured.")


# Email address of the user on whose behalf the email is sent
USER_EMAIL = 'FindMyNextJob@CarawayLabs.com'

# The scope for the OAuth2 request.
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def convertDataFrameToHtmlTable(recommendedJobsDf):
    # Create a new DataFrame with only the desired columns
    df = recommendedJobsDf[['job_title', 'company_name', 'job_posting_date', 'salary_midpoint', 'is_ai', 'is_genai']].copy()
    
    # Store original URLs for hyperlinks
    job_posting_urls = recommendedJobsDf['posting_url']
    company_urls = recommendedJobsDf['linkedin_url']
    
    # Modify Job_title to include hyperlinks
    df['job_title'] = df.apply(lambda x: f'<a href="{job_posting_urls.loc[x.name]}">{x["job_title"]}</a>', axis=1)
    
    # Modify Company_name to include hyperlinks
    df['company_name'] = df.apply(lambda x: f'<a href="{company_urls.loc[x.name]}">{x["company_name"]}</a>', axis=1)
    
    # Convert the DataFrame to HTML, ensuring HTML content is not escaped
    html_table = df.to_html(escape=False, index=False)
    
    return html_table

def createHyperLinksForReports(listOfReportUrls):
    html_links = []

    for url in listOfReportUrls:
        # Extract the filename portion from the URL
        filename = url.split('/')[-1].replace('.html', '')
        
        # Determine the link text
        if 'JobReport' in filename:
            # Extract the report number and format the link text
            report_number = filename.split('JobReport')[-1]
            link_text = f"Job Report {report_number}"
        else:
            # Replace underscores with spaces and capitalize for other reports
            link_text = filename.replace('_', ' ').replace('MatthewCaraway ', '').replace('AIProductManager ', '').capitalize()

        # Generate the HTML link
        link_html = f'<a href="{url}">{link_text}</a><br>'
        html_links.append(link_html)

    # Concatenate all links into a single HTML string
    html_string = ''.join(html_links)
    return html_string

def load_email_template(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        return file.read()


def createEmailBody(listOfReportUrls, recommendedJobsDf):
    # Path to your template
    template_path = 'ResumeProcessor/HtmlTemplates/email_template.html'
    
    # Load the template
    htmlTemplate = load_email_template(template_path)

    # Generate dynamic content
    tableOfRecommendedJobs = convertDataFrameToHtmlTable(recommendedJobsDf)
    reportLinks = createHyperLinksForReports(listOfReportUrls)

    # Insert dynamic content into the template
    emailBody = htmlTemplate.replace('<!-- List of reportLinks goes here -->', reportLinks)\
                            .replace('<!-- tableOfRecommendedJobs goes here -->', tableOfRecommendedJobs)

    return emailBody

def sendEmail(emailAddress, listOfReportUrls, recommendedJobsDf, emailMessage):
    # Authenticate and construct service using the downloaded service account file
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE_PATH, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(USER_EMAIL)
    service = build('gmail', 'v1', credentials=delegated_credentials)
    
    # Create the email
    message = MIMEText(emailMessage, 'html')
    message['to'] = emailAddress
    message['subject'] = 'Your job recommendation report from Caraway Labs'
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
    
    # Send the email
    try:
        sent_message = service.users().messages().send(userId='me', body=raw_message).execute()
        logging.info(f"Finished Jobs Emailer Module. Message Id: {sent_message['id']}")
    except Exception as e:
        logging.error(f"An error occurred: {e}.")

def main(emailAddress, recommendedJobsDf, listOfReportUrls):
    emailMessage = createEmailBody(listOfReportUrls, recommendedJobsDf)
    messageId = sendEmail(emailAddress, listOfReportUrls, recommendedJobsDf, emailMessage)
    logging.info(f"We sent the email. Here is the message id: {messageId}")
    print(f"We sent the email. Here is the message id: {messageId}")
    return messageId

if __name__ == "__main__":
    # Example use of main function
    # You might need to adapt this based on how you intend to call this script
    if len(sys.argv) > 1:
        email_address = sys.argv[1]
        # Assuming `recommendedJobsDf` and `listOfReportUrls` are obtained here
        # main(email_address, recommendedJobsDf, listOfReportUrls)
    else:
        logging.error("Email address required as command-line argument.")

