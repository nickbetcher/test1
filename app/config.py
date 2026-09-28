from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration, read from environment variables (prefix APP_)."""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore")

    # SQLite for local dev; Postgres in real environments, e.g.
    # postgresql+psycopg://user:pass@host:5432/registry
    database_url: str = "sqlite:///./registry.db"

    # Comma-separated "name:token" pairs for service accounts / AI agents.
    # In production these come from a secret manager, never from source control.
    api_tokens: str = ""

    # When deployed behind an SSO proxy (oauth2-proxy, IAP, etc.), the proxy
    # authenticates the user and forwards their identity in this header.
    trusted_user_header: str = "X-Forwarded-Email"

    # If true, requests without SSO identity or API token are rejected.
    # Leave false for local development only.
    require_auth: bool = False

    environment: str = "local"

    def token_map(self) -> dict[str, str]:
        """Return {token: principal_name}."""
        pairs: dict[str, str] = {}
        for item in filter(None, (p.strip() for p in self.api_tokens.split(","))):
            name, _, token = item.partition(":")
            if name and token:
                pairs[token] = f"service:{name}"
        return pairs


@lru_cache
def get_settings() -> Settings:
    return Settings()
