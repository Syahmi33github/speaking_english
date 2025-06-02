import streamlit as st
import speech_recognition as sr
from openai import OpenAI
from gtts import gTTS
from moviepy import AudioFileClip, concatenate_audioclips
import os
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
import re

from streamlit_webrtc import webrtc_streamer, WebRtcMode, ClientSettings
import tempfile
import wave

import base64

# === Konfigurasi halaman ===
st.set_page_config(page_title="Asisten Belajar Inggris", layout="centered")

# === CSS untuk tampilan seperti aplikasi mobile ===
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1E1E2F; /* Latar belakang abu-abu gelap */
    }
    .stButton > button {
        width: 100%;
        padding: 0.75em;
        font-size: 16px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .avatar {
        display: block;
        margin-left: auto;
        margin-right: auto;
        width: 150px;
        margin-bottom: 20px;
    }
    .hai-text {
        text-align: center;
        font-size: 30px !important;
        color:white;
    }
    .center-text {
        text-align: center;
        font-size: 20px !important;
        color:white;
    }
    .bottom-nav {
        position: fixed;
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 20px;
        width: 50%;
        justify-content: center;
    }
    .nav-btn {
        padding: 10px 20px;
        background-color: white;
        border-radius: 15px;
        color: black;
        text-decoration: none;
        text-align: center;
        width: 20%; /* atur panjang kotak */
    }
    .chat-history {
        position: fixed;
        top: 100px;
        right: 100px;
        background-color: #2E2E3E;
        padding: 15px;
        border-radius: 15px;
        max-height: 400px;
        overflow-y: auto;
        width: 300px;
        z-index: 9999;
    }
    .chat-history h3 {
        margin-top: 0;
        color: white;
    }
    .chat-history span {
        display: block;
        margin-bottom: 10px;
        color: white;
    }
    .white-text {
        color: white;
        margin: 0px;
        padding: 0px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# ================== Konfigurasi API Key OpenAI ==================
client = OpenAI(
    api_key=st.secrets["API_KEY"],  # Simpan API key DeepSeek di secrets Streamlit
    base_url="https://api.deepseek.com"
)


# # ================== Fungsi Speech-to-Text ==================
# def speech_to_text():
#     recognizer = sr.Recognizer()
#     recognizer.pause_threshold = 1
#     with sr.Microphone() as source:
#         print("🎙️ Silakan bicara selama 5-10 detik...")
#         audio = recognizer.listen(source, phrase_time_limit=10)

#     # Coba Bahasa Indonesia
#     try:
#         text_id = recognizer.recognize_google(audio, language="id-ID")
#         print(f"📝 (ID) Teks terdeteksi: {text_id}")
#         return text_id
#     except sr.UnknownValueError:
#         pass  # Tidak dikenali, lanjut coba Inggris

#     # Coba Bahasa Inggris
#     try:
#         text_en = recognizer.recognize_google(audio, language="en-US")
#         print(f"📝 (EN) Detected text: {text_en}")
#         return text_en
#     except sr.UnknownValueError:
#         print("😕 Tidak bisa mengenali suara")
#     except sr.RequestError as e:
#         print(f"❌ Error dari Google: {e}")

#     return None


# ================== Fungsi Speech-to-Text Bahasa Inggris ==================
def speech_to_text_indonesia():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1
    with sr.Microphone() as source:
        print("🎙️ Please speak for 5-10 seconds...")
        audio = recognizer.listen(source, phrase_time_limit=10)

    try:
        text_id = recognizer.recognize_google(audio, language="id-ID")
        print(f"📝 (ID) Detected text: {text_id}")
        return text_id
    except sr.UnknownValueError:
        print("😕 Could not recognize speech in Indonesia")
    except sr.RequestError as e:
        print(f"❌ Error from Google: {e}")

    return None


# ================== Fungsi Speech-to-Text Bahasa Inggris ==================
def speech_to_text_english():
    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 1
    with sr.Microphone() as source:
        print("🎙️ Please speak for 5-10 seconds...")
        audio = recognizer.listen(source, phrase_time_limit=10)

    try:
        text_en = recognizer.recognize_google(audio, language="en-US")
        print(f"📝 (EN) Detected text: {text_en}")
        return text_en
    except sr.UnknownValueError:
        print("😕 Could not recognize speech in English")
    except sr.RequestError as e:
        print(f"❌ Error from Google: {e}")

    return None

def record_and_transcribe(language="en-US"):
    st.subheader("🎙️ Record your voice and transcribe to text")

    webrtc_ctx = webrtc_streamer(
        key="speech-to-text",
        mode=WebRtcMode.SENDONLY,
        client_settings=ClientSettings(
            media_stream_constraints={"video": False, "audio": True},
            rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
        ),
        audio_receiver_size=1024,
        async_processing=True,
    )

    audio_frames = []

    if webrtc_ctx.audio_receiver:
        st.info("🔴 Recording... Please speak.")
        
        while True:
            try:
                audio_frame = webrtc_ctx.audio_receiver.recv()
            except:
                break
            pcm_data = audio_frame.to_ndarray().tobytes()
            audio_frames.append(pcm_data)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            wf = wave.open(f.name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)
            wf.writeframes(b''.join(audio_frames))
            wf.close()

            st.success("✅ Audio recorded!")

            recognizer = sr.Recognizer()
            with sr.AudioFile(f.name) as source:
                audio_data = recognizer.record(source)

                try:
                    result_text = recognizer.recognize_google(audio_data, language=language)
                    st.subheader("📝 Transcription Result:")
                    st.write(result_text)
                    return result_text
                except sr.UnknownValueError:
                    st.warning("😕 Speech not recognized.")
                except sr.RequestError:
                    st.error("❌ Could not connect to Google Speech API.")

    return None


def fix_the_sentence(user_input):
    # Panggil API dengan seluruh riwayat percakapan
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Please correct the user's sentence if there are any typos—words that are incorrect and unrelated to the sentence's meaning—and replace them with the correct ones based on the context. ONLY SHOW THE CORRECTED RESULT IF THERE ARE MISTAKES. If there are no mistakes, show the original sentence.",
            },
            {"role": "user", "content": user_input},
        ],
        max_tokens=200,
        temperature=0.7,
    )

    # Ambil response dari GPT
    ai_message = response.choices[0].message["content"].strip()
    return ai_message


