# llmNarration = llmResponsesForTopJobs(recomendedJobsAndAllMetaData, numberOfJobsForLlmReports)
"""

Purpose: This Script takes in a string that represents a resume and then returns the list of recomended jobs

Rough outline: 
    For the top N jobs, call the LLM to generate the reports
        - Report 1: 
        - Report 1: 
        - Report 1: 
    Create each report as a PDF. 
    Save each report to the S3 Bucket
    Return a collection that contains the URL for each report

    Returns a collection that contains the URL for each report
"""

import datetime
import inspect
import logging
import json
import sys
import os
import boto3
import markdown2
import pdfkit
from pathlib import Path
from botocore.exceptions import NoCredentialsError
import pandas as pd
from dotenv import load_dotenv

from ResumeProcessor.LlmResumeProcessor import LlmResumeProcessor

from operation_battleship_common_utilities.JobPostingDao import JobPostingDao
from operation_battleship_common_utilities.JobSkillsDao import JobSkillsDao 
from operation_battleship_common_utilities.JobKeyWordsDao import JobKeyWordsDao 
from operation_battleship_common_utilities.CompanyDao import CompanyDao 


load_dotenv('.env')

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def main(candidateName, resumeAsString, job_posting_ids):
    urlsForPdfReports = []

    logging.debug(f"Number of job posting IDs: {len(job_posting_ids)}")

    bucketName = "operationbattleship-resumes"
    
    resumeAsJson = parseResume(resumeAsString)
    resumeAsJson = json.loads(resumeAsJson)
    jobTitle = resumeAsJson["Title"]

    logging.debug(f"Begin generating reports. Job Title = : {len(jobTitle)}")
    reportNumber = 1
    for job_posting_id in job_posting_ids:

        logging.debug(f"Begin generating reports. Working on report number: {reportNumber}")
        

        markdownString = createJobReports(candidateName, resumeAsString, job_posting_id, resumeAsJson)
        htmlFile = createReportFile(markdownString, candidateName, reportNumber, jobTitle)
        htmlFileUrl = upload_to_space(htmlFile, bucketName)
        urlsForPdfReports.append(htmlFileUrl)

        logging.debug(f"Completed with processing report number: {reportNumber}")

        reportNumber = reportNumber + 1

    adjacentRoles = createAdjacentRolesReport(candidateName, resumeAsString, resumeAsJson)
    htmlFile = createAdjacentRolesFile(adjacentRoles, candidateName)
    htmlFileUrl = upload_to_space(htmlFile, bucketName)
    urlsForPdfReports.append(htmlFileUrl)

    removeFilesLocally(urlsForPdfReports)

    return urlsForPdfReports

def parseResume(resumeAsString):

    llmResumeProcessor = LlmResumeProcessor()
    languageModelResponse = llmResumeProcessor.parseResume(resumeAsString)

    return languageModelResponse

def createJobReports(candidateName, resumeAsString, job_posting_id, resumeAsJson):
    """
    This function creates a series of job reports for the candidate for the given job_posting_id.

        - Provide a "Job Fit Score" 
        - Does the Candidate have the idenfitied skills for the job posting?
        - Does the Candidate's resume contain some of the identified key words found in the job posting?
        - Interview Preparation: Provide potential interview questions and guidance on how to effectively communicate the user's qualifications for the role.

    Return Value: String that represents the report that was generated. 
    """

    jobPostingDao = JobPostingDao()
    jobAsDataFrame = jobPostingDao.getJobByJobPostingId(job_posting_id)

    company_id = jobAsDataFrame.at[0, "company_id"]
    fullPostingDescription = jobAsDataFrame.at[0, "full_posting_description"]
    jobTitle = jobAsDataFrame.at[0, "job_title"]

    reportTitlepage = createReportTitlePage(candidateName, jobTitle, company_id)

    jobFitScore = createJobFitScore(resumeAsString, fullPostingDescription)
    interviewPrepReport = createInterviewPrepReport(jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson)
    jobSkillsReport = createJobSkillsReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson)
    keyWordAnalysis = createResumeKeywordAnalysisReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson)
    hiddenInTheJobPosting = createHiddenMessagessReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson)

    markdownNewline = "\n\n --- \n\n"
    pdfString = reportTitlepage + markdownNewline + jobFitScore + markdownNewline + interviewPrepReport +  markdownNewline + jobSkillsReport + markdownNewline + keyWordAnalysis + markdownNewline

    return pdfString

