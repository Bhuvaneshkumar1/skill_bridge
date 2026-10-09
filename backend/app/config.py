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

    def __init__(self):
        self.PROJECT_NAME = "SkillBridge AI"
        self.TAGLINE = "Turn Learning Into Opportunity (Multi-Model AI Agent Platform)"
        self.VERSION = "2.0.0"
        
        self.HOST: str = os.getenv("HOST", "127.0.0.1")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
        
        _raw_db_url: str = os.getenv("DATABASE_URL", "").strip()
        self.DATABASE_URL: str = _raw_db_url if _raw_db_url else f"sqlite:///{ (BASE_DIR / 'skillbridge.db').as_posix() }"
        
        # NVIDIA NIM API Key
        self.NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "").strip()
        
        # YouTube Data API v3 Key (Optional)
        self.YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "").strip()
        
        # Demo Mode (Set to True for offline deterministic testing)
        self.DEMO_MODE: bool = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "yes")

        # Code Sandbox Security Settings
        self.SECURE_SANDBOX_ENABLED: bool = os.getenv("SECURE_SANDBOX_ENABLED", "False").lower() in ("true", "1", "yes")
        self.ALLOW_UNSECURE_SUBPROCESS_SANDBOX: bool = os.getenv("ALLOW_UNSECURE_SUBPROCESS_SANDBOX", "True").lower() in ("true", "1", "yes")
        self.MAX_SOURCE_LENGTH: int = int(os.getenv("MAX_SOURCE_LENGTH", "65536"))
        self.MAX_STDIN_LENGTH: int = int(os.getenv("MAX_STDIN_LENGTH", "16384"))
        self.MAX_OUTPUT_BYTES: int = int(os.getenv("MAX_OUTPUT_BYTES", "65536"))
        self.MAX_CONCURRENT_SANDBOX_JOBS: int = int(os.getenv("MAX_CONCURRENT_SANDBOX_JOBS", "5"))

settings = Settings()

