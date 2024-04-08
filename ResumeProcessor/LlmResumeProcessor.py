"""

"""


import logging
import json
import os
from botocore.exceptions import NoCredentialsError
from dotenv import load_dotenv

from operation_battleship_common_utilities.OpenAICaller import OpenAICaller

load_dotenv('.env')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class LlmResumeProcessor:

    def __init__(self):
        
        logging.info(f"{self.__class__.__name__} class initialized")

        return
    
    def parseResume(self, resumeAsString):

        llmChain = self.createLlmPromptForResumeAnalysis(resumeAsString)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)

        return languageModelResponse
    
    def generateSkillsReport(self, resumeAsString, fullPostingDescription, listOfSkillsForJob, resumeAsJson):
         
        llmChain = self.createLlmPromptForSkillsReport(resumeAsString, resumeAsJson, fullPostingDescription, listOfSkillsForJob)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)
         
        return languageModelResponse
    
    def createJobFitScore(self, resumeAsString, fullPostingDescription):
        
        llmChain = self.createLlmPromptForJobFitScore(resumeAsString, fullPostingDescription)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)
         
        return languageModelResponse
    
    def createAdjacentRolesReport(self, resumeAsString, resumeAsJson):
         
        llmChain = self.createLlmPromptForAdjacentRolesReport(resumeAsString, resumeAsJson)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)
         
        return languageModelResponse
         
    def generateJobInterviewPrepReport(self, jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson):

        llmChain = self.createLlmPromptForInterviewPrepReport(jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)
         
        return languageModelResponse
    
    def generateResumeKeywordAnalysisReport(self, jobKeywords, fullPostingDescription, resumeAsString, resumeAsJson):

        llmChain = self.createLlmPromptForResumeKeywordAnalysisReport(jobKeywords, fullPostingDescription, resumeAsString, resumeAsJson)
        open_ai_caller = OpenAICaller()
        languageModelResponse = open_ai_caller.get_completion(llmChain)

        return languageModelResponse
    
    def createLlmPromptForSkillsReport(self, resumeAsString, resumeAsJson, fullPostingDescription, listOfSkillsForJob):

        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/SkillsAnalyzerLlmChainV2.json'
        script_dir = os.path.dirname(__file__)  
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            promptMessages = json.load(file)

        skillsList = resumeAsJson["CandidateSkills"]
        skills = '\n'.join(skillsList)
        
        messages=[
            {
            "role": "system",
            "content": promptMessages["systemContentOne"]
            },        
            {
            "role": "user",
            "content": promptMessages["userContentOne"] + listOfSkillsForJob
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentOne"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentTwo"] + fullPostingDescription
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentTwo"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentThree"] + skills
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentThree"]
            },                        {
            "role": "user",
            "content": promptMessages["userContentFour"] + resumeAsString
            }
        ]

        return messages
    
    def createLlmPromptForAdjacentRolesReport(self, resumeAsString, resumeAsJson):

        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/AdjacentRolesLlmChain.json'
        script_dir = os.path.dirname(__file__)  
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            promptMessages = json.load(file)

        skillsList = resumeAsJson["CandidateSkills"]
        skills = '\n'.join(skillsList)

        potentialRolesList = resumeAsJson["PotentialFutureJobTitles"]
        potentialRoles = '\n'.join(potentialRolesList)
        
        messages=[
            {
            "role": "system",
            "content": promptMessages["systemContentOne"]
            },        
            {
            "role": "user",
            "content": promptMessages["userContentOne"] + resumeAsJson["Title"]
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentOne"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentTwo"] + potentialRoles
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentTwo"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentThree"] + skills
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentThree"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentFour"] + resumeAsString
            }
        ]

        return messages

    def createLlmPromptForInterviewPrepReport(self, jobAsDataFrame, fullPostingDescription, resumeAsString, resumeAsJson):

        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/InterviewQuestionsLlmChain.json'
        script_dir = os.path.dirname(__file__)  
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            promptMessages = json.load(file)

        json_string = jobAsDataFrame.to_json(orient='records')

        messages=[
            {
            "role": "system",
            "content": promptMessages["systemContentOne"]
            },        
            {
            "role": "user",
            "content": promptMessages["userContentOne"] + fullPostingDescription
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentOne"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentTwo"] + json_string
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentTwo"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentThree"] + resumeAsString
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentThree"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentFour"] + json.dumps(resumeAsJson)
            }    
        ]

        return messages
    
    def createLlmPromptForJobFitScore(self, resumeAsString, fullPostingDescription):

        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/JobFitScoreLlmChain.json'

        script_dir = os.path.dirname(__file__) 
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            promptMessages = json.load(file)

        messages=[
            {
            "role": "system",
            "content": promptMessages["systemContentOne"]
            },        
            {
            "role": "user",
            "content": promptMessages["userContentOne"] + fullPostingDescription
            },
            {
            "role": "assistant",
            "content": promptMessages["assistantContentOne"]
            },
            {
            "role": "user",
            "content": promptMessages["userContentTwo"] + resumeAsString
            }
        ]

        return messages
        
    def createLlmPromptForResumeAnalysis(self, resumeAsString):
    
        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/ResumeSummarizerLlmChain.json'
        script_dir = os.path.dirname(__file__)  
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
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
    
    def createLlmPromptForResumeKeywordAnalysisReport(self, jobKeywords, fullPostingDescription, resumeAsString, resumeAsJson):

        promptMessagesAsJsonFileRelativePath = 'LlmTemplates/KeywordsLlmChain.json'
        script_dir = os.path.dirname(__file__)  
        abs_file_path = os.path.join(script_dir, promptMessagesAsJsonFileRelativePath)
        
        with open(abs_file_path, 'r', encoding='utf-8') as file:
            promptMessagesAsDataframe = json.load(file)


        # We need to figure out the attribute name in resumeAsJson
        resumeKeywordsList = resumeAsJson["ResumeKeywords"]
        resumeKeywords = '\n'.join(resumeKeywordsList)

        messages=[
            {
            "role": "system",
            "content": promptMessagesAsDataframe["systemContentOne"]
            },        
            {
            "role": "user",
            "content": promptMessagesAsDataframe["userContentOne"] + jobKeywords
            },
            {
            "role": "assistant",
            "content": promptMessagesAsDataframe["assistantContentOne"]
            },
            {
            "role": "user",
            "content": promptMessagesAsDataframe["userContentTwo"] + fullPostingDescription
            },
            {
            "role": "assistant",
            "content": promptMessagesAsDataframe["assistantContentTwo"]
            },
            {
            "role": "user",
            "content": promptMessagesAsDataframe["userContentThree"] + resumeKeywords
            },
            {
            "role": "assistant",
            "content": promptMessagesAsDataframe["assistantContentThree"]
            },
            {
            "role": "user",
            "content": promptMessagesAsDataframe["userContentFour"] + resumeAsString
            }
        ]

        return messages