def createReportTitlePage(candidateName, job_title, company_id):

    companyDao = CompanyDao()
    company_name = companyDao.getCompanyNameByCompanyId(company_id)
    currentDate = datetime.datetime.now().strftime("%B %d %Y")  # Formats the current date as 'Month Day Year'

    # Assuming the file path is correct and the file exists in your project directory
    relativePathForTitlePageText = "ResumeProcessor/TextTemplates/TitlePageTemplate.txt"

    with open(relativePathForTitlePageText, 'r') as file:
        templateContent = file.read()
    
    # Replace placeholders with actual values
    reportTitlePage = templateContent.format(candidateName=candidateName, job_title=job_title, company_name=company_name, currentDate=currentDate)

    return reportTitlePage


def createJobFitScore(resumeAsString, fullPostingDescription):

    """
    Fit Score: Calculate a compatibility score based on skills, experience, and job requirements.
    Justification: Provides a quantifiable measure of how well the user matches the job.
    """

    llmResumeProcessor = LlmResumeProcessor()
    pdfString = llmResumeProcessor.createJobFitScore(resumeAsString, fullPostingDescription)

    return pdfString

def createInterviewPrepReport(jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson):
    """
    Interview Preparation: Provide potential interview questions and guidance on how to effectively communicate the user's qualifications for the role.
    """

    llmResumeProcessor = LlmResumeProcessor()
    jobInterviewPrepReport = llmResumeProcessor.generateJobInterviewPrepReport(jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson)

    return jobInterviewPrepReport

def createResumeKeywordAnalysisReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson):

    jobKeyWordsDao = JobKeyWordsDao()
    dataframeOfKeywordsForJob = jobKeyWordsDao.getKeywordsForJobID(job_posting_id)

    if dataframeOfKeywordsForJob.empty:
        jobKeywords = "Please see resume for jobKeywords."
    else:
        jobKeywords = '\n'.join(dataframeOfKeywordsForJob["item"])


    llmResumeProcessor = LlmResumeProcessor()
    resumeKeywordAnalysisReport = llmResumeProcessor.generateResumeKeywordAnalysisReport(jobKeywords, fullPostingDescription, resumeAsString, resumeAsJson)

    return resumeKeywordAnalysisReport

def createJobSkillsReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson):

    jobSkillsDao = JobSkillsDao()
    dataframeOfSkillsForJob = jobSkillsDao.getSkillsForJobID(job_posting_id)

    if dataframeOfSkillsForJob.empty:
        listOfSkillsForJob = "Please see resume for skills"
    else:
        listOfSkillsForJob = '\n'.join(dataframeOfSkillsForJob["item"])

    llmResumeProcessor = LlmResumeProcessor()
    skillsReport = llmResumeProcessor.generateSkillsReport(resumeAsString, fullPostingDescription, listOfSkillsForJob, resumeAsJson)

    return skillsReport

def createHiddenMessagessReport(job_posting_id, resumeAsString, fullPostingDescription, resumeAsJson):

    pdfString = "## We need to create a report that can help a job candidate \"read in between the lines\" of a job posting. "

    return pdfString

def createAdjacentRolesReport(candidateName, resumeAsString, resumeAsJson):

    llmResumeProcessor = LlmResumeProcessor()
    adjacentRolesReport = llmResumeProcessor.createAdjacentRolesReport(resumeAsString, resumeAsJson)

    return adjacentRolesReport

