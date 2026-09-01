"""Application configuration.

Every setting is read from an environment variable at import time. Copy
`.env.example` to `.env` for local development, or export the variables in your
shell. Docker Compose passes them in through `env_file`.
"""

import os


class Settings:
    """Runtime settings for the API."""

    def __init__(self) -> None:
        self.app_env = os.getenv("APP_ENV", "local")
        self.app_port = int(os.getenv("APP_PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "debug")

        self.postgres_host = os.getenv("POSTGRES_HOST", "localhost")
        self.postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.postgres_db = os.getenv("POSTGRES_DB", "paycore")
        self.postgres_user = os.getenv("POSTGRES_USER", "paycore")
        self.postgres_password = os.getenv("POSTGRES_PASSWORD", "changeme_local_only")

        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        self.risk_engine_threshold = int(os.getenv("RISK_ENGINE_THRESHOLD", "70"))
        self.risk_engine_timeout_ms = int(os.getenv("RISK_ENGINE_TIMEOUT_MS", "250"))
        self.rules_service_url = os.getenv("RULES_SERVICE_URL", "")

    @property
    def database_url(self) -> str:
        """SQLAlchemy connection string for the transactions database."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
