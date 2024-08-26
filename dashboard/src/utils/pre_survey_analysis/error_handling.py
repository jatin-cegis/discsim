import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API_BASE_URL = os.getenv("API_BASE_URL")

ERROR_HANDLING_ENDPOINT = f"{API_BASE_URL}/error-handling"

def check_errors(params):
    response = requests.post(ERROR_HANDLING_ENDPOINT, json={"params": params})
    if response.status_code == 200:
        result = response.json()
        return result["status"], result["message"]
    else:
        return 0, f"Error in error handling: {response.json()['detail']}"
