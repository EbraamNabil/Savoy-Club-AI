import os
from pathlib import Path

from dotenv import load_dotenv


# Define the root directory of the project
PROJECT_ROOT = Path(__file__).resolve().parent

# Load environment variables from the project's .env file
load_dotenv(PROJECT_ROOT / ".env")

# Define the LLM provider and model settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-flash-latest")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Define the policy data directory
POLICY_DIR = PROJECT_ROOT / "data" / "policies"

# Define the transactions data path for future Staff Mode
TRANSACTIONS_PATH = PROJECT_ROOT / "data" / "transactions.csv"

# Define the persistent vector store directory
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
