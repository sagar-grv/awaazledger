"""Core application settings using Pydantic Settings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BACKEND_DIR, "awaazledger.db").replace("\\", "/")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AwaazLedger"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    SECRET_KEY: str = "dev_secret_key_hackathon_only"

    # AI & Service integrations
    SARVAM_API_KEY: Optional[str] = None
    ENABLE_SARVAM_REAL: bool = False
    SARVAM_STT_ENDPOINT: Optional[str] = None
    SARVAM_TTS_ENDPOINT: Optional[str] = None

    ENABLE_OCR_REAL: bool = False

    ENABLE_EVOLUTION_LIVE: bool = False
    EVOLUTION_API_KEY: Optional[str] = None
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_INSTANCE_NAME: str = "paytm-awaazledger"

    # Risk & Policy Engine thresholds
    AUTO_CREDIT_CEILING: float = 2000.0
    MIN_TRUST_SCORE: int = 85
    MAX_FRAUD_SCORE: int = 30
    DUPLICATE_WINDOW_SECONDS: int = 120
    RBI_DELAY_PER_DAY_PENALTY: float = 100.0

    # Mini features & Hackathon toggles
    ENABLE_SWARM_SHIELD: bool = True
    SWARM_SHIELD_WINDOW_MINUTES: int = 5
    SWARM_SHIELD_THRESHOLD: int = 3
    ENABLE_MERCHANT_RECOVERY: bool = True
    DEMO_MODE: bool = True


settings = Settings()
