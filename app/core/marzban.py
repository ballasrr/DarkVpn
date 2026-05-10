from datetime import datetime, timedelta

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class MarzbanClient:
    def __init__(self):
        self.base_url = settings.MARZBAN_MASTER_URL
        self._token: str | None = None

    async def _get_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/admin/token",
                data={
                    "username": settings.MARZBAN_MASTER_USER,
                    "password": settings.MARZBAN_MASTER_PASS,
                },
            )
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
            return self._token

    async def _headers(self) -> dict:
        token = await self._get_token()
        return {"Authorization": f"Bearer {token}"}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def create_user(self, username: str, days: int, traffic_gb: int) -> dict:
        headers = await self._headers()
        expire_ts = int((datetime.now() + timedelta(days=days)).timestamp())
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/user",
                headers=headers,
                json={
                    "username": username,
                    "proxies": {"vless": {"flow": "xtls-rprx-vision"}},
                    "inbounds": {"vless": ["VLESS TCP REALITY"]},
                    "expire": expire_ts,
                    "data_limit": traffic_gb * 1024 ** 3,
                    "data_limit_reset_strategy": "week",
                    "status": "active",
                },
            )
            resp.raise_for_status()
            return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def get_user(self, username: str) -> dict:
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/user/{username}",
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_user_key(self, username: str) -> str:
        user = await self.get_user(username)
        links = user.get("links", [])
        if not links:
            raise ValueError(f"Нет ключей для пользователя {username}")
        return links[0]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def update_user(self, username: str, days: int | None = None, traffic_gb: int | None = None, status: str | None = None) -> dict:
        headers = await self._headers()
        payload = {}
        if days is not None:
            payload["expire"] = int((datetime.now() + timedelta(days=days)).timestamp())
        if traffic_gb is not None:
            payload["data_limit"] = traffic_gb * 1024 ** 3
        if status is not None:
            payload["status"] = status
        async with httpx.AsyncClient() as client:
            resp = await client.put(
                f"{self.base_url}/api/user/{username}",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def delete_user(self, username: str) -> None:
        headers = await self._headers()
        async with httpx.AsyncClient() as client:
            resp = await client.delete(
                f"{self.base_url}/api/user/{username}",
                headers=headers,
            )
            resp.raise_for_status()

    async def disable_user(self, username: str) -> dict:
        return await self.update_user(username, status="disabled")

    async def enable_user(self, username: str) -> dict:
        return await self.update_user(username, status="active")


marzban = MarzbanClient()