import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
import speech_recognition as sr
import av
import queue
import threading
import numpy as np

# Audio frame queue
audio_queue = queue.Queue()

# Handler untuk menangkap audio frame
class AudioProcessor:
    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        audio = frame.to_ndarray()
        audio_queue.put(audio)
        return frame

# Fungsi untuk mengubah audio ke teks
def transcribe_audio():
    recognizer = sr.Recognizer()
    while True:
        audio_data = []
        try:
            for _ in range(10):  # ambil beberapa frame dulu
                audio_frame = audio_queue.get(timeout=3)
                audio_data.extend(audio_frame.flatten())

            audio_np = np.array(audio_data).astype(np.int16)

            audio_obj = sr.AudioData(audio_np.tobytes(), sample_rate=frame.sample_rate, sample_width=2)
            text = recognizer.recognize_google(audio_obj, language="id-ID")  # ubah ke 'en-US' untuk bahasa Inggris
            st.session_state["transcript"] = text
        except Exception as e:
            pass  # bisa tambahkan logging kalau mau

# Judul aplikasi
st.title("🎤 Ucapan ke Teks di Streamlit")

# Mulai webrtc
webrtc_ctx = webrtc_streamer(
    key="speech-to-text",
    mode=WebRtcMode.SENDONLY,
    rtc_configuration=RTCConfiguration(
        rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    ),
    media_stream_constraints={"audio": True, "video": False},
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"video": False, "audio": True},
)

# Inisialisasi session state
if "transcript" not in st.session_state:
    st.session_state["transcript"] = ""

# Jalankan thread untuk transkripsi
if webrtc_ctx.state.playing:
    threading.Thread(target=transcribe_audio, daemon=True).start()

# Tampilkan teks hasil ucapan
st.markdown("### 📝 Transkrip:")
st.write(st.session_state["transcript"])
