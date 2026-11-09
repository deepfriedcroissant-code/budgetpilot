"""Safely check local Gemini configuration and a minimal API request.

Run from the repository root: python scripts/check_gemini.py
Never print or commit API keys, .env files, or raw provider exception payloads.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from google import genai

load_dotenv(ROOT / ".env", override=False)

key = (os.getenv("GEMINI_API_KEY") or "").strip()
model = (os.getenv("GEMINI_MODEL") or "gemini-3.8-flash").strip()

print("GEMINI_API_KEY present:", bool(key))
print("GEMINI_MODEL:", model)

if not key:
    print("FAIL: Add a newly generated GEMINI_API_KEY to .env beside app.py.")
    raise SystemExit(1)

client = None
try:
    # Hold a strong reference for the entire request; constructing the client
    # inline can allow its transport to close before generate_content finishes.
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model=model,
        contents="Return the single word SUCCESS.",
        config={"max_output_tokens": 128, "thinking_config": {"thinking_level": "low"}}
        if model == "gemini-3.8-flash" else {"max_output_tokens": 128},
    )
    if response.text and "SUCCESS" in response.text.upper():
        print("PASS: Gemini API reachable and generating text.")
    else:
        print("WARN: Gemini API responded, but did not return the expected text.")
except Exception as exc:
    code = getattr(exc, "code", None)
    status = getattr(exc, "status", None)
    print("FAIL: Gemini API request failed.")
    print("Error class:", type(exc).__name__)
    print("HTTP code:", code if code is not None else "unavailable")
    print("Status:", status if status is not None else "unavailable")
    # Remove common credential patterns before showing the underlying error.
    details = str(exc).replace(key, "[REDACTED]")
    details = re.sub(r"(?i)(key=|api_key=|api[-_]key: ?|authorization: ?bearer )[\\w.\\-]+", r"\\1[REDACTED]", details)
    details = re.sub(r"AIza[0-9A-Za-z_-]{20,}", "[REDACTED]", details)
    details = re.sub(r"AQ\\.[A-Za-z0-9_-]{15,}", "[REDACTED]", details)
    print("Exception details (redacted):", details[:1000])
    print("Underlying cause type:", type(exc.__cause__).__name__ if exc.__cause__ else "None")
    print("Review output for secrets before sharing; do not share raw exceptions.")
    raise SystemExit(1)

finally:
    if client is not None:
        client.close()
