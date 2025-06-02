import streamlit as st
from st_audiorec import st_audiorec
import speech_recognition as sr
import tempfile
import wave
import os

st.title("🎙️ Rekam & Transkripsi Audio")

# Komponen rekam suara
wav_audio_data = st_audiorec()

if wav_audio_data is not None:
    st.audio(wav_audio_data, format='audio/wav')
    
    # Simpan sementara ke file .wav
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
        tmp_file.write(wav_audio_data)
        tmp_filename = tmp_file.name

    # Proses transkripsi
    recognizer = sr.Recognizer()
    with sr.AudioFile(tmp_filename) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language="id-ID")
            st.markdown("### 📝 Transkrip:")
            st.success(text)
        except sr.UnknownValueError:
            st.error("Tidak dapat mengenali suara.")
        except sr.RequestError:
            st.error("Gagal menghubungi layanan pengenalan suara.")

    # Hapus file sementara
    os.remove(tmp_filename)
