# Basic Flow for Processing a Resume - Upload via email. 

A user will send their resume to findmynextjob@carawaylabs.com

A zap will trigger and then move the file to S3 bucket. 

A zap will then call our own Rest API that is hosted on Digial Ocean. 
The zap will provide two items in the REST Call
1: Will include the S3 URL to the Resume
2: Will include the email address that submitted the resume

The API will then go get the resume our of the S3



# Idea for demo

We will create a QR Code that will take the user to a hosted folder of resumes that they can pick from. 
They can then attach that to an email and send to findmynextjob@carawaylabs.com

Our system will then process the


# Recomendation Algorithm

## Smoke Test
In the spirit of showing progress over perfection, we will demonstrate the most BASIC ability to recomend jobs when given a resume. This implementation is given in the HelloWorldJobRecomendation.py file

- A resume is provided as a PDF
- We convert the PDF -> Python String -> Nomic.AI Embeddings (768 Dimensions)
- We call Pinecone Vector DB and leverage Cosine Similarity to find the 25 KNN
- Return the list of 25 jobs and some basic metadata to the user. 

## First Inteligent Iteration
The above iteration is really basic and will likely recomend jobs that are not the best fit for the Job Applicant. 

### Job Reports from the LLM
For the top five jobs in the Inteligent Recomendation System, we will also call the LLM and have it return some additional information to aide the user. 
- One a scale of 1-10, how we written is the user's resume? Does it contain key words that are present in the Job Description?
- What key strengths does the user have that make them a good fit for the job?
- What gaps in skills or experience does the user have that present a risk for them landing the job?
- What key questions could the user ask for each job when they get an interview?

