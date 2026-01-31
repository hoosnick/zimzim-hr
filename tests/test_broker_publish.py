import asyncio
import json
import uuid

from loguru import logger

from apps.hr.tables import Message
from core.db import database_connection
from core.mq.broker import broker

payload = {
    "batch_id": "7a75e3ea63415feb39c9a3d6e766fa5cc188663fc0ac8df54a35c92e4ca2b595946580da1c096dc96dc5cedc4612a48c",
    "remaining_number": 0,
    "event": [
        {
            "basicInfo": {
                "occurrenceTime": "2026-01-15T16:09:26+05:00",
                "systemId": "3ccc543923d34a77974c77818b031226",
                "msgType": "Msg110003",
                "device": {
                    "id": "5500192ba0524282b820fa00da52eeb5",
                    "name": "ZimZim1",
                    "category": "accessControllerDevice",
                    "deviceSerial": "FR3774911",
                },
            },
            "data": {
                "openDoorInfo": {
                    "event": {
                        "basicInfo": {
                            "systemId": "3ccc543923d34a77974c77818b031226",
                            "eventType": 110003,
                            "elementId": "dad01520315c4416b82fc30c3925c6c1",
                            "elementType": 1002,
                            "elementName": "ZimZim1",
                            "areaId": "783596c137a64d789a26daf4aadf484e",
                            "areaName": "ZimIT",
                            "occurTime": "2026-01-15T16:09:26+05:00",
                            "deviceId": "5500192ba0524282b820fa00da52eeb5",
                            "category": "2002",
                            "deviceSerial": "FR3774911",
                            "deviceName": "ZimZim1",
                            "channelNo": 1,
                            "currentEvent": 1,
                            "serialNo": 11973,
                            "cardReaderId": "fcf9aecac80b49e2813e2008e8a5592b",
                        },
                        "intelliInfo": {
                            "cardNumber": "0000095180",
                            "personId": "655816174650934274",
                            "firstName": "Husniddin",
                            "lastName": "Murodov Zafarjon o'g'li",
                            "fullPath": "ZimDevs",
                            "phoneNum": "",
                            "personPicUrl": "https://hpc-sgp-prod-s3-person-data-storage.oss-ap-southeast-1.aliyuncs.com/GDPR001/3ccc543923d34a77974c77818b031226/655816174650934274/0/picture.data?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=LTAI5tQckMpJxMb4qoHXJySP%2F20260115%2Foss-ap-southeast-1%2Fs3%2Faws4_request&X-Amz-Date=20260115T110550Z&X-Amz-Expires=3600&X-Amz-SignedHeaders=host&X-Amz-Signature=69f04a50251e367da7bbf9b86c3e12cd15c0859c0305a580b939c6efdd376c89",
                            "groupId": "666676336647342080",
                            "attendanceStatus": 1,
                            "authResult": 1,
                        },
                    }
                }
            },
        }
    ],
}


async def mock_event() -> None:
    message_id = uuid.uuid4()

    message = Message(
        id=message_id,
        payload=payload,
        status=Message.Status.pending,
    )
    await message.save()
    logger.info(f"Saved message {message_id} to database")

    await broker.publish(
        message=json.dumps(payload).encode(),
        stream="events",
        headers={"event_id": str(message_id)},
    )
    logger.info(f"Published message {message_id} to Redis stream")


async def main() -> None:
    await database_connection()
    await broker.connect()
    await mock_event()
    await broker.stop()
    await database_connection(close=True)


if __name__ == "__main__":
    asyncio.run(main())
