from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from pydantic import BaseModel

from arcis.core.tts.tts_manager import tts_manager
from arcis.core.tts.voice_store import (
    save_voice_metadata,
    get_all_voices,
    get_voice,
    delete_voice_metadata,
    set_default_voice,
    get_default_voice,
    save_wav_to_disk,
    delete_wav_from_disk,
)
from arcis.logger import LOGGER

voices_router = APIRouter(prefix="/voices", tags=["voices"])

class VoiceResponse(BaseModel):
    voice_id: str
    name: str
    is_default: bool
    created_at: float

@voices_router.get("", response_model=List[VoiceResponse])
async def list_voices():
    """List all available custom voices."""
    try:
        voices = await get_all_voices()
        result = []
        for v in voices:
            result.append({
                "voice_id": v["voice_id"],
                "name": v["name"],
                "is_default": v["is_default"],
                "created_at": v["created_at"].timestamp() if v.get("created_at") else 0
            })
        return result
    except Exception as e:
        LOGGER.error(f"Failed to list voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voices_router.post("")
async def upload_custom_voice(
    voice_id: str = Form(...),
    name: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a new custom voice WAV file."""
    if not file.filename.endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only .wav files are supported")
    
    try:
        content = await file.read()
        
        # 1. Save to disk
        file_path = save_wav_to_disk(voice_id, content)
        
        # 2. Extract and load into TTS Manager
        success = tts_manager.update_voice_state_from_bytes(voice_id, content)
        if not success:
            delete_wav_from_disk(voice_id)
            raise HTTPException(status_code=500, detail="Failed to parse voice state from audio")
            
        # 3. Save to database
        await save_voice_metadata(voice_id=voice_id, name=name, file_path=file_path)
        
        return {"status": "success", "message": f"Voice '{name}' uploaded successfully", "voice_id": voice_id}
    except Exception as e:
        LOGGER.error(f"Voice upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voices_router.delete("/{voice_id}")
async def delete_custom_voice(voice_id: str):
    """Delete a custom voice."""
    try:
        voice = await get_voice(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
            
        if voice.get("is_default"):
            raise HTTPException(status_code=400, detail="Cannot delete the default voice")

        # 1. Remove from database
        await delete_voice_metadata(voice_id)
        
        # 2. Remove from disk
        delete_wav_from_disk(voice_id)
        
        # 3. Remove from TTS Manager memory
        if voice_id in tts_manager.voice_states:
            del tts_manager.voice_states[voice_id]
            
        return {"status": "success", "message": f"Voice '{voice_id}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Voice deletion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@voices_router.put("/{voice_id}/default")
async def set_custom_voice_default(voice_id: str):
    """Set a custom voice as the default voice."""
    try:
        # Check if the voice exists in our DB
        voice = await get_voice(voice_id)
        if not voice:
            raise HTTPException(status_code=404, detail="Voice not found")
            
        # Update database
        await set_default_voice(voice_id)
        
        # Update TTS Manager memory
        if voice_id in tts_manager.voice_states:
            tts_manager.default_voice_state = tts_manager.voice_states[voice_id]
            tts_manager.voice_states["default"] = tts_manager.voice_states[voice_id]
        
        return {"status": "success", "message": f"Voice '{voice_id}' set as default"}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Setting default voice failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