# ================== Fungsi GPT (Text Generation) ==================
def generate_response(fix_user_input):
    # Tambahkan pesan baru ke dalam session_state.history
    st.session_state.history.append({"role": "user", "content": fix_user_input})

    # Tentukan prompt system berdasarkan level
    level = st.session_state.get(
        "mode_belajar", "ngobrol"
    )  # default ngobrol jika belum dipilih

    if level == "ngobrol":
        system_prompt = """You are my English conversation partner. Your only task is to have casual conversations with me in English, like a friendly chat.
                            ALWAYS REPLY IN ENGLISH.
                            Talk about anything — daily life, hobbies, news, or random fun topics.
                            If I respond in Indonesian, simply translate it into English and ask me to say it.
                            Do not correct my grammar or vocabulary, even if it’s wrong — just keep the conversation going naturally.
                            Use simple and clear English, like you’re talking to a complete beginner.
                            Your main goal is to make me feel comfortable and enjoy speaking English without fear."""

    elif level == "koreksi":
        system_prompt = """You are my English conversation partner. Your task is to casually chat with me in English like a kind and supportive friend.
                            ALWAYS REPLY IN ENGLISH.
                            Talk about any topic you like — hobbies, daily activities, travel, etc.
                            If I respond in Indonesian, give me the English translation and ask me to say it.
                            If I make a grammar or vocabulary mistake, gently correct me. Give the correct version and a short explanation.
                            If the mistake is small, you can just give the correction without asking me to repeat it.
                            If there is no mistake please continue
                            Use short, simple sentences and explain anything I might not understand.
                            Treat me as a beginner who is just starting to gain confidence in speaking English.
                            Your goal is to help me speak better and more confidently step by step.
"""

    try:
        # Panggil API dengan seluruh riwayat percakapan
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}]
            + st.session_state.history,
            max_tokens=200,
            temperature=0.7,
        )

        # Ambil response dari GPT
        ai_message = response.choices[0].message["content"].strip()

        # Tambahkan jawaban AI ke riwayat
        st.session_state.history.append({"role": "assistant", "content": ai_message})

        return ai_message
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat menghubungi OpenAI: {e}")
        return None


