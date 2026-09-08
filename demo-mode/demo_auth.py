import hmac

import streamlit as st

from demo_mode.demo_config import DEMO_USER_ALIASES, DEMO_USERS
from demo_mode.local_storage import seed_dummy_data_if_empty


def is_auth_configured():
    return True


def get_auth_credentials():
    primary = DEMO_USERS[0]
    return {
        'username': primary['username'],
        'password': primary['password'],
    }


def _normalize_username(username):
    cleaned = (username or '').strip()
    return DEMO_USER_ALIASES.get(cleaned, cleaned)


def verify_login(username, password):
    cleaned = _normalize_username(username)
    for user in DEMO_USERS:
        user_ok = hmac.compare_digest(cleaned, user['username'])
        pass_ok = hmac.compare_digest(password, user['password'])
        if user_ok and pass_ok:
            return True
    # Accept legacy `viewer` username
    if cleaned == 'viewer@demo.com':
        for user in DEMO_USERS:
            if user['username'] == 'viewer@demo.com' and hmac.compare_digest(password, user['password']):
                return True
    return False


def render_login_page():
    st.markdown(
        """
        <style>
        .login-wrap {
            max-width: 520px;
            margin: 2.5rem auto 0 auto;
            padding: 1.75rem 1.5rem 2rem 1.5rem;
            border: 1px solid rgba(250, 250, 250, 0.12);
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.03);
        }
        .demo-account-card {
            border: 1px solid rgba(34, 197, 94, 0.35);
            background: rgba(34, 197, 94, 0.08);
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.65rem;
        }
        .demo-account-card strong { display: block; margin-bottom: 0.2rem; }
        .demo-account-card code {
            font-size: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 1.35, 1])
    with center_col:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.title("Demo Login")
        st.caption("Markaz to Shopify Converter — Demo Mode")

        st.info(
            "This is a simulated environment. No live Markaz scrape, Supabase, or Shopify API calls are made. "
            "Each account has an isolated sandbox."
        )

        st.markdown("**Choose a demo account** (fills the form — then click Sign in):")
        for idx, user in enumerate(DEMO_USERS):
            st.markdown(
                f"""
                <div class="demo-account-card">
                <strong>{user['label']}</strong>
                <code>{user['username']}</code> / <code>{user['password']}</code><br>
                <span style="opacity:0.85;font-size:0.9rem;">{user.get('description', '')}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(
                f"Use {user['label']} account",
                key=f"demo_pick_{idx}",
                width='stretch',
            ):
                st.session_state['demo_login_username'] = user['username']
                st.session_state['demo_login_password'] = user['password']
                st.rerun()

        default_user = st.session_state.get('demo_login_username', DEMO_USERS[0]['username'])
        default_pass = st.session_state.get('demo_login_password', DEMO_USERS[0]['password'])

        with st.form('demo_login_form', clear_on_submit=False):
            username = st.text_input("Username", value=default_user, autocomplete="username")
            password = st.text_input(
                "Password",
                value=default_pass,
                type="password",
                autocomplete="current-password",
            )
            submitted = st.form_submit_button("Sign in to Demo", type="primary", width='stretch')

        if submitted:
            if not username or not password:
                st.error("Enter username and password.")
            elif verify_login(username, password):
                resolved = _normalize_username(username)
                st.session_state.authenticated = True
                st.session_state.auth_username = resolved
                seed_dummy_data_if_empty(resolved)
                from auth import persist_auth_token

                persist_auth_token(resolved)
                st.rerun()
            else:
                st.error("Invalid demo username or password.")

        st.markdown('</div>', unsafe_allow_html=True)
