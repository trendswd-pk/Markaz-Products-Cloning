import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ['MARKAZ_DEMO_MODE'] = '1'

from demo_mode.bootstrap import activate_demo_mode

activate_demo_mode()

from auth import init_auth_session, is_authenticated, render_login_page
from demo_mode.demo_ui import render_demo_banner

init_auth_session()

if not is_authenticated():
    render_login_page()
    st.stop()

render_demo_banner()

from app import main

main()
