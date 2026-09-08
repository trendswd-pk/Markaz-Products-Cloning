"""Compatibility entry: Streamlit Main file `demo_mode/app.py` → real app in `demo-mode/`."""

import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st

os.environ['MARKAZ_DEMO_MODE'] = '1'

_DEMO_DIR = Path(__file__).resolve().parent.parent / 'demo-mode'
_FAVICON = _DEMO_DIR / 'public' / 'favicon.png'
_PAGE_ICON = str(_FAVICON) if _FAVICON.exists() else '🛍️'

st.set_page_config(
    page_title='Markaz to Shopify — Demo Mode',
    page_icon=_PAGE_ICON,
    layout='wide',
)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_reg_spec = importlib.util.spec_from_file_location(
    '_demo_mode_register_pkg',
    _DEMO_DIR / 'register_pkg.py',
)
_reg_mod = importlib.util.module_from_spec(_reg_spec)
assert _reg_spec.loader is not None
_reg_spec.loader.exec_module(_reg_mod)
_reg_mod.ensure_demo_mode_package()

from demo_mode.bootstrap import activate_demo_mode

activate_demo_mode()

from auth import init_auth_session, is_authenticated, render_login_page, render_logout_control
from demo_mode.demo_main import run
from demo_mode.demo_ui import render_demo_banner

init_auth_session()

if not is_authenticated():
    render_login_page()
    st.stop()

render_demo_banner()
render_logout_control()
run()
