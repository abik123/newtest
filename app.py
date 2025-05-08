# app.py
import streamlit as st
import os
from deepgram import Deepgram
import yt_dlp
import asyncio
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

st.set_page_config(page_title="Abik's Transcriber", layout="centered")

load_dotenv()
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

st.title("🎙️ Abik's Transcriber – Upload or Paste URL")

tab1, tab2 = st.tabs(["Upload a File", "Paste a Link"])

uploaded_file = None
video_url = ""

with tab1:
    uploaded_file = st.file_uploader("Upload MP3, MP4, or WAV", type=["mp3", "mp4", "wav"])

with tab2:
    video_url = st.text_input("Paste a video/audio link", placeholder="e.g. https://youtube.com/watch?...")

# Download and convert URL audio
def download_audio(url):
    output_path = "/tmp/audio"
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path + '.%(ext)s',
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        'ffmpeg_location': '/opt/homebrew/bin'  # UPDATE THIS TO YOUR ffmpeg PATH
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_path + ".mp3"

# Transcribe Function (Deepgram)
async def transcribe(mp3_file_path):
    dg = Deepgram(DEEPGRAM_API_KEY)
    with open(mp3_file_path, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/mp3"}
        response = await dg.transcription.prerecorded(source, {
            "punctuate": True,
            "smart_format": True
        })
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]

# Interface
if st.button("🧠 Transcribe"):
    audio_path = None

    if uploaded_file:
        with st.spinner("Saving uploaded file..."):
            temp = NamedTemporaryFile(delete=False, suffix=".mp3")
            temp.write(uploaded_file.read())
            temp.close()
            audio_path = temp.name

    elif video_url.strip():
        with st.spinner("Downloading audio from link..."):
            try:
                audio_path = download_audio(video_url)
            except Exception as e:
                st.error(f"❌ Error: {e}")

    if audio_path:
        st.audio(audio_path)
        with st.spinner("Transcribing using Deepgram..."):
            try:
                transcript = asyncio.run(transcribe(audio_path))
                st.success("✅ Transcription complete!")
                st.text_area("📝 Transcript", transcript, height=300)
                st.download_button("📥 Download Text File", data=transcript, file_name="transcript.txt")
            except Exception as e:
                st.error(f"⚠️ Transcription Error: {e}")
