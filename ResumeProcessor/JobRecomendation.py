"""

Purpose: This Script takes in a string that represents a resume and then returns the list of recomended jobs

Rough outline: 
    Call the LLM and process the resume and output as JSON
        - Title
        - Summary
        - Key Skills

    Embed these strings:
        - Full Resume
        - Title
        - Resume Summary

    Call the Vector DB for each of the embedded strings as find the top N KNN

    Returns the average score and rank 
"""

import logging
import json
import sys
import os
import pandas as pd
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

from ResumeProcessor.LlmResumeProcessor import LlmResumeProcessor

from operation_battleship_common_utilities.JobPostingDao import JobPostingDao
from operation_battleship_common_utilities.NomicAICaller import NomicAICaller
from operation_battleship_common_utilities.OpenAICaller import OpenAICaller
from operation_battleship_common_utilities.PineConeDatabaseCaller import PineConeDatabaseCaller

load_dotenv('.env')

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')


def main(resumeAsString, numberOfJobs):

    #Variables that are necessary for searching the correct Pinecone Index and Namespaces: 
    indexName = "job-postings" 
    namsSpaceForFullPosting = "full-posting-description"
    namsSpaceForJobTitles = "job-title"
    namsSpaceForShortJobDescrption = "short-job-description"

    resumeAsJson = parseResume(resumeAsString)

    resumeAsJson = json.loads(resumeAsJson)
        
    jobTitle = resumeAsJson["Title"]
    resumeSummary = resumeAsJson["CandidateSummary"]

    recomendedJobsAndAllMetaData = getJobsAndMetaData(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary)

    return recomendedJobsAndAllMetaData
    

def parseResume(resumeAsString):

    llmResumeProcessor = LlmResumeProcessor()
    languageModelResponse = llmResumeProcessor.parseResume(resumeAsString)

    return languageModelResponse

def getJobsAndMetaData(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary):

    completeSetOfRecommendedJobs = getRecommendedJobs(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary)

    jobPostingDao = JobPostingDao()
    recomendedJobsWithAllMetaData = jobPostingDao.getjobsFromListOfJobsIds(completeSetOfRecommendedJobs)

    merged_df = recomendedJobsWithAllMetaData.merge(completeSetOfRecommendedJobs, on='job_posting_id', how='outer')

    merged_df = merged_df.sort_values(by='overall_rank')

    columns_ordered = [
        'weightedScoreRank',
        'weightedScore',
        'overall_rank',
        'overall_score',
        'average_rank',
        'company_name',
        'linkedin_url',
        'job_title',
        'posting_url',
        'full_posting_description',
        'job_description',
        'is_ai',
        'is_genai',
        'salary_low',
        'salary_midpoint',
        'salary_high',
        'job_posting_id',
        'job-title-score',
        'job-title-rank',
        'full-posting-description-score',
        'full-posting-description-rank',
        'short-job-description-score',
        'short-job-description-rank',
        'job_salary',
        'job_category',
        'job_posting_date',
        'company_id',
        'posting_source',
        'posting_source_id',
        'job_posting_company_information',
        'job_insertion_date',
        'job_last_collected_date',
        'job_active',
        'city',
        'state',
        'job_skills',
        'is_ai_justification',
        'work_location_type'
    ]

    merged_df = merged_df[columns_ordered]

    return merged_df


def  getRecommendedJobs(namsSpaceForFullPosting, namsSpaceForJobTitles, namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeAsString, jobTitle, resumeSummary):

    #Call Pinecone and get the list of N KNN and return as a dictionary
    similarJobsByTitle = embedAndGetNeighbors(namsSpaceForJobTitles, indexName, numberOfJobs, jobTitle)
    similarJobsByResume = embedAndGetNeighbors(namsSpaceForFullPosting, indexName, numberOfJobs, resumeAsString)
    similarJobsByShortDescription = embedAndGetNeighbors(namsSpaceForShortJobDescrption, indexName, numberOfJobs, resumeSummary)

    #Convert the dictionary to DF and retun the overal recomendation
    recomendedJobs = combineRecomendedJobsAndGetAverages(similarJobsByTitle, similarJobsByResume, similarJobsByShortDescription)

    return recomendedJobs


