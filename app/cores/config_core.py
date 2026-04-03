from pydantic import SecretStr, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    hf_token: SecretStr = Field(
        default=SecretStr(""),
        description="Token de acesso ao Hub da Hugging Face",
        alias="HF_TOKEN",
    )
    sentence_transformer: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
        description="Modelo de embedding usado na Groq",
        alias="SENTENCE_TRANSFORMER",
    )
    groq_api_key: SecretStr = Field(
        default=SecretStr(""),
        description="Chave de acesso da Groq",
        alias="GROQ_API_KEY",
    )
    foundation_model: str = Field(
        default="llama3-70b-8192",
        description="Modelo de embedding usado na Groq",
        alias="FOUNDATION_MODEL",
    )

    # Garante que as variáveis de ambiente imprescindíveis estejam presentes
    @model_validator(mode="after")
    def check_tokens(self):
        if not self.hf_token.get_secret_value():
            raise ValueError("HF_TOKEN não definido no arquivo .env")
        if not self.groq_api_key.get_secret_value():
            raise ValueError("GROQ_API_KEY não definido no arquivo .env")
        return self
