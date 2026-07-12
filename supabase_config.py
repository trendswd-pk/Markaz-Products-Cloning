import os
from pathlib import Path

_SECRETS_PATH = Path(__file__).resolve().parent / '.streamlit' / 'secrets.toml'


def _load_from_secrets_file():
    if not _SECRETS_PATH.exists():
        return None, None

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    with _SECRETS_PATH.open('rb') as secrets_file:
        data = tomllib.load(secrets_file)

    supabase = data.get('supabase', {})
    return supabase.get('url'), supabase.get('key')


def get_supabase_credentials():
    """Load Supabase URL and API key from env vars, secrets.toml, or Streamlit secrets."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if url and key:
        return url, key

    file_url, file_key = _load_from_secrets_file()
    if file_url and file_key:
        return file_url, file_key

    try:
        import streamlit as st

        if hasattr(st, 'secrets') and 'supabase' in st.secrets:
            section = st.secrets['supabase']
            url = section.get('url')
            key = section.get('key')
            if url and key:
                return url, key
    except Exception:
        pass

    return None, None


def is_supabase_configured():
    url, key = get_supabase_credentials()
    if not url or not key:
        return False

    placeholders = (
        'YOUR_PROJECT_ID',
        'YOUR_SUPABASE_SERVICE_ROLE_KEY',
        'YOUR_SUPABASE_SERVICE_ROLE_OR_ANON_KEY',
        'PASTE_',
    )
    combined = f'{url} {key}'
    return not any(token in combined for token in placeholders)
