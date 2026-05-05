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

BUILTIN_VOICES = [
    {"voice_id": "alba", "name": "Alba (English)"},
    {"voice_id": "giovanni", "name": "Giovanni (Italian)"},
    {"voice_id": "lola", "name": "Lola (Spanish)"},
    {"voice_id": "juergen", "name": "Juergen (German)"},
    {"voice_id": "rafael", "name": "Rafael (Portuguese)"},
    {"voice_id": "estelle", "name": "Estelle (French)"},
    {"voice_id": "anna", "name": "Anna (English)"},
    {"voice_id": "azelma", "name": "Azelma (English)"},
    {"voice_id": "bill_boerst", "name": "Bill Boerst (English)"},
    {"voice_id": "caro_davy", "name": "Caro Davy (English)"},
    {"voice_id": "charles", "name": "Charles (English)"},
    {"voice_id": "cosette", "name": "Cosette (English)"},
    {"voice_id": "eponine", "name": "Eponine (English)"},
    {"voice_id": "eve", "name": "Eve (English)"},
    {"voice_id": "fantine", "name": "Fantine (English)"},
    {"voice_id": "george", "name": "George (English)"},
    {"voice_id": "jane", "name": "Jane (English)"},
    {"voice_id": "jean", "name": "Jean (English)"},
    {"voice_id": "javert", "name": "Javert (English)"},
    {"voice_id": "marius", "name": "Marius (English)"},
    {"voice_id": "mary", "name": "Mary (English)"},
    {"voice_id": "michael", "name": "Michael (English)"},
    {"voice_id": "paul", "name": "Paul (English)"},
    {"voice_id": "peter_yearsley", "name": "Peter Yearsley (English)"},
    {"voice_id": "stuart_bell", "name": "Stuart Bell (English)"},
    {"voice_id": "vera", "name": "Vera (English)"},
]

class VoiceResponse(BaseModel):
    voice_id: str
    name: str
    is_default: bool
    created_at: float
    is_builtin: bool = False

@voices_router.get("", response_model=List[VoiceResponse])
async def list_voices():
    """List all available custom voices."""
    try:
        voices = await get_all_voices()
        
        db_default_voice_id = None
        result = []
        for v in voices:
            if v.get("is_builtin"):
                if v.get("is_default"):
                    db_default_voice_id = v["voice_id"]
                continue # we will add built-ins later
            
            if v.get("is_default"):
                db_default_voice_id = v["voice_id"]
                
            result.append({
                "voice_id": v["voice_id"],
                "name": v["name"],
                "is_default": v.get("is_default", False),
                "created_at": v["created_at"].timestamp() if v.get("created_at") else 0,
                "is_builtin": False
            })
            
        # Add built-in voices
        for builtin in BUILTIN_VOICES:
            is_default = (builtin["voice_id"] == db_default_voice_id)
            if db_default_voice_id is None and builtin["voice_id"] == "alba":
                is_default = True # default fallback
                
            result.append({
                "voice_id": builtin["voice_id"],
                "name": builtin["name"],
                "is_default": is_default,
                "created_at": 0,
                "is_builtin": True
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
    """Set a custom or built-in voice as the default voice."""
    try:
        # Check if the voice exists in our DB or is built-in
        is_builtin = any(v["voice_id"] == voice_id for v in BUILTIN_VOICES)
        builtin_name = next((v["name"] for v in BUILTIN_VOICES if v["voice_id"] == voice_id), "")
        
        if not is_builtin:
            voice = await get_voice(voice_id)
            if not voice:
                raise HTTPException(status_code=404, detail="Voice not found")
            
        # Update database
        await set_default_voice(voice_id, is_builtin=is_builtin, name=builtin_name)
        
        # Update TTS Manager memory
        if is_builtin:
            try:
                state = tts_manager.tts_model.get_state_for_audio_prompt(voice_id)
                tts_manager.default_voice_state = state
                tts_manager.voice_states["default"] = state
            except Exception as e:
                LOGGER.error(f"Failed to load builtin voice {voice_id} directly: {e}")
                raise HTTPException(status_code=500, detail="Failed to load built-in voice")
        else:
            if voice_id in tts_manager.voice_states:
                tts_manager.default_voice_state = tts_manager.voice_states[voice_id]
                tts_manager.voice_states["default"] = tts_manager.voice_states[voice_id]
        
        return {"status": "success", "message": f"Voice '{voice_id}' set as default"}
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Setting default voice failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
