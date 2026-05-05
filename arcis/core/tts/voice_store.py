"""
Voice Store — MongoDB-backed persistence layer for custom TTS voices.

Each voice document looks like:
{
    "voice_id": "my_custom_voice",
    "name": "My Custom Voice",
    "is_default": false,
    "created_at": <datetime>,
    "file_path": "<absolute path to .wav on disk>",
}
"""

import os
import shutil
from datetime import datetime
from typing import Optional, List

from arcis.config import Config
from arcis.database.mongo.connection import mongo, COLLECTIONS
from arcis.logger import LOGGER


# Directory on disk where uploaded WAV files are persisted.
VOICE_STORAGE_DIR = os.path.join(Config.WORK_DIR, "voice_uploads")
os.makedirs(VOICE_STORAGE_DIR, exist_ok=True)

# Collection name
VOICE_COLLECTION = "tts_voices"


async def save_voice_metadata(
    voice_id: str,
    name: str,
    file_path: str,
    is_default: bool = False,
) -> dict:
    """Insert or update a voice document in MongoDB."""
    doc = {
        "voice_id": voice_id,
        "name": name,
        "file_path": file_path,
        "is_default": is_default,
        "created_at": datetime.utcnow(),
    }
    await mongo.db[VOICE_COLLECTION].update_one(
        {"voice_id": voice_id},
        {"$set": doc},
        upsert=True,
    )
    LOGGER.info(f"Voice metadata saved: {voice_id}")
    return doc


async def get_all_voices() -> List[dict]:
    """Return all stored voice documents."""
    cursor = mongo.db[VOICE_COLLECTION].find({}, {"_id": 0})
    return await cursor.to_list(length=100)


async def get_voice(voice_id: str) -> Optional[dict]:
    """Return a single voice document or None."""
    return await mongo.db[VOICE_COLLECTION].find_one(
        {"voice_id": voice_id}, {"_id": 0}
    )


async def delete_voice_metadata(voice_id: str) -> bool:
    """Delete a voice document. Returns True if something was deleted."""
    result = await mongo.db[VOICE_COLLECTION].delete_one({"voice_id": voice_id})
    return result.deleted_count > 0


async def set_default_voice(voice_id: str, is_builtin: bool = False, name: str = "") -> bool:
    """
    Mark *voice_id* as the default voice and un-default everything else.
    If it's built-in, we upsert a metadata record just to track its default status.
    Returns False if a custom voice doesn't exist.
    """
    if not is_builtin:
        voice = await get_voice(voice_id)
        if not voice:
            return False

    # Clear existing default
    await mongo.db[VOICE_COLLECTION].update_many(
        {"is_default": True},
        {"$set": {"is_default": False}},
    )
    
    if is_builtin:
        await mongo.db[VOICE_COLLECTION].update_one(
            {"voice_id": voice_id},
            {"$set": {
                "voice_id": voice_id,
                "name": name,
                "is_default": True,
                "is_builtin": True,
            }},
            upsert=True
        )
    else:
        # Set new default for custom voice
        await mongo.db[VOICE_COLLECTION].update_one(
            {"voice_id": voice_id},
            {"$set": {"is_default": True}},
        )
        
    LOGGER.info(f"Default voice set to: {voice_id}")
    return True


async def get_default_voice() -> Optional[dict]:
    """Return the voice marked as default, or None."""
    return await mongo.db[VOICE_COLLECTION].find_one(
        {"is_default": True}, {"_id": 0}
    )


def save_wav_to_disk(voice_id: str, wav_bytes: bytes) -> str:
    """Persist WAV bytes to disk and return the absolute file path."""
    file_path = os.path.join(VOICE_STORAGE_DIR, f"{voice_id}.wav")
    with open(file_path, "wb") as f:
        f.write(wav_bytes)
    LOGGER.info(f"Voice WAV saved to disk: {file_path}")
    return file_path


def delete_wav_from_disk(voice_id: str) -> bool:
    """Remove WAV file from disk. Returns True if file existed."""
    file_path = os.path.join(VOICE_STORAGE_DIR, f"{voice_id}.wav")
    if os.path.exists(file_path):
        os.remove(file_path)
        LOGGER.info(f"Voice WAV deleted from disk: {file_path}")
        return True
    return False
