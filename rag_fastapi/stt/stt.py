from fastapi import APIRouter, WebSocket
import whisper  # openai-whisper


router = APIRouter(tags=["Speach-To-Text"])

@router.websocket("/transcribe")
async def transcribe():
    pass