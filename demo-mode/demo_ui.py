import streamlit as st

from demo_mode.local_storage import reset_demo_data


def render_demo_banner():
    st.markdown(
        """
        <div style="
            background: linear-gradient(90deg, rgba(34,197,94,0.18), rgba(59,130,246,0.18));
            border: 1px solid rgba(34,197,94,0.35);
            border-radius: 10px;
            padding: 0.75rem 1rem;
            margin-bottom: 0.75rem;
        ">
            <strong>Demo Mode</strong> — simulated Markaz scrape and Shopify actions.
            Data is stored per signed-in user on this server only (no production backends).
        </div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([4, 1])
    with cols[1]:
        if st.button("Reset demo data", key="demo_reset_sandbox", help="Restore seeded products for this account"):
            reset_demo_data()
            st.success("Demo sandbox reset.")
            st.rerun()
