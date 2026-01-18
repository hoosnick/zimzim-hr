import asyncio
from datetime import datetime, timedelta

from apps.hik.client import HikClient
from apps.hik.models.person import Person
from apps.hik.utils import format_iso_datetime, image_to_base64
from tests.config import TOKEN_DATA


async def main():
    async with HikClient(token_data=TOKEN_DATA.model_dump()) as client:

        # Get person groups first
        groups = await client.get_person_groups()
        if not groups:
            print("No person groups found. Please create a group first.")
            return

        group_id = groups[0].group_id
        print(f"Using group: {groups[0].group_name} (ID: {group_id})")

        # Create new person
        new_person = Person(
            group_id=group_id,
            person_code="EMP001",
            first_name="Ana",
            last_name="De Armas",
            gender=0,  # Female
            phone="1234567890",
            email="ana.dearmas@example.com",
            description="Test employee",
            start_date=format_iso_datetime(datetime.now()),
            end_date=format_iso_datetime(datetime.now() + timedelta(days=365)),
        )

        print("\n--- Adding Person ---")
        person_id = await client.add_person(new_person)
        print(f"✓ Person added with ID: {person_id}")

        # Manually set person_id for testing if needed
        # person_id = "656867083971611648"

        # Update person's PIN code
        print("\n--- Updating PIN Code ---")
        await client.update_person_pincode(person_id, "1234")
        print("✓ PIN code updated")

        # Update person's face photo
        print("\n--- Updating Face Photo ---")
        with open("ana.jpeg", "rb") as image_file:
            photo_base64 = image_to_base64(image_file.read())

        # # Update the photo - remove data URL prefix if present
        # if photo_base64.startswith("data:"):
        #     photo_base64 = photo_base64.split(",")[1]

        try:
            await client.update_person_photo(person_id, photo_base64)
            print("✓ Face photo updated")
        except Exception as e:
            print(f"✗ Failed to update face photo: {e}")

        # Search for the person
        print("\n--- Searching for Person ---")
        persons = await client.get_persons(name_filter="Ana")
        for person in persons:
            if person.person_id == person_id:
                print(f"✓ Found: {person.first_name} {person.last_name}")
                break

        # Delete person (optional - uncomment to delete)
        # print("\n--- Deleting Person ---")
        # await client.delete_person(person_id)
        # print("✓ Person deleted")


if __name__ == "__main__":
    asyncio.run(main())
