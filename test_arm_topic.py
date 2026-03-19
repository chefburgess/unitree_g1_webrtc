"""
Topic discovery script — found rt/api/arm/request as correct arm topic on G1.
Tests multiple candidate topics and shows which ones respond.
"""

import asyncio
import json

from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
from unitree_webrtc_connect.constants import WebRTCConnectionMethod, DATA_CHANNEL_TYPE

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.123.161")
    await conn.connect()
    await asyncio.sleep(1)

    channel = conn.datachannel.channel
    ps = conn.datachannel.pub_sub

    @channel.on("message")
    async def on_all(message):
        try:
            if isinstance(message, str):
                parsed = json.loads(message)
                if parsed.get('type') in ('res', 'err'):
                    print(f"  << {parsed}")
        except Exception:
            pass

    topics = [
        "rt/api/arm/request",       # CORRECT — returns code 0 with action list
        "rt/api/loco/request",      # Returns 'Invalid Topic.xx' on G1
        "rt/api/arm_action/request", # Returns 'Invalid Topic.xx'
        "rt/api/g1/arm/request",    # Returns 'Invalid Topic.xx'
    ]

    for i, topic in enumerate(topics):
        print(f"\nTrying GetActionList (7107) on: {topic}")
        ps.publish_without_callback(
            topic=topic,
            data={"header": {"identity": {"id": i+1, "api_id": 7107}}, "parameter": ""},
            msg_type=DATA_CHANNEL_TYPE["REQUEST"]
        )
        await asyncio.sleep(2)

    await conn.disconnect()

asyncio.run(main())