# ================== Fungsi GPT (Text Generation) ==================
def generate_response_bantuan(user_input):
    # Tambahkan pesan baru ke dalam session_state.history
    st.session_state.history.append({"role": "user", "content": user_input})

    system_prompt = """Kamu adalah Guru Bahasa Inggris saya, kamu pandai menjelaskan dalam bahasa Indonesia.
                    Lihat Pertanyaan terakhirnya. Bantu saya, bagaimana caranya menjawab pertanyaan ini.
                    Wajib gunakan penjelaskan dalam Bahasa Indonesia dan berikan contoh dalam Bahasa Inggris.
                    Gunakan kalimat yang sederhana, pendek, dan mudah dipahami."""

    try:
        # Panggil API dengan seluruh riwayat percakapan
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": f"{system_prompt}",
                }
            ]
            + st.session_state.history,
            max_tokens=200,
            temperature=0.7,
        )

        # Ambil response dari GPT
        ai_message = response.choices[0].message["content"].strip()

        # Tambahkan jawaban AI ke riwayat
        st.session_state.history.append(
            {
                "role": "assistant",
                "content": f"{ai_message}",
            }
        )

        return ai_message
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan saat menghubungi OpenAI: {e}")
        return None


import string

DetectorFactory.seed = 0


def potong_dan_deteksi(teks_panjang):
    # 1. Potong berdasarkan tanda baca
    potongan = re.split(r'[.!?\'"]+', teks_panjang)
    potongan_bersih = [bagian.strip() for bagian in potongan if bagian.strip()]

    hasil = []
    for bagian in potongan_bersih:
        try:
            lang = detect(bagian)
            lang = "id" if lang == "id" else "en"  # semua selain 'id' dianggap 'en'
        except LangDetectException:
            lang = "en"  # fallback jika error juga dianggap 'en'
        hasil.append((bagian, lang))

    return hasil


from datetime import datetime


def text_to_speech(text):
    try:
        # =================== Text-to-Speech ===================
        list_audio = []

        for i, (text, lang) in enumerate(text):
            audio_name = f"test_output_{lang}_{i}.mp3"
            tts = gTTS(text=text, lang=lang)
            tts.save(audio_name)
            list_audio.append(audio_name)

            print(f"Generated {lang}_{i} TTS: {text}")

        print(list_audio)

        print("TTS files have been saved.")
        # =================== Text-to-Speech ===================

        # =================== Menggabungkan file audio ===================
        # Baca dan gabungkan
        clips = [AudioFileClip(f) for f in list_audio]
        combined = concatenate_audioclips(clips)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_audio_name = f"combined_output_{timestamp}.mp3"
        # Simpan ke file baru
        combined.write_audiofile(full_audio_name)
        print("Audio gabungan telah disimpan sebagai 'combined_output.mp3'")
        # =================== Menggabungkan file audio ===================

        return full_audio_name

    except Exception as e:
        st.error(f"❌ Gagal mengubah teks menjadi audio: {e}")
        return None


# ================== Fungsi Text-to-Speech ==================
def text_to_speech_english(text):
    try:
        # Text-to-speech dengan parameter eksplorasi
        tts = gTTS(
            text=text,
            lang="en",
            tld="com",
            slow=False,
            lang_check=True,
        )

        print("===================SCSC===================")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_audio_name = f"combined_output_{timestamp}.mp3"
        tts.save(full_audio_name)

        return full_audio_name

    except Exception as e:
        st.error(f"❌ Gagal mengubah teks menjadi audio: {e}")
        return None


# Inisialisasi history jika belum ada
if "history" not in st.session_state:
    st.session_state.history = []

# ================== Inisialisasi Session State ==================
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "all_texts" not in st.session_state:
    st.session_state.all_texts = []

if "show_confirm_button" not in st.session_state:
    st.session_state.show_confirm_button = False

# ================== UI Streamlit ==================
# st.title("🗣️ Asisten Belajar Bahasa Inggris (Speech to GPT + TTS)")

st.markdown(
    "<p class='hai-text'>Hey Sam 👋</p>",
    unsafe_allow_html=True,
)

# Baca gambar dan encode ke base64
with open(
    "2b5aca69-2984-4cc2-a5e8-b497cd1526be-removebg-preview.png", "rb"
) as img_file:
    base64_image = base64.b64encode(img_file.read()).decode()

