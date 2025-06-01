# main.py
import streamlit as st

# === CSS untuk tampilan seperti aplikasi mobile ===
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E1E2F; /* Latar belakang abu-abu gelap */
        color: white;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("Halo! 👋")
st.write("Selamat datang di aplikasi Streamlit sederhana.")
