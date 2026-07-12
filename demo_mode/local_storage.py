import json
import re
from copy import deepcopy
from pathlib import Path

import streamlit as st

from demo_mode.demo_config import STORAGE_NAMESPACE, TRACKED_PRODUCTS_KEY
from demo_mode.dummy_data import DUMMY_TRACKED_PRODUCTS

DATA_ROOT = Path(__file__).resolve().parent / 'data' / 'users'


def browser_storage_key(username):
    return f'{STORAGE_NAMESPACE}_{_safe_username(username)}'


def _safe_username(username):
    return re.sub(r'[^a-zA-Z0-9_-]', '_', (username or 'guest').strip()) or 'guest'


class PerUserStorage:
    """Server-side per-user JSON store for demo mode."""

    def __init__(self, username):
        self.username = username
        self.user_dir = DATA_ROOT / _safe_username(username)
        self.user_dir.mkdir(parents=True, exist_ok=True)
        self.store_path = self.user_dir / 'local_storage.json'
        self._data = self._load_file()

    def _load_file(self):
        if not self.store_path.exists():
            return {}
        try:
            return json.loads(self.store_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            return {}

    def _save_file(self):
        self.store_path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding='utf-8',
        )

    def get(self, key, default=None):
        return deepcopy(self._data.get(key, default))

    def set(self, key, value):
        self._data[key] = deepcopy(value)
        self._save_file()

    def delete(self, key):
        if key in self._data:
            del self._data[key]
            self._save_file()

    def export_payload(self):
        return deepcopy(self._data)


def get_current_storage():
    username = st.session_state.get('auth_username') or 'guest'
    cache_user = st.session_state.get('_demo_storage_user')
    if 'demo_storage' not in st.session_state or cache_user != username:
        st.session_state.demo_storage = PerUserStorage(username)
        st.session_state._demo_storage_user = username
    return st.session_state.demo_storage


def seed_dummy_data_if_empty(username):
    storage = PerUserStorage(username)
    if storage.get(TRACKED_PRODUCTS_KEY):
        return

    storage.set(TRACKED_PRODUCTS_KEY, deepcopy(DUMMY_TRACKED_PRODUCTS))
    st.session_state.demo_storage = storage
    st.session_state._demo_storage_user = username


def render_local_storage_bridge():
    """No-op: browser localStorage sync disabled (components.html segfaults on some Linux setups).

    Demo data persists via server-side JSON in demo_mode/data/users/.
    """
    return
