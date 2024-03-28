"""
Call the LLM and process the resume and output as JSON
    - Title
    - Summary
    - Key Skills

Embed these strings:
    - Full Resume
    - Title
    - Resume Summary

Call the Vector DB for each of the embedded strings as find KNN
Persist to the spreadseet

Get the average rank for each of the values and then create a ranked alogorthm

Get the average score for each of the values and then create a ranked algorthm. 

"""

import logging
import json
import sys
import os
import pandas as pd
from pdfminer.high_level import extract_text
from dotenv import load_dotenv
from operation_battleship_common_utilities.JobPostingDao import JobPostingDao
from operation_battleship_common_utilities.NomicAICaller import NomicAICaller
from operation_battleship_common_utilities.OpenAICaller import OpenAICaller
from operation_battleship_common_utilities.PineConeDatabaseCaller import PineConeDatabaseCaller

load_dotenv('.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def main(resumeAsString, numberOfJobs):

    #Variables that are used for this script: 
    indexName = "job-postings" 
    namsSpaceForFullPosting = "full-posting-description"
    namsSpaceForJobTitles = "job-title"
    namsSpaceForShortJobDescrption = "short-job-description"

    resumeAsJson = parseResume(resumeAsString)
    resumeAsJson = json.loads(resumeAsJson)
        
    jobTitle = resumeAsJson["Title"]
    resumeSummary = resumeAsJson["CandidateSummary"]
    
    """
    Call Pinecone for each index and get the top N KNN
    Merge into a dataframe that contains ALL results
    Get the averages
    Call the Job Dao for all the Job IDs
    """
    completeSetOfRecommendedJobs = getRecommendedJobs(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary)



    namsSpaceForJobTitles = "job-title"
    recommendedJobsFromFullPosting = recomendedJobsWhenGivenNamespaceCallsDB(namsSpaceForFullPosting, indexName, numberOfJobs, resumeAsString)
    recommendedJobsFromJobTitle = recomendedJobsWhenGivenNamespaceCallsDB(namsSpaceForJobTitles, indexName, numberOfJobs, jobTitle)
    recommendedJobsFromShortJobDescription = recomendedJobsWhenGivenNamespaceCallsDB(namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeSummary)

    averageRecomendation = combineDataFramesAndGetAverages(recommendedJobsFromFullPosting, recommendedJobsFromJobTitle, recommendedJobsFromShortJobDescription)

    return averageRecomendation

def returnPdfResumeAsString(resumeRelativeFilePath):
    """
    This function takes in the resume as a PDF and is responsible for opening the file and converting it to a string so it can be returned.

    Args: 
        - resumeRelativeFilePath this is the relative file path to the document that represents the applican'ts resume. Its expected to be in PDF Form. 

    Return Value: A Python String that represents 
    """

    resumeAsString = extract_text(resumeRelativeFilePath)

    return resumeAsString

def parseResume(resumeAsString):

    llmChain = createLlmPromptForResumeAnalysis(resumeAsString)
    
    # Call the OpenAI API with the job description
    open_ai_caller = OpenAICaller()
    languageModelResponse = open_ai_caller.get_completion(llmChain)

    return languageModelResponse

def  getRecommendedJobs(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary):

    return 
    
def recomendedJobsWhenGivenNamespaceCallsDB(nameSpace, indexName, numberOfJobs, documentToEmbed):

    embeddedResume = convertToEmbedding(documentToEmbed)

    listOfNeightbors = getTopNearestNeighborsInNamespace(embeddedResume, numberOfJobs, indexName, nameSpace )

    recomendedJobs = getJobPostingDataForNearestNeighbors(listOfNeightbors, nameSpace)

    return recomendedJobs


def convertToEmbedding(documentToEmbed):
    """
    Converts the resume text string into embedding and then returns this value. 
    """
    nomicAICaller = NomicAICaller()
    embeddedResume = nomicAICaller.embedDocument(documentToEmbed) 

    return embeddedResume

def  getTopNearestNeighborsInNamespace(embeddedResume, numberOfNeighbors, indexName, nameSpace ):
    
    #Create an instance of PineConeDatabaseCaller and then search for top N KNN of the input vector
    pineconeApiKey = os.getenv("PINECONE_API_KEY")
    pineConeDatabaseCaller = PineConeDatabaseCaller(pineconeApiKey)
    listOfNeightbors = pineConeDatabaseCaller.query(embeddedResume[0], numberOfNeighbors, indexName, nameSpace)

    return listOfNeightbors

def getJobPostingDataForNearestNeighbors(listOfNeightbors, nameSpace):
    logging.debug(f"Datatype of the listOfNeightbors variable is: {type(listOfNeightbors)}")
    #print(listOfNeightbors)

    pineconeResultsAsDataframe = convertPineconeResultsToDataframe(listOfNeightbors, nameSpace)

    jobPostingDao = JobPostingDao()
    recomendedJobs = jobPostingDao.getjobsFromListOfJobsIds(pineconeResultsAsDataframe)

    mergedDataFrame = pd.merge(recomendedJobs, pineconeResultsAsDataframe, on="job_posting_id", how="inner")

    return mergedDataFrame

def convertPineconeResultsToDataframe(listOfNeightbors, nameSpace):

    data = []
    rank = 1
    for match in listOfNeightbors['matches']:
        # Dynamically create keys using the namespace
        score_key = f"{nameSpace}-score"
        rank_key = f"{nameSpace}-rank"
        entry = {
            'job_posting_id': match['id'],
            score_key: match['score'],
            rank_key: rank 
        }
        data.append(entry)
        rank = rank + 1

    # Creating the dataframe
    df = pd.DataFrame(data)

    return df

def createLlmPromptForResumeAnalysis(resumeAsString):

    promptMessagesAsJsonFileRelativePath = 'LlmTemplates/ResumeSummarizerLlmChain.json'

    # Get the absolute path of the script
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
    
    # Step 1: Open the JSON file
    with open(abs_file_path, 'r', encoding='utf-8') as file:
        promptMessagesAsDataframe = json.load(file)

    messages=[
        {
        "role": "system",
        "content": promptMessagesAsDataframe["systemContentOne"]
        },        
        {
        "role": "user",
        "content": promptMessagesAsDataframe["userContentOne"]
        },
        {
        "role": "assistant",
        "content": promptMessagesAsDataframe["assistantContentOne"]
        },
        {
        "role": "user",
        "content": promptMessagesAsDataframe["userContentTwo"]
        },
        {
        "role": "assistant",
        "content": promptMessagesAsDataframe["assistantContentTwo"]
        },
        {
        "role": "user",
        "content": promptMessagesAsDataframe["userContentThree"]
        },
        {
        "role": "assistant",
        "content": promptMessagesAsDataframe["assistantContentThree"]
        },
        {
        "role": "user",
        "content": resumeAsString
        }
    ]

    return messages




def combineDataFramesAndGetAverages(recommendedJobsFromFullPosting, recommendedJobsFromJobTitle, recommendedJobsFromShortJobDescription):
    """
    Purpose: 
        We've got three Dataframes that contain their own rank and score for recomended jobs. We need to combine these results and then produce a sinle rank and score for all jobs combined. We can use job_id column from each DF to prove uniqueness. 

        1: Combine the three DF into a single DG called averageRecomendations
            Create three columns in this new DF, Rank, Overall_Recomendation, Overall_Score. These are the first columns in this new DF
        2: Populate Overall_Score by getting the average score for the three DF
        3: Populate Overall_Rank by getting the average rank for the three DF
        4: Sort by Overall_Rank, highest rank first.
                Populate the Rank based on the Overall_Rank 
        

    Args:
        The three input args are almost identical, except the naming of two columns in each DF. 
        recommendedJobsFromFullPosting - 
            'full-posting-description-rank'
            'full-posting-description-score'
        recommendedJobsFromJobTitle -            
            'job-title-rank'
            'job-title-score'
        recommendedJobsFromShortJobDescription -
            'short-job-description-rank'
            'short-job-description-score'

    
    Return Value:
        averageRecomendations - a Pandas Dataframe that represents all of the jobs and three  new columns Overall_Recomendation and Overall_Score and Rank 
    """
    # Merge the DataFrames on 'job_id'
    mergedDF = pd.merge(recommendedJobsFromFullPosting, recommendedJobsFromJobTitle, on="job_posting_id", how="outer")
    mergedDF = pd.merge(mergedDF, recommendedJobsFromShortJobDescription, on="job_posting_id", how="outer")
    #mergedDF = recommendedJobsFromFullPosting.merge(recommendedJobsFromJobTitle, on='job_posting_id', suffixes=('_fp', '_jt')).merge(recommendedJobsFromShortJobDescription, on='job_posting_id')
    
    # Calculate Overall_Score and Overall_Rank
    mergedDF['Overall_Score'] = mergedDF[['full-posting-description-score', 'job-title-score', 'short-job-description-score']].mean(axis=1)
    mergedDF['Overall_Rank'] = mergedDF[['full-posting-description-rank', 'job-title-rank', 'short-job-description-rank']].mean(axis=1)
    
    # Sort by Overall_Rank in descending order
    mergedDF.sort_values(by='Overall_Rank', ascending=False, inplace=True)
    
    # Assign new rank based on sorted order
    mergedDF['Rank'] = range(1, len(mergedDF) + 1)
    
    # Select and reorder the relevant columns
    averageRecommendations = mergedDF[['job_posting_id', 'Rank', 'Overall_Rank', 'Overall_Score']]
    
    return mergedDF


if __name__ == "__main__":
    logging.info(f"Hello World - Resume Recomendation Script has started.")
    main()