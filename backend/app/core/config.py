from functools import lru_cache
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    jwt_secret: str = Field(default="change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=480, alias="JWT_EXPIRE_MINUTES")

    database_url: str = Field(
        default="postgresql+psycopg://examgrader:examgrader@db:5432/examgrader",
        alias="DATABASE_URL",
    )

    # Origines autorisées (CORS), séparées par des virgules.
    cors_origins: str = Field(default="http://localhost:5173", alias="CORS_ORIGINS")

    @field_validator("database_url")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        """Render/Heroku fournissent `postgres://` ou `postgresql://`.

        SQLAlchemy + psycopg v3 attend `postgresql+psycopg://`. On normalise
        sans toucher aux URLs déjà préfixées (`...+psycopg`) ni à SQLite.
        """
        if v.startswith("postgresql+"):
            return v
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        return v

    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_max_tokens: int = Field(default=4096, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.0, alias="OPENAI_TEMPERATURE")

    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_local_root: str = Field(default="/data/uploads", alias="STORAGE_LOCAL_ROOT")

    poppler_path: str = Field(default="", alias="POPPLER_PATH")
    pdf_render_dpi: int = Field(default=300, alias="PDF_RENDER_DPI")
    confidence_review_threshold: float = Field(
        default=0.80, alias="CONFIDENCE_REVIEW_THRESHOLD"
    )
    max_upload_mb: int = Field(default=50, alias="MAX_UPLOAD_MB")

    bootstrap_admin_email: str = Field(
        default="admin@local", alias="BOOTSTRAP_ADMIN_EMAIL"
    )
    # Si défini, l'admin initial utilise ce mot de passe (sinon généré aléatoirement).
    bootstrap_admin_password: str = Field(default="", alias="BOOTSTRAP_ADMIN_PASSWORD")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
