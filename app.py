"""Visitor-facing demonstration, reading list, and project overview."""
from pathlib import Path
import streamlit as st
from context_safety.ui.review_app import VIEWS, render_shell


def main():
    st.set_page_config(page_title='Context-Aware AI Safety', layout='wide', initial_sidebar_state='collapsed')
    view=st.session_state.get('review_view','Demonstration')
    if view not in VIEWS:
        view='Demonstration'
    # No evaluator import, route, query parameter, or launch control in this entry point.
    styles=(Path(__file__).parent/'src/context_safety/ui/demo.css').read_text()
    st.html('<style>'+styles+'''
    [data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stToolbar"] { display:none !important; }
    .block-container { max-width:none !important; padding:0 !important; }
    [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] { gap:0 !important; }
    </style>''')
    render_shell(view)


if __name__=='__main__':
    main()
