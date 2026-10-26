
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# LLM provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY:
    try:
        import streamlit as st
        GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
    except Exception:
        GROQ_API_KEY = ""

# Project data paths
POLICY_DIR = PROJECT_ROOT / "data" / "policies"
TRANSACTIONS_PATH = PROJECT_ROOT / "data" / "transactions.csv"
VECTOR_STORE_DIR = PROJECT_ROOT / "data" / "vector_store"
