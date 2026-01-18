import asyncio

from apps.hik.client import HikClient
from tests.config import HIK_APP_KEY, HIK_SECRET_KEY, TOKEN_DATA


async def main():
    async with HikClient(
        app_key=HIK_APP_KEY,
        secret_key=HIK_SECRET_KEY,
        token_data=TOKEN_DATA.model_dump(),
    ) as client:
        print(f"✓ Authenticated as user: {client.user_id}")
        print(f"✓ Token: {client._token}")
        print(f"✓ Token expires at: {client.token_expires_at}")

        print("--- Persons ---")
        persons = await client.get_persons(page_size=50)
        for person in persons:
            print(f"  • {person.first_name} {person.last_name} ({person.person_id})")


if __name__ == "__main__":
    asyncio.run(main())
