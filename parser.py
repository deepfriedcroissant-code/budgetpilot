"""LLM team: replace this mock parser with Gemini integration."""
import re
import os
import json
from dotenv import load_dotenv
from google import genai


# def parse_request(message: str) -> dict:
#     budget = re.search(r'(?:\$|under\s+)(\d+(?:\.\d+)?)', message, re.I)
#     people = re.search(r'(\d+)\s+(?:people|guests|students)', message, re.I)
#     return {"budget": float(budget.group(1)) if budget else 50.0,
#             "people": int(people.group(1)) if people else 10,
#             "categories": ["snacks", "drinks"] if "drink" in message.lower() else ["snacks"],
#             "priority": "variety"}

load_dotenv()
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

DEFAULTS = {"budget": 50.0, "people": 10, "categories": ["snacks"], "priority": "variety"}

def parse_request(message: str) -> dict:
    try:
        response = client.models.generate_content(
              model="gemini-flash-latest",
              contents=(
                  "Extract shopping details from this request and return JSON with keys: "
                  "budget (number), people (integer), categories (list of strings), "
                  "priority (string). Use null for anything not mentioned.\n\n"
                  f"Request: {message}",
                  ),
              config={"response_mime_type": "application/json"},
              )
        data = json.loads(response.text)
    
    except Exception as e:
            print(f"Gemini failed, using defaults: {e}")
            return DEFAULTS.copy()
    
    return {
        "budget": data.get("budget") or DEFAULTS["budget"],
        "people": data.get("people") or DEFAULTS["people"],
        "categories": data.get("categories") or DEFAULTS["categories"],
        "priority": data.get("priority") or DEFAULTS["priority"],
    }


