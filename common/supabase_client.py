import streamlit as st
from supabase import create_client


@st.cache_resource
def get_supabase_client():
    """Create and cache a server-side Supabase client."""
    url = st.secrets["SUPABASE_URL"]
    secret_key = st.secrets["SUPABASE_SECRET_KEY"]

    return create_client(url, secret_key)


def test_database_connection():
    """Test access to the tickets table without exposing credentials."""
    client = get_supabase_client()
    return client.table("tickets").select("ticket_id").limit(1).execute()
