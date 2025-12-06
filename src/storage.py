import threading

import streamlit as st


# Define the structure of your ephemeral DB
@st.cache_resource
def get_storage():
    return {"polls": {}, "lock": threading.Lock()}


# Helper to access state easily
def get_polls():
    return get_storage()["polls"]


def get_lock():
    return get_storage()["lock"]
