from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.background import BackgroundTask
import numpy as np
from pathlib import Path
import tempfile
import os

router = APIRouter()

# Get voice service instance
def get_voice_service():
    from app.main import voice_service
    return voice_service

@router.post("/voice/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    voice_service = Depends(get_voice_service)
):
    """Transcribe uploaded audio file"""
    try:
        # Read audio file
        audio_data = await file.read()
        audio_np = np.frombuffer(audio_data, dtype=np.float32)
        
        # Transcribe
        text = voice_service.transcribe_audio(audio_np)
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/synthesize")
async def synthesize_speech(
    text: str,
    voice_service = Depends(get_voice_service)
):
    """Convert text to speech"""
    try:
        # Create temp file for audio
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = Path(tmp.name)
            
        # Generate speech
        voice_service.synthesize_speech(text, output_path)
        
        # Return audio file
        return FileResponse(
            path=output_path,
            media_type="audio/mpeg",
            filename="speech.mp3",
            background=BackgroundTask(lambda: os.unlink(output_path))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
