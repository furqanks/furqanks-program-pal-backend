# This service will handle the logic for the advanced natural language search.
# It will interact with external APIs (Perplexity, US Scorecard, etc.)
# and potentially trigger web scraping tasks.

import httpx
import os
import json # Added for parsing JSON responses
from dotenv import load_dotenv
from typing import List, Optional # Added List, Optional
from urllib.parse import urlencode # Added for query string encoding

from ..schemas import SearchQuery, SearchResultItem, SearchResponse

load_dotenv()

# API Keys and Endpoints
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "dummy_perplexity_key")
SCOREBOARD_API_KEY = os.getenv("SCOREBOARD_API_KEY", "dummy_scoreboard_key") # Get a real key from https://collegescorecard.ed.gov/data/api-documentation/

SCOREBOARD_API_BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools.json"
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions" # Check actual endpoint

# Define fields to request from College Scorecard API
# See: https://collegescorecard.ed.gov/data/documentation/
SCOREBOARD_FIELDS = [
    "id",
    "school.name",
    "school.city",
    "school.state",
    "school.school_url",
    "latest.student.size", # Example field
    "latest.cost.tuition.in_state", # Example field
    "latest.cost.tuition.out_of_state", # Example field
    # Add fields relevant to programs if available (often school-level)
    # e.g., fields related to specific CIP codes if user query allows mapping
]

async def _call_scoreboard_api(query_text: str) -> List[SearchResultItem]:
    """Queries the US College Scorecard API."""
    results = []
    # Basic keyword extraction (can be improved with NLU)
    keywords = query_text.split()
    search_term = " ".join(k for k in keywords if k.lower() not in ["us", "usa", "in", "the", "a", "for"])

    params = {
        "api_key": SCOREBOARD_API_KEY,
        "school.name": search_term, # Simple name search for now
        "fields": ",".join(SCOREBOARD_FIELDS),
        "per_page": 5 # Limit results for now
    }
    async with httpx.AsyncClient() as client:
        try:
            print(f"Querying Scoreboard: {SCOREBOARD_API_BASE_URL}?{urlencode(params)}")
            response = await client.get(SCOREBOARD_API_BASE_URL, params=params, timeout=20.0)
            response.raise_for_status() # Raise exception for bad status codes
            data = response.json()

            for school in data.get("results", []):
                results.append(
                    SearchResultItem(
                        program_name=f"Programs at {school.get('school.name', 'N/A')}", # Scorecard is school-level
                        university_name=school.get("school.name", "N/A"),
                        country="USA",
                        url=school.get("school.school_url", None),
                        description=f"Located in {school.get(	'school.city', 'N/A')}, {school.get(	'school.state', 'N/A')}. Student size: {school.get(	'latest.student.size', 'N/A')}",
                        tuition_fees=f"In-state: ${school.get(	'latest.cost.tuition.in_state', 'N/A')}, Out-of-state: ${school.get(	'latest.cost.tuition.out_of_state', 'N/A')}",
                        source="US College Scorecard"
                    )
                )
        except httpx.HTTPStatusError as e:
            print(f"Scoreboard API request failed: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Scoreboard API request failed: {e}")
        except json.JSONDecodeError as e:
            print(f"Failed to decode Scoreboard API response: {e}")
        except Exception as e:
            print(f"An unexpected error occurred querying Scoreboard: {e}")
    return results

async def _call_perplexity_api(query_text: str) -> List[SearchResultItem]:
    """Queries the Perplexity API for broader search, especially non-US."""
    results = []
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    # Construct a prompt asking for structured information
    # This needs refinement based on Perplexity's capabilities for structured output
    prompt = f"""
    Find university programs based on the following query: "{query_text}"
    Please provide results in a JSON list format, where each item has the following keys (use null if info not found):
    - program_name (string)
    - university_name (string)
    - country (string)
    - url (string, direct link to program if possible)
    - description (string, brief summary)
    - tuition_fees (string, e.g., "$10,000/year")
    - intake_dates (list of strings, e.g., ["September 2025", "January 2026"])
    - visa_support (boolean, if known)

    Example JSON item:
    {{
        "program_name": "MSc Artificial Intelligence",
        "university_name": "University of Example",
        "country": "UK",
        "url": "http://example.ac.uk/ai",
        "description": "Focuses on machine learning and robotics.",
        "tuition_fees": "£20,000/year",
        "intake_dates": ["September 2025"],
        "visa_support": true
    }}

    Provide only the JSON list in your response.
    """

    payload = {
        "model": "llama-3-sonar-large-32k-online", # Or another suitable model
        "messages": [
            {"role": "system", "content": "You are an AI assistant helping find university programs. Respond ONLY with the requested JSON list."}, # System prompt to guide output format
            {"role": "user", "content": prompt}
        ]
        # Add parameters for temperature, max_tokens etc. if needed
    }

    async with httpx.AsyncClient() as client:
        try:
            print(f"Querying Perplexity API...")
            response = await client.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60.0)
            response.raise_for_status()
            api_response = response.json()

            # Extract the content from the response
            content = api_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"Perplexity Raw Response Content: {content}")

            # Attempt to parse the JSON content
            try:
                # Clean potential markdown/fencing
                if content.startswith("```json"): content = content[7:]
                if content.endswith("```"): content = content[:-3]
                content = content.strip()

                parsed_json = json.loads(content)
                if isinstance(parsed_json, list):
                    for item in parsed_json:
                        # Validate and map to SearchResultItem
                        if isinstance(item, dict) and "program_name" in item and "university_name" in item:
                            results.append(
                                SearchResultItem(
                                    program_name=item.get("program_name"),
                                    university_name=item.get("university_name"),
                                    country=item.get("country"),
                                    url=item.get("url"),
                                    description=item.get("description"),
                                    tuition_fees=item.get("tuition_fees"),
                                    intake_dates=item.get("intake_dates"),
                                    visa_support=item.get("visa_support"),
                                    source="Perplexity AI"
                                )
                            )
            except json.JSONDecodeError as json_err:
                print(f"Failed to parse JSON from Perplexity response: {json_err}. Content was: {content}")
                # Optionally, add a generic result indicating failure to parse
                results.append(SearchResultItem(program_name="Error Parsing Perplexity Response", university_name="N/A", source="Perplexity AI", description=content[:500])) # Include partial raw content

        except httpx.HTTPStatusError as e:
            print(f"Perplexity API request failed: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Perplexity API request failed: {e}")
        except Exception as e:
            print(f"An unexpected error occurred querying Perplexity: {e}")

    return results

async def perform_advanced_search(query: SearchQuery) -> SearchResponse:
    """Processes the natural language query and returns structured search results."""
    print(f"Received search query: {query.query}")

    # Query Data Sources concurrently (using asyncio.gather could be an option)
    us_results = await _call_scoreboard_api(query.query)
    perplexity_results = await _call_perplexity_api(query.query)

    # Combine and Format Results (simple concatenation for now)
    combined_results = us_results + perplexity_results

    # Generate Summary (Optional: Use LLM)
    summary = f"Found {len(combined_results)} potential results for '{query.query}'. {len(us_results)} from US Scorecard, {len(perplexity_results)} from Perplexity AI. (Summary needs improvement)"

    return SearchResponse(results=combined_results, summary=summary)

# Placeholder for scraping logic - to be implemented if needed
# async def scrape_university_site(url: str) -> Optional[SearchResultItem]:
#     pass

