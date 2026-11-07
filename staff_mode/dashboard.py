import streamlit as st

from common.supabase_client import test_database_connection


def render_staff_dashboard():
    """Render the initial staff dashboard and database connection test."""

    st.title("SAVOY Club | Staff Mode")
    st.success(f"Signed in as {st.session_state.staff_email}")

    st.subheader("Database Connection")
    st.caption("Check whether the application can access the shared tickets database.")

    if st.button(
        "Test Supabase Connection",
        type="primary",
        key="test_supabase_connection",
    ):
        try:
            test_database_connection()
            st.success("Connection successful. The tickets table is accessible.")
        except Exception as error:
            print(f"Supabase connection test failed: {error!r}")
            st.error(
                "Connection failed. Please check the Supabase configuration "
                "in Streamlit Cloud Secrets."
            )
