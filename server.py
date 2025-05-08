# server.py

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from deepgram import Deepgram
import yt_dlp
import asyncio
import os
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS so your frontend (Next.js or otherwise) can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this to your Vercel domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Load Deepgram API Key from environment variable
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

# Transcription logic (reusable for both endpoints)
async def transcribe_audio(mp3_path):
    dg = Deepgram(DEEPGRAM_API_KEY)
    with open(mp3_path, "rb") as f:
        source = {"buffer": f, "mimetype": "audio/mp3"}
        response = await dg.transcription.prerecorded(source, {
            "punctuate": True,
            "smart_format": True
        })
    return response["results"]["channels"][0]["alternatives"][0]["transcript"]

# 🎤 1. Upload File Endpoint
@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    try:
        temp = NamedTemporaryFile(delete=False, suffix=".mp3")
        contents = await file.read()
        temp.write(contents)
        temp.close()
        transcript = await transcribe_audio(temp.name)
        return {"transcript": transcript}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# 🔗 2. Transcribe From URL Endpoint (e.g. YouTube)
@app.post("/transcribe/url")
async def transcribe_from_url(url: str = Form(...)):
    try:
        download_path = "/tmp/audio"
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": download_path + ".%(ext)s",
            "quiet": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        audio_path = download_path + ".mp3"
        transcript = await transcribe_audio(audio_path)
        return {"transcript": transcript}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
