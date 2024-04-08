"""
Purpose:
Once we've created a list of jobs to recomend and the reports for the top selected jobs, we need to email the reports back to our users. 



"""

import logging
import sys
import os
import pandas as pd
from dotenv import load_dotenv


from google.oauth2 import service_account
from googleapiclient.discovery import build
from email.mime.text import MIMEText
import base64


load_dotenv('.env')

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)s:%(name)s:%(funcName)s: %(message)s')
logger = logging.getLogger(__name__)



SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_PATH')

# Email address of the user in whose behalf the email is sent
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
    
    
    # Authenticate and construct service
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    delegated_credentials = credentials.with_subject(USER_EMAIL)
    service = build('gmail', 'v1', credentials=delegated_credentials)
    
    # Create the email
    message = MIMEText(emailMessage, 'html')
    message['to'] = emailAddress
    message['subject'] = 'Your job recomendation report from Caraway Labs'
    raw_message = {'raw': base64.urlsafe_b64encode(message.as_string().encode()).decode()}
    
    # Send the email
    try:
        sent_message = service.users().messages().send(userId='me', body=raw_message).execute()
        print(f"Message Id: {sent_message['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")
def main(emailAddress, recommendedJobsDf, listOfReportUrls):

    emailMessage = createEmailBody(listOfReportUrls, recommendedJobsDf)
    sendEmail(emailAddress, listOfReportUrls, recommendedJobsDf, emailMessage)

    return 


if __name__ == "__main__":
    
    args = {"name": sys.argv[1]} if len(sys.argv) > 1 else {}
    



