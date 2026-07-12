import streamlit as st


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
            <strong>Demo Mode</strong> — per-user JSON storage on server.
            Supabase, live Markaz scraping, and real Shopify are disabled. Actions are simulated only.
        </div>
        """,
        unsafe_allow_html=True,
    )
