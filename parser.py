"""LLM team: replace this mock parser with Gemini integration."""
import re

def parse_request(message: str) -> dict:
    budget = re.search(r'(?:\$|under\s+)(\d+(?:\.\d+)?)', message, re.I)
    people = re.search(r'(\d+)\s+(?:people|guests|students)', message, re.I)
    return {"budget": float(budget.group(1)) if budget else 50.0,
            "people": int(people.group(1)) if people else 10,
            "categories": ["snacks", "drinks"] if "drink" in message.lower() else ["snacks"],
            "priority": "variety"}
