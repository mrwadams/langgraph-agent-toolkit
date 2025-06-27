#!/usr/bin/env python3
"""
Test script to debug Google Search functionality
"""
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

# Create Google GenAI client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def test_search_directly():
    """Test Google Search directly with the google-genai SDK"""
    try:
        query = "news Milton Keynes yesterday"
        search_prompt = f"Please search for information about: {query}. Provide a comprehensive summary of the most relevant and current information you find."
        
        print(f"Testing search for: {query}")
        print("Using google-genai SDK directly...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=search_prompt,
            config={'tools': [{'google_search': {}}]}
        )
        
        print("Response received:")
        print(response.text)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_without_search():
    """Test model without search for comparison"""
    try:
        query = "What is Milton Keynes?"
        
        print(f"\nTesting without search: {query}")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query
        )
        
        print("Response received:")
        print(response.text)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Google Search functionality")
    print("=" * 50)
    
    # Test API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ No GOOGLE_API_KEY found in environment")
        exit(1)
    else:
        print(f"✅ API key found: {api_key[:10]}...")
    
    # Test without search first
    print("\n1. Testing basic model functionality:")
    test_without_search()
    
    # Test with search
    print("\n2. Testing model with Google Search:")
    test_search_directly()