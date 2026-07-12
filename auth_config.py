import os
from pathlib import Path

_SECRETS_PATH = Path(__file__).resolve().parent / '.streamlit' / 'secrets.toml'


def _is_placeholder(value):
    placeholders = (
        'YOUR_',
        'your_',
        'change-me',
        'changeme',
        'PASTE_',
        'password_here',
    )
    lowered = (value or '').lower()
    return not lowered or any(token.lower() in lowered for token in placeholders)


def _load_from_secrets_file():
    if not _SECRETS_PATH.exists():
        return {}

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with _SECRETS_PATH.open('rb') as secrets_file:
        data = tomllib.load(secrets_file)

    return data.get('app_login', {})


def get_auth_credentials():
    """Load app login credentials from env vars, secrets.toml, or Streamlit secrets."""
    username = os.getenv('APP_USERNAME', '').strip()
    password = os.getenv('APP_PASSWORD', '').strip()
    if username and password:
        return {'username': username, 'password': password}

    file_section = _load_from_secrets_file()
    if file_section.get('username') and file_section.get('password'):
        return {
            'username': str(file_section['username']).strip(),
            'password': str(file_section['password']).strip(),
        }

    try:
        import streamlit as st

        if hasattr(st, 'secrets') and 'app_login' in st.secrets:
            section = st.secrets['app_login']
            username = str(section.get('username', '')).strip()
            password = str(section.get('password', '')).strip()
            if username and password:
                return {'username': username, 'password': password}
    except Exception:
        pass

    return {'username': '', 'password': ''}


def is_auth_configured():
    creds = get_auth_credentials()
    username = creds.get('username', '')
    password = creds.get('password', '')
    return bool(username and password and not _is_placeholder(username) and not _is_placeholder(password))
