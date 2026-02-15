from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # MongoDB Configuration
    MONGO_URI: str = Field(..., validation_alias="MONGO_URI")
    DB_NAME: str = "resource_hub"
    
    # Security Configuration
    JWT_SECRET: str = Field(..., validation_alias="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    
    # Admin Credentials
    ADMIN_USER: str = Field(default="admin", validation_alias="ADMIN_USER")
    ADMIN_PASSWORD: str = Field(..., validation_alias="ADMIN_PASSWORD")
    
    # AI Configuration
    GEMINI_API_KEY: str = Field(..., validation_alias="GEMINI_API_KEY")

    # env_file_encoding is optional but good practice
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

# Global settings instance
settings = Settings()