def createReportFile(markdownText, candidateName, reportNumber, jobTitle):

    fileName = f"{candidateName}_{jobTitle}_JobReport{reportNumber}.html"
    fileName = fileName.replace(" ", "")
    htmlPageTitle = f"{candidateName}'s Report"

    reportFile = createHtmlFile(markdownText, fileName, htmlPageTitle)

    return reportFile


def createHtmlFile(markdownText, fileName, htmlPageTitle):
    """
    Converts a markdown string to HTML and then saves it as an HTML file.

    FileName: {candidateName}_JobReport{reportNumber}_{jobTitle}.html
        EX: MatthewCaraway_JobReport1_ProductManager.html

    Return Value: FileName.html
    """

    htmlContent = markdown2.markdown(markdownText, extras=["toc", "tables", "smarty-pants"] )
    
    # Optional: Wrap the HTML in a <body> tag or apply CSS for better styling
    htmlContent = f"<html><head><title>{htmlPageTitle}</title></head><body>{htmlContent}</body></html>"
    
    # Save the HTML content to a file
    with open(fileName, 'w', encoding='utf-8') as file:
        file.write(htmlContent)
    
    return fileName


def createAdjacentRolesFile(markdownText, candidateName):

    """
    When given a string that represents the contents of the report, this function will create a PDF file from the string. 

    FileName: {candidateName}_AdjacentRolesReport.pdf
        EX: MatthewCaraway_AdjacentRolesReport.pdf

    Return Value: FileName.pdf
    """

    # Ensure candidateName doesn't have any whitespace
    candidateName = candidateName.replace(" ", "")
    fileName = f"{candidateName}_AdjacentRolesReport.html"

    htmlPageTitle = f"Potential Roles for {candidateName}"

    fileName = createHtmlFile(markdownText, fileName, htmlPageTitle)
    
    return fileName


def upload_to_space(file_name, bucket_name, object_name=None):
    """Upload a file to a DigitalOcean Space

    :param file_name: File to upload
    :param bucket_name: Bucket to upload to
    :param object_name: S3 object name. If not specified then file_name is used
    :return: True if file was uploaded, else False
    """

    logging.debug(f"Begin attempt to upload file named: {file_name}")
    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = file_name

    logging.debug(f"DO_SPACES_KEY: {os.getenv('DO_SPACES_KEY')}")
    logging.debug(f"DO_SPACES_SECRET: {os.getenv('DO_SPACES_SECRET')}")

    # Setup the session with DigitalOcean Spaces
    session = boto3.session.Session()
    client = session.client('s3',
                            region_name='nyc3',
                            endpoint_url='https://nyc3.digitaloceanspaces.com',
                            aws_access_key_id=os.getenv('DO_SPACES_KEY'),
                            aws_secret_access_key=os.getenv('DO_SPACES_SECRET'))

    # Upload the file
    try:
        client.upload_file(file_name, bucket_name, object_name)
        file_url = f"https://{bucket_name}.nyc3.digitaloceanspaces.com/{object_name}"
        print(f"{file_name} has been uploaded to {bucket_name}/{object_name}.")
        return file_url
    except NoCredentialsError:
        logging.error(f"Failed when trying to upload to space. Recieved: NoCredentialsError", NoCredentialsError)
        logging.error("Credentials not available")
        return None
    
    except Exception as e:
        logging.error("Some other error:", e)
        return None

    
def removeFilesLocally(urlsForPdfReports):
    for url in urlsForPdfReports:
        # Extracting the filename from the URL
        filename = url.split('/')[-1]
        
        # Check if the file exists locally
        if os.path.exists(filename):
            # Remove the file if it exists
            os.remove(filename)
            print(f"Removed: {filename}")
        else:
            print(f"File does not exist: {filename}")

    return

if __name__ == "__main__":

    current_function_name = inspect.stack()[0][3]
    logging.debug(f"Manually invoked: {current_function_name}")

    candidateName = "Matthew Caraway"
    resumeAsString ="My fake resume"
    job_posting_ids = [1, 2, 3, 4] 

    main(candidateName, resumeAsString, job_posting_ids)
