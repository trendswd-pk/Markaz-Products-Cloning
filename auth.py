import hashlib
import hmac
import time

import streamlit as st

from auth_config import get_auth_credentials, is_auth_configured

# Keep login for 14 days across browser refreshes (signed query-param token).
AUTH_TOKEN_TTL_SECONDS = 60 * 60 * 24 * 14
AUTH_QUERY_KEY = 'auth'


def init_auth_session():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'auth_username' not in st.session_state:
        st.session_state.auth_username = None

    # Restore login after page refresh / new Streamlit session.
    if not st.session_state.authenticated:
        restored_user = restore_auth_from_token()
        if restored_user:
            st.session_state.authenticated = True
            st.session_state.auth_username = restored_user


def is_authenticated():
    return bool(st.session_state.get('authenticated'))


def _token_secret():
    creds = get_auth_credentials()
    username = creds.get('username', '')
    password = creds.get('password', '')
    return f'{username}:{password}:markaz-auth-v1'.encode('utf-8')


def make_auth_token(username, ttl_seconds=AUTH_TOKEN_TTL_SECONDS):
    """Create signed auth token: username|expiry|signature."""
    username = (username or '').strip()
    exp = int(time.time()) + int(ttl_seconds)
    payload = f'{username}|{exp}'
    signature = hmac.new(_token_secret(), payload.encode('utf-8'), hashlib.sha256).hexdigest()[:32]
    return f'{payload}|{signature}'


def verify_auth_token(token):
    """Return username if token is valid and not expired, else None."""
    if not token or not isinstance(token, str):
        return None
    try:
        username, exp_s, signature = token.rsplit('|', 2)
        exp = int(exp_s)
        if exp < int(time.time()):
            return None
        payload = f'{username}|{exp}'
        expected = hmac.new(
            _token_secret(),
            payload.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()[:32]
        if not hmac.compare_digest(signature, expected):
            return None
        return username.strip() or None
    except Exception:
        return None


def persist_auth_token(username):
    token = make_auth_token(username)
    try:
        st.query_params[AUTH_QUERY_KEY] = token
    except Exception:
        pass
    st.session_state['_auth_token'] = token


def clear_auth_token():
    st.session_state.pop('_auth_token', None)
    try:
        if AUTH_QUERY_KEY in st.query_params:
            del st.query_params[AUTH_QUERY_KEY]
    except Exception:
        try:
            params = dict(st.query_params)
            params.pop(AUTH_QUERY_KEY, None)
            st.query_params.clear()
            st.query_params.update(params)
        except Exception:
            pass


def restore_auth_from_token():
    token = None
    try:
        token = st.query_params.get(AUTH_QUERY_KEY)
    except Exception:
        token = None
    if not token:
        token = st.session_state.get('_auth_token')
    return verify_auth_token(token)


def verify_login(username, password):
    creds = get_auth_credentials()
    expected_user = creds.get('username', '')
    expected_pass = creds.get('password', '')
    if not expected_user or not expected_pass:
        return False

    user_ok = hmac.compare_digest(username.strip(), expected_user)
    pass_ok = hmac.compare_digest(password, expected_pass)
    return user_ok and pass_ok


def logout():
    st.session_state.authenticated = False
    st.session_state.auth_username = None
    clear_auth_token()


def render_login_page():
    st.markdown(
        """
        <style>
        .login-wrap {
            max-width: 420px;
            margin: 4rem auto 0 auto;
            padding: 2rem;
            border: 1px solid rgba(250, 250, 250, 0.15);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.03);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    _, center_col, _ = st.columns([1, 1.2, 1])
    with center_col:
        st.markdown('<div class="login-wrap">', unsafe_allow_html=True)
        st.title("Login")
        st.caption("Markaz to Shopify Converter — authorized access only.")

        if not is_auth_configured():
            st.error(
                "Login is not configured. Add an `[app_login]` block to `.streamlit/secrets.toml`:\n\n"
                "```toml\n[app_login]\nusername = \"your_username\"\npassword = \"your_strong_password\"\n```"
            )
            st.markdown('</div>', unsafe_allow_html=True)
            return

        with st.form('login_form', clear_on_submit=False):
            username = st.text_input("Username", autocomplete="username")
            password = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in", type="primary", width='stretch')

        if submitted:
            if not username or not password:
                st.error("Enter username and password.")
            elif verify_login(username, password):
                st.session_state.authenticated = True
                st.session_state.auth_username = username.strip()
                persist_auth_token(username.strip())
                st.rerun()
            else:
                st.error("Invalid username or password.")

        st.markdown('</div>', unsafe_allow_html=True)


def render_logout_control():
    header_col, logout_col = st.columns([0.82, 0.18])
    with header_col:
        if st.session_state.get('auth_username'):
            st.caption(f"Signed in as **{st.session_state.auth_username}**")
    with logout_col:
        if st.button("Logout", key="logout_button", width='stretch'):
            logout()
            st.rerun()