# HTML untuk menampilkan gambar dan memperbesarnya
st.markdown(
    f"""
    <div style="text-align:center">
        <img src="data:image/png;base64,{base64_image}" style="width:1500px; border-radius: 50%;" />
    </div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    "<p class='center-text'>Ada yang mau di obrolin?</p>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .play-button {
        background-color: #4CAF50;
        border: none;
        color: white;
        padding: 12px 28px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        border-radius: 8px;
        cursor: pointer;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 1 2 1

# 1 1 3 1 1 1
# with col1:
#     st.button("🧠 Talk to AI Coach", key="coach")

import streamlit.components.v1 as components
import base64
import time
import ast


# Baca file MP3 dan ubah jadi base64
def get_audio_base64(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# audio_base64 = get_audio_base64("welcome_speech.mp3")
# audio_html = f"""
#     <audio autoplay>
#         <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
#     </audio>
# """
# components.html(audio_html, height=0)

# === Tombol pilihan ===
_, col_halo, _ = st.columns([1, 2, 1])

# === Tombol pilihan ===
_, _, col_bicara, col_bantuan, _, _ = st.columns([1, 1, 3, 1, 1, 1])

with col_halo:
    # Inisialisasi session_state
    if "halo_clicked" not in st.session_state:
        st.session_state.halo_clicked = False

    # Jika belum diklik, tampilkan tombol "👋 Halo"
    if not st.session_state.halo_clicked:
        if st.button("👋 Halo", key="Halo"):
            st.session_state.halo_clicked = True  # Simpan bahwa tombol telah diklik
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "content": "Halo sam {Hai sam} adakah yang menarik hari ini {Is there anything interesting today?}",
                }
            )
            audio_base64 = get_audio_base64("welcome_speech.mp3")
            audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                </audio>
            """
            components.html(audio_html, height=0)
    else:
        with col_bicara:
            # Jika tombol sudah diklik, tampilkan tombol "🎤 Bicara"
            # ================== Tombol Toggle Rekam ==================
            label = "⏹️ Berhenti" if st.session_state.is_recording else "▶️ Mulai Rekam"
            if st.button(label):
                st.session_state.is_recording = not st.session_state.is_recording

                if st.session_state.is_recording:
                    st.session_state.all_texts = []  # Kosongkan teks sebelumnya
                    st.session_state.show_confirm_button = False
                    st.session_state.show_text = (
                        False  # Menambahkan flag untuk kontrol teks
                    )
                else:
                    st.session_state.show_confirm_button = (
                        True  # Tampilkan tombol konfirmasi saat berhenti
                    )

                st.rerun()

            mode_bahasa = st.radio(
                label="",
                options=[":blue[Indonesia]", ":blue[English]"],
                index=0,
                horizontal=True,
                label_visibility="collapsed",
            )

            # if st.session_state.mode_bahasa == ":blue[Indonesia]":
            #     print(f"IND")
            #     # text = speech_to_text_indonesia()
            # elif st.session_state.mode_bahasa == ":blue[English]":
            #     print(f"ENG")
            #     # text = speech_to_text_english()

            # Toggle button
            koreksi_mode = st.toggle(":blue[Koreksi]")

            # Tampilkan hasil toggle
            if koreksi_mode:
                st.session_state.mode_belajar = "koreksi"
            else:
                st.session_state.mode_belajar = "ngobrol"

            # ================== Tampilkan Semua Hasil ==================
            if st.session_state.all_texts and not st.session_state.show_text:
                full_text = " ".join(st.session_state.all_texts)
                st.success(full_text)
                fix_response = fix_the_sentence(full_text)
                st.success(f"🧠 Fix: {fix_response} ")

            # ================== Loop Perekaman ==================
            if st.session_state.is_recording:
                # with st.spinner("⏳ Merekam..."):
                    st.session_state.mode_bahasa = mode_bahasa

                    if st.session_state.mode_bahasa == ":blue[Indonesia]":
                        print(f"mode_bahasa = {mode_bahasa}")
                        text = record_and_transcribe("id-ID")
                    elif st.session_state.mode_bahasa == ":blue[English]":
                        print(f"mode_bahasa = {mode_bahasa}")
                        text = record_and_transcribe("en-US")
                    else:
                        print(f"ELSE")
                        text = speech_to_text_indonesia()

                    if text:
                        st.session_state.all_texts.append(text)
                    time.sleep(1)
                    st.rerun()

            # ================== Tampilkan Tombol Konfirmasi ==================
            if st.session_state.show_confirm_button:
                if st.button("✅ Konfirmasi Selesai"):
                    st.session_state.show_text = (
                        True  # Menandakan bahwa teks telah dikonfirmasi
                    )
                    st.session_state.show_confirm_button = (
                        False  # Menyembunyikan tombol konfirmasi
                    )
                    st.session_state.all_texts = []  # Kosongkan teks yang ditampilkan
                    if fix_response:
                        # Tahap 2: Generate Response
                        start_gen = time.time()
                        response = generate_response(fix_response)
                        end_gen = time.time()
                        st.info(
                            f"🧠 Generate Response: {end_gen - start_gen:.2f} detik"
                        )

                        if response:
                            # # Tahap 3: Klasifikasi Bahasa
                            # start_klas = time.time()
                            # pecahan_teks_dan_klasifikasi = potong_dan_deteksi(response)
                            # print(pecahan_teks_dan_klasifikasi)
                            # end_klas = time.time()
                            # st.info(
                            #     f"🗂️ Klasifikasi Bahasa: {end_klas - start_klas:.2f} detik"
                            # )

                            # Tahap 4: Text to Speech
                            start_tts = time.time()
                            audio_output_path = text_to_speech_english(response)
                            print(audio_output_path)
                            if "all_audio_outputs" not in st.session_state:
                                st.session_state["all_audio_outputs"] = []
                            st.session_state["all_audio_outputs"].append(
                                audio_output_path
                            )
                            st.session_state["audio_output_index"] = (
                                len(st.session_state["all_audio_outputs"]) - 1
                            )
                            end_tts = time.time()
                            st.info(
                                f"🔊 Text-to-Speech: {end_tts - start_tts:.2f} detik"
                            )

                            if audio_output_path:
                                st.session_state["audio_output_path"] = (
                                    audio_output_path
                                )
                                st.session_state["show_audio_button"] = True

        with col_bantuan:
            if st.button("Bantu", key="courses"):
                input_text = st.session_state.history[-1]["content"]
                print(f"S==V=================={type(input_text)}")

                print(f"S==S=================={input_text}")
                if input_text:
                    # Tahap 2: Generate Response
                    start_gen = time.time()
                    response = generate_response_bantuan(input_text)
                    end_gen = time.time()
                    st.info(f"🧠 Generate Response: {end_gen - start_gen:.2f} detik")

                    if response:
                        # Tahap 3: Klasifikasi Bahasa
                        start_klas = time.time()
                        pecahan_teks_dan_klasifikasi = potong_dan_deteksi(response)
                        print(pecahan_teks_dan_klasifikasi)
                        end_klas = time.time()
                        st.info(
                            f"🗂️ Klasifikasi Bahasa: {end_klas - start_klas:.2f} detik"
                        )

                        # Tahap 4: Text to Speech
                        start_tts = time.time()
                        audio_output_path = text_to_speech(pecahan_teks_dan_klasifikasi)
                        print(audio_output_path)
                        if "all_audio_outputs" not in st.session_state:
                            st.session_state["all_audio_outputs"] = []
                        st.session_state["all_audio_outputs"].append(audio_output_path)
                        st.session_state["audio_output_index"] = (
                            len(st.session_state["all_audio_outputs"]) - 1
                        )
                        end_tts = time.time()
                        st.info(f"🔊 Text-to-Speech: {end_tts - start_tts:.2f} detik")

                        if audio_output_path:
                            st.session_state["audio_output_path"] = audio_output_path
                            st.session_state["show_audio_button"] = True
                else:
                    print("input_text : None")

# === Tombol pilihan ===
_, colputar, _ = st.columns([1, 2, 1])

with colputar:
    if st.session_state.get("show_audio_button", False):
        # Fungsi untuk memutar audio berdasarkan indeks saat ini
        def play_audio():
            index = st.session_state.get("audio_output_index", 0)
            all_paths = st.session_state.get("all_audio_outputs", [])

            if 0 <= index < len(all_paths):
                audio_path = all_paths[index]
                with open(audio_path, "rb") as f:
                    audio_bytes = f.read()
                    b64 = base64.b64encode(audio_bytes).decode()
                    audio_html = f"""
                        <audio autoplay style="display:none">
                            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                        </audio>
                    """
                    st.markdown(audio_html, unsafe_allow_html=True)
            else:
                st.warning("🔇 Tidak ada audio untuk diputar.")

        # Tombol untuk memutar audio pertama kali
        if st.button("🔊 Putar Audio", key="play_audio"):
            play_audio()
            st.session_state["show_restart_button"] = (
                True  # Menampilkan tombol Putar Ulang Audio
            )

        # Tombol Putar Ulang Audio
        if st.session_state.get("show_restart_button", False):
            if st.button("🔄 Putar Ulang Audio", key="restart_audio"):
                play_audio()
                st.session_state["show_restart_button"] = False

# ================== Riwayat Percakapan ==================

if "history_offset" not in st.session_state:
    st.session_state.history_offset = 0

# Jumlah chat yang ditampilkan (1 user + 1 assistant = 2 item)
CHUNK_SIZE = 2

# Tombol navigasi
(
    _,
    col1,
    col2,
    col3,
    _,
) = st.columns([1, 1, 1, 1, 1])

st.markdown(
    "</br></br>",
    unsafe_allow_html=True,
)

with col1:
    st.markdown(
        "</br></br>" '<p class="white-text">Halaman Riwayat Percakapan: </p>',
        unsafe_allow_html=True,
    )
with col2:
    st.markdown("</br></br>", unsafe_allow_html=True)
    if st.button("⬅️ Before"):
        max_offset = len(st.session_state.history) - CHUNK_SIZE
        if st.session_state.history_offset < max_offset:
            st.session_state.history_offset += CHUNK_SIZE
            # Mundur audio jika bisa
            if st.session_state.audio_output_index > 0:
                st.session_state.audio_output_index -= 1

with col3:
    st.markdown("</br></br>", unsafe_allow_html=True)
    if st.button("➡️ After"):
        if st.session_state.history_offset >= CHUNK_SIZE:
            st.session_state.history_offset -= CHUNK_SIZE
            # Maju audio jika masih dalam range
            if st.session_state.audio_output_index + 1 < len(
                st.session_state.all_audio_outputs
            ):
                st.session_state.audio_output_index += 1

# Hitung batas indeks
start_idx = max(
    len(st.session_state.history) - st.session_state.history_offset - CHUNK_SIZE, 0
)
end_idx = len(st.session_state.history) - st.session_state.history_offset

# Ambil potongan chat
last_msgs = st.session_state.history[start_idx:end_idx]

# Tampilkan chat history
chat_history_html = """
<div class='chat-history'>
    <h3>📜 Riwayat Percakapan</h3>
