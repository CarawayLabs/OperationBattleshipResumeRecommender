"""
This python script accepts a string as input that represents a resume. We then call the LLM to add structure and return a JSON object. 

"""

import logging
import json
import sys
import os
import pandas as pd
from pdfminer.high_level import extract_text
from dotenv import load_dotenv

from ResumeProcessor.LlmResumeProcessor import LlmResumeProcessor

from operation_battleship_common_utilities.OpenAICaller import OpenAICaller


load_dotenv('.env')

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')

def main(resumeAsString):

    parseResume(resumeAsString)

    return


def parseResume(resumeAsString):

    llmResumeProcessor = LlmResumeProcessor()
    languageModelResponse = llmResumeProcessor.parseResume(resumeAsString)

    return languageModelResponse



if __name__ == "__main__":
    logging.info(f"Resume Recomendation Script has started.")
    main()