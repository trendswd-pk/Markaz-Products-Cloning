import streamlit as st

from demo_mode.local_storage import render_local_storage_bridge


def render_demo_banner():
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, rgba(34,197,94,0.18), rgba(59,130,246,0.18));
            border: 1px solid rgba(34,197,94,0.35);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
        ">
            <strong>Demo Mode</strong> — localStorage + local JSON storage.
            Supabase and API routes are disabled. Shopify actions are simulated.
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_local_storage_bridge()
