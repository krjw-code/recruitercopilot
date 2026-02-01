# Recruiter Copilot

An Azure Function that helps HR recruiters improve job descriptions using Azure OpenAI.

## Overview

This function assesses and scores job descriptions based on best practices for:
- **Readability** - Simple vocabulary, short sentences, active voice
- **Accessibility** - Clear headings, logical flow, accessible formats
- **Tone** - Professional and friendly, positive language
- **Content Clarity** - Concise role expectations, clear qualifications
- **Format** - Bullet points, consistent layout, visual hierarchy

## Features

- Score job descriptions from 1-5 on each criterion
- Fetch and assess job postings from Azure SQL database
- Assess draft job descriptions directly via API
- Structured evaluation output

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/recruitercopilot` | Fetch and assess all job descriptions from database |
| GET | `/api/recruitercopilot?job_id=123` | Assess a specific job description by ID |
| POST | `/api/recruitercopilot` | Assess a draft job description |

## Request Format (POST)

```json
{
  "draft_description": "We are looking for a Software Engineer to join our team..."
}
```

## Response Example

```json
{
  "job_id": 123,
  "description": "Software Engineer position...",
  "evaluation": {
    "Readability": "4/5 - Good use of active voice...",
    "Accessibility": "3/5 - Could use more headings...",
    "Tone": "5/5 - Professional and welcoming...",
    "Content Clarity": "4/5 - Clear requirements...",
    "Format": "3/5 - Consider adding bullet points..."
  }
}
```

## Database Schema

The function queries a `Reckitt_Sample_JobPosting` table with columns:
- `JobID` - Unique job identifier
- `Description` - Job description text

## Quick Start

### Prerequisites

- Python 3.11+
- Azure Functions Core Tools v4
- Azure OpenAI resource (GPT-4o deployment)
- Azure SQL Database with job postings

### Setup

1. Clone the repository
2. Create virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `local.settings.json` from template:
```bash
cp local.settings.template.json local.settings.json
# Edit with your credentials
```

5. Run locally:
```bash
func start
```

### Test

```bash
# Assess a draft description
curl -X POST http://localhost:7071/api/recruitercopilot \
  -H "Content-Type: application/json" \
  -d '{"draft_description": "Looking for an experienced developer to build cool stuff. Must be good at coding."}'

# Get all job descriptions
curl http://localhost:7071/api/recruitercopilot

# Get specific job
curl "http://localhost:7071/api/recruitercopilot?job_id=1"
```

## Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | Yes |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key | Yes |
| `SQL_CONNECTION_STRING` | Azure SQL connection string | Yes |

## Architecture

```
┌─────────────────────────────────────────┐
│           Recruiter Copilot             │
│          (Azure Function)               │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    ▼                         ▼
┌────────────┐         ┌─────────────┐
│  Azure     │         │  Azure SQL  │
│  OpenAI    │         │  Database   │
│  (GPT-4o)  │         │             │
└────────────┘         └─────────────┘
    │                         │
    │  Scoring &              │ Job Postings
    │  Evaluation             │
    └─────────┬───────────────┘
              ▼
       Structured
       Assessment
```

## License

MIT
