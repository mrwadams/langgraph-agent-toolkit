import os
from langchain_core.tools import tool
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Create Google GenAI client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

@tool
def google_search(query: str) -> str:
    """
    Search the web using Google Search.
    Use this tool to find current information, news, or answers to topical questions.
    """
    try:
        # Create a search-focused prompt
        search_prompt = f"Please search for information about: {query}. Provide a comprehensive summary of the most relevant and current information you find."
        
        # Use Google GenAI client with search tool
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=search_prompt,
            config={'tools': [{'google_search': {}}]}
        )
        
        return response.text
    except Exception as e:
        return f"Search failed: {str(e)}"