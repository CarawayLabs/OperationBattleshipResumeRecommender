"""
This Python script is used to call the Job Posting Dao and return the top 10 most recently posted AI PM Jobs. 

"""
import logging
import pandas as pd
import os
from dotenv import load_dotenv


load_dotenv('.env')

log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')



def main():

    return

if __name__ == "__main__":
    logging.info(f"Resume Recomendation Script has started.")
    main()