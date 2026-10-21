"""Server-only configuration; no hardcoded contact value or persistent reveal state."""
import os
import re
import streamlit as st


def contact_email():
    # An explicitly empty environment value also disables the local secret for testing.
    value = os.environ.get('CONTACT_EMAIL')
    if value is None:
        try:
            value = st.secrets.get('contact', {}).get('email', '')
        except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
            value = ''
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9.!#$%&\x27*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', value):
        return None
    return value


def contact_payload(revealed=False):
    value = contact_email()
    result = {'available': bool(value)}
    if revealed and value:
        result['email'] = value
    return result
