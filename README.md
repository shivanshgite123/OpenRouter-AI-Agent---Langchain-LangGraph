# OpenRouter  AI - Multi-Agent AI Research System

OpenRouter- is a multi-agent AI research system built using LangChain and LangGraph.

It takes a research question, searches the web, collects information, analyzes the results, checks the research quality, and generates a final research report with sources.

The project uses FastAPI as the backend and Streamlit as the only frontend.

## Architecture

```text
Streamlit
    |
    v
FastAPI
    |
    v
LangGraph
    |
    v
LangChain Agents
    |
    v
Search, Scraping, Reranking and LLM
```

## Main Workflow

```text
Question
   |
Planner
   |
Query Rewriter
   |
Web Search
   |
Reader
   |
Reranker
   |
Research Analyst
   |
Critic
   |
Replanner (if more research is needed)
   |
Solver
   |
Evaluator
   |
Final Report
```

## Main Components

### Planner

Breaks the user's question into smaller research tasks.

### Query Rewriter

Creates useful search queries from the research plan.

### Search Agent

Searches the web using Tavily.

### Reader

Downloads and extracts useful content from web pages.

### Reranker

Finds the most relevant documents. Jina Reranker is used when the API key is available. Otherwise, the system uses a simple fallback method.

### Research Analyst

Analyzes the collected information and extracts important findings with source references.

### Critic

Checks whether enough information has been collected and identifies missing information.

### Replanner

Creates additional search queries when the critic finds that more research is required.

### Solver

Uses the research findings to generate the final report.

### Evaluator

Checks the final report for completeness, source coverage, and citation coverage.

## LangChain and LangGraph

LangChain is used for:

* LLM integration
* Prompts
* Structured outputs
* Tools
* Web search
* Document processing

LangGraph is used for:

* Agent orchestration
* Shared research state
* Conditional routing
* Reflection
* Replanning
* Research loops

The research loop is limited by `MAX_REPLANS` so it cannot run forever.

## FastAPI

The FastAPI backend provides these endpoints:

```text
GET  /health
POST /api/research
GET  /api/research/{id}/status
GET  /api/research/{id}
```

Research runs in the background while the Streamlit interface checks the current status.

## Streamlit

Streamlit is the only frontend.

It displays:

* Research plan
* Search results
* Sources
* Evidence
* Agent activity
* Reflection
* Final report
* Evaluation

The application does not display hidden chain-of-thought.

## Tools

The project uses:

* LangChain
* LangGraph
* FastAPI
* Streamlit
* Tavily
* BeautifulSoup
* Jina Reranker
* OpenAI or Google Gemini

## Installation

Create a virtual environment:

```bash
python -m venv .venv
```

For Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

For Linux or macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the environment file:

```bash
cp .env.example .env
```

On Windows, you can create `.env` manually.

## Environment Variables

```env
MODEL_PROVIDER=google
MODEL_NAME=gemini-2.5-flash

GOOGLE_API_KEY=
OPENAI_API_KEY=
TAVILY_API_KEY=
JINA_API_KEY=

MAX_SEARCH_RESULTS=10
MAX_REPLANS=2

BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
STREAMLIT_PORT=8501

BACKEND_URL=http://localhost:8000

MOCK_MODE=false
```

## Run the Project

Start FastAPI:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Then start Streamlit in another terminal:

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

## Mock Mode

You can run the project without API keys:

```bash
MOCK_MODE=true
```

Mock mode is useful for testing the complete workflow without external APIs.

## Docker

Build the image:

```bash
docker build -t researchiq .
```

Run it:

```bash
docker run -p 8000:8000 -p 8501:8501 --env-file .env researchiq
```

## Project Structure

```text
project/
├── app.py
├── backend/
│   ├── main.py
│   ├── routes/
│   ├── schemas/
│   └── services/
├── src/
│   ├── agents/
│   ├── graph/
│   ├── state/
│   ├── tools/
│   ├── models/
│   ├── prompts/
│   ├── evaluation/
│   └── config/
├── tests/
├── requirements.txt
├── .env.example
├── Dockerfile
├── run.sh
└── README.md
```

## Example

```text
Compare EV adoption growth in India and China since 2020
and summarize the main policy drivers in each country.
```

## Limitations

The evaluator uses simple heuristic scores and is not a validated benchmark.

The research data is stored in memory, so it is mainly suitable for local or single-instance deployment.

The web reader may not work correctly with websites that require JavaScript to display their content.