def embedAndGetNeighbors(nameSpace, indexName, numberOfJobs, documentToEmbed):

    embeddedResume = convertToEmbedding(documentToEmbed)
    listOfNeightbors = getTopNearestNeighborsInNamespace(embeddedResume, numberOfJobs, indexName, nameSpace )

    return listOfNeightbors

def convertToEmbedding(documentToEmbed):

    nomicAICaller = NomicAICaller()
    embeddedResume = nomicAICaller.embedDocument(documentToEmbed) 

    return embeddedResume

def  getTopNearestNeighborsInNamespace(embeddedResume, numberOfNeighbors, indexName, nameSpace ):
    
    #Create an instance of PineConeDatabaseCaller and then search for top N KNN of the input vector
    pineconeApiKey = os.getenv("PINECONE_API_KEY")
    pineConeDatabaseCaller = PineConeDatabaseCaller(pineconeApiKey)
    listOfNeightbors = pineConeDatabaseCaller.query(embeddedResume[0], numberOfNeighbors, indexName, nameSpace)

    return listOfNeightbors

def combineRecomendedJobsAndGetAverages(similarJobsByTitle, similarJobsByResume, similarJobsByShortDescription):
    """
    
    """

    similarJobsByTitleDataFrame = convertToDataFrameAndInsertScore(similarJobsByTitle)
    similarJobsByResumeDataFrame = convertToDataFrameAndInsertScore(similarJobsByResume)
    similarJobsByShortDescriptionDataFrame = convertToDataFrameAndInsertScore(similarJobsByShortDescription)

    averageScoresAndRankDataFrame = combineDataFramesAndCreateAverages(similarJobsByTitleDataFrame, similarJobsByResumeDataFrame, similarJobsByShortDescriptionDataFrame)

    return averageScoresAndRankDataFrame


def convertToDataFrameAndInsertScore(pineconeResultSet):
    """
    Converts the dictionary to a Pandas Dataframe and adds the score as a column

    Expected columns in DF
        job_posting_id
        namespaceScore - Example: job_title_score
        namespaceRank - Example job_title_rank
    """
    
    data = []
    rank = 1
    nameSpace = pineconeResultSet['namespace']
    for match in pineconeResultSet['matches']:
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

def addMissingRankValues(dataFrame, columnNameToRank, columnNameWithScore):
    """
    This function will sort the dataframe by the columnNameWithScore. Highest score is provided first. 

    It will then list the rank value in the columnNameToRank
    
    """
    dataFrame.sort_values(by=columnNameWithScore, ascending=False, inplace=True)
    
    # Use the `rank` method to generate ranks based on the score, assuming higher scores get lower rank numbers.
    # method='first' ensures that ties are broken based on the order they appear in the data, which is now sorted by score.
    dataFrame[columnNameToRank] = dataFrame[columnNameWithScore].rank(method='first', ascending=False)
    
    return dataFrame
def addMissingScoreValues(dataFrame, columnName):
    """
    This function is responsible for adding missing values into a specific column of the dataframe. 

    We will get the lowest value in this column that is non-null or non-zero.
    Assign the lowest value to the varaiable called "lowestScore 
    And then we will order the df by job_posting_date column.
    Starting with the newest records that are missing values, We will assign the lowestScore. 
    We will reduce lowest score by .01 each record. 

    we might have a dataFrame called similarJobsByResumeDataFrame and it might have a column called full-posting-description-score. We will fill in descending values into any missing row of full-posting-description-score
    """
    dataFrame = dataFrame.sort_values(by=columnName, ascending=False)
    
    # Find the lowest non-null, non-zero value in the specified column
    lowestScore = dataFrame[dataFrame[columnName] > 0][columnName].min()
    
    # If there's no such value (all values are null or 0), set a default starting point
    if pd.isnull(lowestScore):
        lowestScore = 1  # Default starting point, adjust as needed
    
    # Iterate over rows in the DataFrame
    for index, row in dataFrame.iterrows():
        # Check if the current row's value in the specified column is missing
        if pd.isnull(row[columnName]) or row[columnName] == 0:
            # Assign the current lowestScore to the missing value
            dataFrame.at[index, columnName] = lowestScore
            # Decrement lowestScore for the next missing value, if any
            lowestScore -= 0.0001

    return dataFrame

