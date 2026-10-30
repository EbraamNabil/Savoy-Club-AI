
import hashlib
import hmac
import streamlit as st

ITERATIONS = 310000

STAFF_USERS = {
    "veronia.atef@savoy-sharm.com",
    "nader.hanna@savoy-sharm.com",
    "ebraam.nabil@savoy-sharm.com",
}


def verify_password(password, stored_value):
    try:
        salt, expected_hash = stored_value.split(":")
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            ITERATIONS
        ).hex()

        return hmac.compare_digest(actual_hash, expected_hash)
    except Exception:
        return False


def render_staff_login():
    if st.session_state.get("staff_authenticated", False):
        return True

    st.title("SAVOY Club | Staff Login")
    st.caption("Authorized staff members only")

    if st.session_state.get("login_locked", False):
        st.error("Too many failed attempts. Please restart your session.")
        return False

    with st.form("staff_login_form"):
        email = st.text_input("Work Email").strip().lower()
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)

    if submitted:
        attempts = st.session_state.get("login_attempts", 0)

        if email not in STAFF_USERS:
            valid = False
        else:
            users = st.secrets.get("staff_users", {})
            stored_value = users.get(email, "")
            valid = bool(stored_value) and verify_password(
                password, stored_value
            )

        if valid:
            st.session_state.staff_authenticated = True
            st.session_state.staff_email = email
            st.session_state.login_attempts = 0
            st.rerun()
        else:
            attempts += 1
            st.session_state.login_attempts = attempts
            if attempts >= 5:
                st.session_state.login_locked = True
                st.error("Too many failed attempts. Please restart your session.")
            else:
                st.error("Invalid email or password.")

    return False


def staff_logout():
    st.session_state.staff_authenticated = False
    st.session_state.pop("staff_email", None)
    st.session_state.login_attempts = 0
    st.session_state.login_locked = False
    st.session_state.page = "home"
    st.rerun()
