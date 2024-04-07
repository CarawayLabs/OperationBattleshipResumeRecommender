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

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
        'overall_rank',
        'overall_score',
        'average_rank',
        'company_name',
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
    merged_df = similarJobsByTitleDataFrame.merge(similarJobsByResumeDataFrame, on='job_posting_id', how='outer')
    merged_df = merged_df.merge(similarJobsByShortDescriptionDataFrame, on='job_posting_id', how='outer')
    
    merged_df['average_rank'] = merged_df[['job-title-rank', 'full-posting-description-rank', 'short-job-description-rank']].mean(axis=1)
    merged_df['overall_score'] = merged_df[['job-title-score', 'full-posting-description-score', 'short-job-description-score']].mean(axis=1)

    merged_df.sort_values(by='overall_score', ascending=False, inplace=True)

    merged_df['rank_temp'] = merged_df.groupby('overall_score').cumcount()
    merged_df = merged_df.sample(frac=1, random_state=1).sort_values(by=['overall_score', 'rank_temp'], ascending=[False, True])
    
    merged_df['overall_rank'] = range(1, len(merged_df) + 1)
    merged_df.drop(columns=['rank_temp'], inplace=True)

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
        'short-job-description-rank'
    ]]

    return merged_df

if __name__ == "__main__":
    logging.info(f"Resume Recomendation Script has started.")
    main()