"""
for msg in last_msgs:
    if msg["role"] == "user":
        chat_history_html += (
            f"<span><strong>🗣️ Anda:</strong> {msg['content']}</span><br>"
        )
    elif msg["role"] == "assistant":
        chat_history_html += (
            f"<span><strong>🤖 AI:</strong> {msg['content']}</span><br>"
        )

chat_history_html += "</div>"
st.markdown(chat_history_html, unsafe_allow_html=True)
# ================== Riwayat Percakapan ==================


# # === Navigasi bawah ===

# # Garis pemisah
# # st.markdown("---")

# # Tambahkan CSS untuk mengatur warna tulisan menjadi putih
# st.markdown(
#     """
#     <style>
#     .white-text {
#         color: white;
#         margin: 0px;
#         padding: 0px;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # Navigasi bawah
# col1, col2, col3 = st.columns(3)

# with col1:
#     if st.button("🏠 Beginner"):
#         st.session_state.level = "Beginner"  # atau logika lain untuk berpindah halaman
#         st.session_state.history = []  # Reset riwayat percakapan saat ganti level

# with col2:
#     if st.button("📘 Intermediate"):
#         st.session_state.level = "Intermediate"  # sesuaikan dengan kebutuhan
#         st.session_state.history = []  # Reset riwayat percakapan saat ganti level

# with col3:
#     if st.button("📘 Advanced"):
#         st.session_state.level = "Advanced"  # sesuaikan dengan kebutuhan
#         st.session_state.history = []  # Reset riwayat percakapan saat ganti level

# # Contoh logika halaman (jika kamu pakai satu file dan session_state)
# if "level" in st.session_state:
#     if st.session_state.level == "Beginner":
#         st.markdown(
#             '<p class="white-text">Kamu di halaman Beginner</p>', unsafe_allow_html=True
#         )
#     elif st.session_state.level == "Intermediate":
#         st.markdown(
#             '<p class="white-text">Kamu di halaman Intermediate</p>',
#             unsafe_allow_html=True,
#         )
#     elif st.session_state.level == "Advanced":
#         st.markdown(
#             '<p class="white-text">Kamu di halaman Advanced</p>', unsafe_allow_html=True
#         )
# else:
#     st.session_state.level = "Beginner"
#     st.markdown(
#         '<p class="white-text">Kamu di halaman Beginner</p>', unsafe_allow_html=True
#     )