def modifiedWeights(dataFrame):
    # Weights
    jobTitleWeight = 0.3  # Reduced weight for Job-title-score
    fullJobPostingWeight = 0.4  # Increased weight for Full-posting-description-score
    summarizedJobWeight = 0.3  # Balanced weight for Short-job-description-score
    
    # Calculate the weighted average score
    dataFrame['weightedScore'] = (dataFrame['job-title-score'] * jobTitleWeight + 
                                  dataFrame['full-posting-description-score'] * fullJobPostingWeight + 
                                  dataFrame['short-job-description-score'] * summarizedJobWeight)
    
    # Sort the dataframe by the weightedScore in descending order and then use rank to assign a rank
    dataFrame['weightedScoreRank'] = dataFrame['weightedScore'].rank(ascending=False, method='min')
    
    return dataFrame


def combineDataFramesAndCreateAverages(similarJobsByTitleDataFrame, similarJobsByResumeDataFrame, similarJobsByShortDescriptionDataFrame):
    """
    This function takes in the three dataframes and averages the score and also averages the rank. Will create a new DF as a return value. 

    Input Args:
        similarJobsByTitleDataFrame
        similarJobsByResumeDataFrame
        similarJobsByShortDescriptionDataFrame

    Return:
        averageRankAndScore
            - Contains all the original columns and also adds overall_rank, overall_score, and average_rank
            job_posting_id
            overall_rank
            overall_score
            job-title-score
            job-title-rank
            full-posting-description-score
            full-posting-description-rank
            short-job-description-score
            short-job-description-rank
    """

    # comment

    merged_df = similarJobsByTitleDataFrame.merge(similarJobsByResumeDataFrame, on='job_posting_id', how='outer')
    merged_df = merged_df.merge(similarJobsByShortDescriptionDataFrame, on='job_posting_id', how='outer')

    merged_df = addMissingScoreValues(merged_df, "job-title-score")
    merged_df = addMissingScoreValues(merged_df, "full-posting-description-score")
    merged_df = addMissingScoreValues(merged_df, "short-job-description-score")
    
    merged_df = addMissingRankValues(merged_df, "job-title-rank",  "job-title-score") 
    merged_df = addMissingRankValues(merged_df, "full-posting-description-rank", "full-posting-description-score")
    merged_df = addMissingRankValues(merged_df, "short-job-description-rank", "short-job-description-score")


    merged_df['average_rank'] = merged_df[['job-title-rank', 'full-posting-description-rank', 'short-job-description-rank']].mean(axis=1)
    merged_df['overall_score'] = merged_df[['job-title-score', 'full-posting-description-score', 'short-job-description-score']].mean(axis=1)

    merged_df.sort_values(by='overall_score', ascending=False, inplace=True)

    merged_df['rank_temp'] = merged_df.groupby('overall_score').cumcount()
    merged_df = merged_df.sample(frac=1, random_state=1).sort_values(by=['overall_score', 'rank_temp'], ascending=[False, True])
    
    merged_df['overall_rank'] = range(1, len(merged_df) + 1)
    merged_df.drop(columns=['rank_temp'], inplace=True)

    merged_df = modifiedWeights(merged_df)

    merged_df = merged_df[[
        'job_posting_id',
        'overall_rank',
        'overall_score',
        'average_rank',
        'job-title-score',
        'job-title-rank',
        'full-posting-description-score',
        'full-posting-description-rank',
        'short-job-description-score',
        'short-job-description-rank',
        'weightedScore',
        'weightedScoreRank'
    ]]

    return merged_df

if __name__ == "__main__":
    logging.info(f"Resume Recomendation Script has started.")
    main()