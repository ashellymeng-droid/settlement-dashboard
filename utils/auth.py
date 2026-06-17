"""Shared authentication check for all pages"""
import streamlit as st


def check_auth():
    """Ensure user is authenticated before showing page content"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        st.warning("🔐 请先在主页输入密码")
        st.stop()
