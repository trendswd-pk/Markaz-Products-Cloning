import hmac
from copy import deepcopy

import streamlit as st

from demo_mode.demo_config import DEMO_USERS
from demo_mode.local_storage import seed_dummy_data_if_empty


def is_auth_configured():
    return True


def get_auth_credentials():
    primary = DEMO_USERS[0]
    return {
        'username': primary['username'],
        'password': primary['password'],
    }


def verify_login(username, password):
    for user in DEMO_USERS:
        user_ok = hmac.compare_digest(username.strip(), user['username'])
        pass_ok = hmac.compare_digest(password, user['password'])
        if user_ok and pass_ok:
            return True
    return False


def render_login_page():
    st.markdown(
        """
        <style>
        .login-wrap {
            max-width: 460px;
            margin: 3rem auto 0 auto;
            padding: 2rem;
            border: 1px solid rgba(250, 250, 250, 0.15);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.03);
        }
        .demo-creds {
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.35);
            border-radius: 8px;
            padding: 0.9rem 1rem;
            margin: 1rem 0 1.25rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 1.3, 1])
    with center_col:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.title("Demo Login")
        st.caption("Markaz to Shopify Converter — demo environment")

        st.markdown(
            """
            <div class="demo-creds">
            <strong>Demo accounts (use any one):</strong><br>
            • <code>demo</code> / <code>demo123</code> (Demo Admin)<br>
            • <code>viewer</code> / <code>view123</code> (Demo Viewer)
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Demo Mode uses per-user JSON files on the server. "
            "No Supabase, live Markaz scraping, or real Shopify."
        )

        with st.form('demo_login_form', clear_on_submit=False):
            username = st.text_input("Username", value='demo', autocomplete="username")
            password = st.text_input("Password", value='demo123', type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in to Demo", type="primary", width='stretch')

        if submitted:
            if not username or not password:
                st.error("Enter username and password.")
            elif verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_username = username.strip()
                seed_dummy_data_if_empty(username.strip())
                from auth import persist_auth_token

                persist_auth_token(username.strip())
                st.rerun()
            else:
                st.error("Invalid demo username or password.")

        st.markdown('</div>', unsafe_allow_html=True)
