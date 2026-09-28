import secrets

from fastapi import Depends, HTTPException, Request, status

from app.config import Settings, get_settings


def get_principal(request: Request, settings: Settings = Depends(get_settings)) -> str:
    """Identify the caller.

    Two supported paths, mirroring a typical corporate setup:
      * Humans: an SSO reverse proxy in front of the app authenticates them and
        sets a trusted identity header (the app is never exposed without it).
      * Agents / services: send ``Authorization: Bearer <token>``.
    """
    auth = request.headers.get("Authorization", "")
    if auth.lower().startswith("bearer "):
        presented = auth[7:].strip()
        for token, principal in settings.token_map().items():
            if secrets.compare_digest(presented, token):
                return principal
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API token")

    user = request.headers.get(settings.trusted_user_header)
    if user:
        return f"user:{user}"

    if settings.require_auth:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    return "anonymous"
