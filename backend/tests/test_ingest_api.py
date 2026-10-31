"""Unit tests for multimodal ingestion HTTP endpoint functions."""

import io
from fastapi import UploadFile
from app.api.ingest import (
    ingest_text,
    ingest_demo_text,
    ingest_image,
    ingest_voice,
    get_demo_users,
)
from app.schemas.ingest import IngestTextRequest, IngestDemoTextRequest


def test_api_ingest_text(db_session):
    payload = IngestTextRequest(
        user_id=1,
        message="Mera 450 rupaye kat gaya Kirana store pe. UTR 987654321012.",
        channel="SIMULATOR",
    )
    data = ingest_text(payload=payload, db=db_session)
    assert data["needs_more_info"] is False
    assert data["dispute_id"] is not None
    assert data["dispute_code"].startswith("DISP-")


def test_api_ingest_demo_text(db_session):
    payload = IngestDemoTextRequest(
        user_id=1,
        scenario="SCN-01",
    )
    data = ingest_demo_text(payload=payload, db=db_session)
    assert data["needs_more_info"] is False
    assert data["dispute_id"] is not None
    assert data["entities"].utr == "987654321012"


def test_api_ingest_image(db_session):
    upload_file = UploadFile(
        file=io.BytesIO(b"MOCK_JPEG_CONTENT"),
        filename="screenshot_scn01_valid.jpg",
    )
    res_data = ingest_image(
        file=upload_file,
        user_id=1,
        channel="SIMULATOR",
        db=db_session,
    )
    assert res_data["needs_more_info"] is False
    assert res_data["dispute_id"] is not None
    assert res_data["entities"].utr == "987654321012"


def test_api_ingest_voice(db_session):
    upload_file = UploadFile(
        file=io.BytesIO(b"MOCK_OGG_CONTENT"),
        filename="voice_hindi_scn01.ogg",
    )
    res_data = ingest_voice(
        file=upload_file,
        user_id=1,
        channel="SIMULATOR",
        db=db_session,
    )
    assert res_data["needs_more_info"] is False
    assert res_data["dispute_id"] is not None
    assert res_data["entities"].utr == "987654321012"


def test_api_get_demo_users():
    users = get_demo_users()
    assert len(users) >= 5
    assert users[0]["name"] == "Rohit Verma"
