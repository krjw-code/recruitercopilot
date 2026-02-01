import azure.functions as func
import openai
import os
import pyodbc
import json
from decimal import Decimal
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="recruitercopilot", methods=["GET", "POST"])

def recruitercopilot(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        if req.method == "POST":
            # Handle POST request with a job description draft for assessment
            req_body = req.get_json()
            draft_description = req_body.get('draft_description')
            if not draft_description:
                return func.HttpResponse("Please provide a job description draft for assessment.", status_code=400)

            processed_draft = process_job_description_only(draft_description)
            logging.info(f"Assessed Job Description Draft: {processed_draft['evaluation']}")
            return func.HttpResponse(body=json.dumps(processed_draft, cls=CustomJSONEncoder, indent=4), status_code=200)

        elif req.method == "GET":
            job_id = req.params.get('job_id')
            if job_id:
                # Fetch and process a specific job description from the database
                job_description = fetch_job_description_by_id(job_id)
                if job_description:
                    processed_job = process_job_description(job_description)
                    logging.info(f"Processed Job ID {processed_job['job_id']}: {processed_job['evaluation']}")
                    return func.HttpResponse(body=json.dumps(processed_job, cls=CustomJSONEncoder, indent=4), status_code=200)
                else:
                    return func.HttpResponse("Job ID not found", status_code=404)
            else:
                # Process all job descriptions
                job_descriptions = fetch_job_descriptions()
                processed_jobs = [process_job_description(desc) for desc in job_descriptions]
                return func.HttpResponse(body=json.dumps(processed_jobs, cls=CustomJSONEncoder, indent=4), status_code=200)

    except Exception as e:
        error_message = {"error": str(e)}
        return func.HttpResponse(body=json.dumps(error_message), status_code=500, headers={"Content-Type": "application/json"})

def fetch_job_descriptions():
    connection_string = os.getenv('SQL_CONNECTION_STRING')
    query = "SELECT JobID, Description FROM JobPostings"
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return [{"job_id": row.JobID, "description": row.Description} for row in cursor.fetchall()]

def fetch_job_description_by_id(job_id):
    connection_string = os.getenv('SQL_CONNECTION_STRING')
    query = "SELECT JobID, Description FROM JobPostings WHERE JobID = ?"
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        cursor.execute(query, (job_id,))
        row = cursor.fetchone()
        if row:
            return {"job_id": row.JobID, "description": row.Description}
        return None

def process_job_description(job):
    assessment_criteria = """
    Please assess and score the following job description from 1 to 5 based on these criteria:
    - Readability: Use simple vocabulary, short sentences, active voice, and aim for a Flesch Reading Ease score of 60 or above.
    - Accessibility: Use clear headings, straightforward language, logical flow, and ensure formats are accessible.
    - Tone: Maintain a professional and friendly tone, use positive language, and avoid overly casual or aggressive language.
    - Content Clarity: Provide concise, direct information about role expectations and responsibilities, with clear details on required qualifications and skills.
    - Format: Use bullet points, maintain a consistent layout, and apply visual hierarchy techniques like font sizes and bolding to guide the reader.
    Here is the job description: '{job['description']}' 
        """

    prompt = f"{assessment_criteria}"

    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT") 
    openai.api_version = "2024-02-01"
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    response = openai.chat.completions.create(
        model="hr-gpt4o",  # Use an appropriate model
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": job['description']}
        ]

    )

    evaluation = response.choices[0].message.content.strip()
    # Split the evaluation into a structured format
    evaluation_lines = evaluation.split('\n')
    structured_evaluation = {}
    for line in evaluation_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            structured_evaluation[key.strip()] = value.strip()

    return {
        "job_id": job['job_id'],
        "description": job['description'],
        "evaluation": structured_evaluation
    }

def process_job_description_only(draft_description):
    assessment_criteria = """
    - Readability: Use simple vocabulary, short sentences, active voice, and aim for a Flesch Reading Ease score of 60 or above.
    - Accessibility: Use clear headings, straightforward language, logical flow, and ensure formats are accessible.
    - Tone: Maintain a professional and friendly tone, use positive language, and avoid overly casual or aggressive language.
    - Content Clarity: Provide concise, direct information about role expectations and responsibilities, with clear details on required qualifications and skills.
    - Format: Use bullet points, maintain a consistent layout, and apply visual hierarchy techniques like font sizes and bolding to guide the reader.
       """

    prompt = f"You are HR Copilot, your job is to help recruiters improve and write job advertisements. The user will provide a draft job description. Please assess and score their job description from 1 to 5 based on these criteria: {assessment_criteria}."

    openai.api_type = "azure"
    openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT") 
    openai.api_version = "2024-02-01"
    openai.api_key = os.getenv("AZURE_OPENAI_KEY")
    response = openai.chat.completions.create(
        model="hr-gpt4o",  # Use an appropriate model
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": draft_description}
        ]

    )

    evaluation = response.choices[0].message.content.strip()
    # Split the evaluation into a structured format
    evaluation_lines = evaluation.split('\n')
    structured_evaluation = {}
    for line in evaluation_lines:
        if ':' in line:
            key, value = line.split(':', 1)
            structured_evaluation[key.strip()] = value.strip()

    return {
        "description": draft_description,
        "evaluation": structured_evaluation
    }


def clean_sql_query(sql_query):
    return sql_query.replace('```sql', '').replace('```', '').strip()

class CustomJSONEncoder(json.JSONEncoder):
    """ Custom JSON Encoder for handling Decimal types in JSON """
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)
