from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    GROQ_API_KEY: SecretStr | None = None
    GROQ_MODEL: str = Field(
        default="llama-3.3-70b-versatile",
        min_length=1,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()