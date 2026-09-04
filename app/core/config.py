from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Video Viewer API"
    API_V1_STR: str = "/api/v1"
    
    # Upstash Redis URL (TLS enabled with rediss://)
    REDIS_URL: str = "rediss://default:Aaa2AAIgcDFjM2YyNmNlNzYzYWE0NWZjODllMDY4ZTkxYmU4ZDhkOA@valid-boar-42678.upstash.io:6379" 
    
    CACHE_TTL_SECONDS: int = 7200  # 2 hours
    YOUTUBE_COOKIES_BASE64: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
