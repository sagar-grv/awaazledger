"""Evidence schemas."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvidenceCreate(BaseModel):
    dispute_id: int
    evidence_type: str
    file_path: Optional[str] = None
    ocr_extracted_text: Optional[str] = None
    audio_transcript: Optional[str] = None
    metadata_json: Optional[str] = None


class EvidenceResponse(EvidenceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
