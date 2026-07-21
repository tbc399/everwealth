import httpx
from fastapi import HTTPException

from everwealth.config import settings


def plaid_base_url() -> str:
    environment = settings.plaid_env.lower()
    if environment == "production":
        return "https://production.plaid.com"
    if environment == "development":
        return "https://development.plaid.com"
    return "https://sandbox.plaid.com"


async def plaid_post(path: str, payload: dict) -> dict:
    request_payload = {
        **payload,
        "client_id": settings.plaid_client_id,
        "secret": settings.plaid_secret,
    }
    async with httpx.AsyncClient(base_url=plaid_base_url(), timeout=30) as client:
        response = await client.post(path, json=request_payload)
    if response.is_error:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=502, detail=detail)
    return response.json()
