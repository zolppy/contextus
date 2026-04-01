from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    hf_token: SecretStr = SecretStr("")
    sentence_transformer: str = "sentence-transformers/all-mpnet-base-v2"
    groq_api_key: SecretStr = SecretStr("")
    foundation_model: str = "openai/gpt-oss-120b"
