"""Test the server and client together."""

from typing import Optional, Sequence
from uuid import uuid4

import asyncpg
from pydantic import BaseModel

from app.schema import Assistant, Thread
from tests.unit_tests.app.helpers import get_client


def _project(model: BaseModel, *, exclude_keys: Optional[Sequence[str]] = None) -> dict:
    """Return a dict with only the keys specified."""
    d = model.model_dump()
    _exclude = set(exclude_keys) if exclude_keys else set()
    return {k: v for k, v in d.items() if k not in _exclude}


async def test_list_and_create_assistants(pool: asyncpg.pool.Pool) -> None:
    """Test list and create assistants."""
    headers = {"Cookie": "opengpts_user_id=1"}
    aid = str(uuid4())

    async with pool.acquire() as conn:
        assert len(await conn.fetch("SELECT * FROM assistant;")) == 0

    async with get_client() as client:
        response = await client.get(
            "/assistants/",
            headers=headers,
        )
        assert response.status_code == 200

        assert response.json() == []

        # Create an assistant
        response = await client.put(
            f"/assistants/{aid}",
            json={"name": "bobby", "config": {}, "public": False},
            headers=headers,
        )
        assert response.status_code == 200
        assistant = Assistant.model_validate(response.json())
        assert _project(assistant, exclude_keys=["updated_at", "user_id"]) == {
            "assistant_id": aid,
            "config": {},
            "name": "bobby",
            "public": False,
        }
        async with pool.acquire() as conn:
            assert len(await conn.fetch("SELECT * FROM assistant;")) == 1

        response = await client.get("/assistants/", headers=headers)
        assistants = [Assistant.model_validate(d) for d in response.json()]
        assert [
            _project(d, exclude_keys=["updated_at", "user_id"]) for d in assistants
        ] == [
            {
                "assistant_id": aid,
                "config": {},
                "name": "bobby",
                "public": False,
            }
        ]

        response = await client.put(
            f"/assistants/{aid}",
            json={"name": "bobby", "config": {}, "public": False},
            headers=headers,
        )

        assistant = Assistant.model_validate(response.json())
        assert _project(assistant, exclude_keys=["updated_at", "user_id"]) == {
            "assistant_id": aid,
            "config": {},
            "name": "bobby",
            "public": False,
        }

        # Check not visible to other users
        headers = {"Cookie": "opengpts_user_id=2"}
        response = await client.get("/assistants/", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json() == []


async def test_threads(pool: asyncpg.pool.Pool) -> None:
    """Test put thread."""
    headers = {"Cookie": "opengpts_user_id=1"}
    aid = str(uuid4())
    tid = str(uuid4())

    async with get_client() as client:
        response = await client.put(
            f"/assistants/{aid}",
            json={
                "name": "assistant",
                "config": {"configurable": {"type": "chatbot"}},
                "public": False,
            },
            headers=headers,
        )

        response = await client.put(
            f"/threads/{tid}",
            json={"name": "bobby", "assistant_id": aid},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        _ = Thread.model_validate(response.json())

        response = await client.get(f"/threads/{tid}/state", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"values": None, "next": []}

        response = await client.get("/threads/", headers=headers)

        assert response.status_code == 200
        threads = [Thread.model_validate(d) for d in response.json()]
        assert [
            _project(d, exclude_keys=["updated_at", "user_id"]) for d in threads
        ] == [
            {
                "assistant_id": aid,
                "name": "bobby",
                "thread_id": tid,
                "metadata": {"assistant_type": "chatbot"},
            }
        ]

        response = await client.put(
            f"/threads/{tid}",
            headers={"Cookie": "opengpts_user_id=2"},
        )
        assert response.status_code == 422
