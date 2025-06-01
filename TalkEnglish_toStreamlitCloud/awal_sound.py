from moviepy import AudioFileClip, concatenate_audioclips
from gtts import gTTS
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

        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_audio_name = f"welcome_speech.mp3"
        # Simpan ke file baru
        combined.write_audiofile(full_audio_name)
        print("Audio gabungan telah disimpan sebagai 'welcome_speech.mp3'")
        # =================== Menggabungkan file audio ===================

        return full_audio_name
    except Exception as e:
        print({e})
        return None


text = [
    ("Halo sam", "id"),
    ("Hai sam", "en"),
    ("adakah yang menarik hari ini?", "id"),
    ("Is there anything interesting today?", "en"),
]

text_to_speech(text)
