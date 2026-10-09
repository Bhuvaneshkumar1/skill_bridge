import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "SkillBridge AI"
    TAGLINE: str = "Turn Learning Into Opportunity (Multi-Model AI Agent Platform)"
    VERSION: str = "2.0.0"
    
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{ (BASE_DIR / 'skillbridge.db').as_posix() }")
    
    # NVIDIA NIM API Key
    NVIDIA_API_KEY: str = os.getenv(
        "NVIDIA_API_KEY",
        "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"
    )
    
    # YouTube Data API v3 Key (Optional)
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    
    # Demo Mode (Set to True for offline deterministic testing)
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "False").lower() in ("true", "1", "yes")

settings = Settings()
