# webscrape/olx_ai.py
import os
import re
import openai
from openai import RateLimitError, OpenAIError

def initialize_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    # normalize any non-breaking hyphens and strip whitespace
    api_key = api_key.replace('‑', '-').strip()
    openai.api_key = api_key


def redact_phone(text: str) -> str:
    """
    Replace any phone-like sequences with "[hidden]".
    """
    return re.sub(r"(\+?\d[\d\s\-\(\)]{5,}\d)", "[hidden]", text)


def extract_landmark(text: str) -> str:
    """
    Ask the model to pull out a landmark/nearby reference from text.
    Falls back to empty string if any error (including rate limit).
    """
    try:
        initialize_openai()
        prompt = (
            "Extract the most specific landmark or nearby reference "
            "(e.g. metro station, park) from this ad text. "
            "If none, reply with an empty string.\n\n" + text
        )
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=30,
        )
        return resp.choices[0].message["content"].strip()
    except RateLimitError:
        print("OpenAI rate limit reached, skipping landmark extraction.")
        return ""
    except OpenAIError as e:
        print(f"OpenAI error in extract_landmark: {e}")
        return ""
    except Exception as e:
        print(f"General error in extract_landmark: {e}")
        return ""


def translate(text: str, target_lang: str = "Russian") -> str:
    """
    Translate text into the target language via OpenAI.
    Falls back to original text upon failure.
    """
    try:
        initialize_openai()
        prompt = (
            f"Translate the following text into {target_lang}, keeping all details but without any phone numbers:\n\n" + text
        )
        resp = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=800,
        )
        return resp.choices[0].message["content"].strip()
    except RateLimitError:
        print("OpenAI rate limit reached, skipping translation.")
        return text
    except OpenAIError as e:
        print(f"OpenAI error in translate: {e}")
        return text
    except Exception as e:
        print(f"General error in translate: {e}")
        return text
