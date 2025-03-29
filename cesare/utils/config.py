import os
from dotenv import load_dotenv

def load_api_key():
    load_dotenv('secrets.env')
    api_key = os.getenv('TOGETHER_API_KEY')
    if not api_key:
        raise ValueError("TOGETHER_API_KEY not found in secrets.env")
    return api_key
