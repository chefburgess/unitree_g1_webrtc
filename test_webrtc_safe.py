"""
Safe read-only WebRTC probe for Unitree G1 EDU.
No motion commands — subscribes to state topics only.
Useful for verifying connection and checking FSM/service state.
"""

import asyncio
import json
import sys

import os
from dotenv import load_dotenv
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
load_dotenv(os.path.expanduser("~/brewbert_brain/.env"))
AES_KEY = os.environ.get("UNITREE_AES_KEY")
from unitree_webrtc_connect.constants import WebRTCConnectionMethod, RTC_TOPIC, DATA_CHANNEL_TYPE

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.123.161", aes_128_key=AES_KEY, device_type="G1")
    await conn.connect()
    await asyncio.sleep(1)

    channel = conn.datachannel.channel
    ps = conn.datachannel.pub_sub

    @channel.on("message")
    async def on_all(message):
        try:
            if isinstance(message, str):
                parsed = json.loads(message)
                t = parsed.get('type')
                topic = parsed.get('topic', '')
                if t == 'res':
                    print(f"  << RES: {parsed}")
                elif t == 'msg' and 'servicestate' in str(topic):
                    data = parsed.get('data', '')
                    try:
                        services = json.loads(data) if isinstance(data, str) else data
                        print("\nSERVICES:")
                        for s in services:
                            status = '●' if s.get('status') else '○'
                            print(f"  {status} {s.get('name','?'):40} v{s.get('version','')}")
                    except Exception:
                        print(f"  << SERVICES RAW: {str(data)[:200]}")
                elif t == 'msg' and 'sportmode' in str(topic):
                    data = parsed.get('data', {})
                    print(f"  FSM: id={data.get('fsm_id')} mode={data.get('fsm_mode')} task={data.get('task_id')}")
        except Exception:
            pass

    print("Subscribing to state topics...")
    ps.subscribe(RTC_TOPIC["SERVICE_STATE"])
    ps.subscribe(RTC_TOPIC["LF_SPORT_MOD_STATE"])
    await asyncio.sleep(3)

    print("\nReading FSM ID...")
    ps.publish_without_callback(
        topic=RTC_TOPIC["SPORT_MOD"],
        data={"header": {"identity": {"id": 1, "api_id": 7001}}, "parameter": ""},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )
    await asyncio.sleep(1)

    print("Reading FSM Mode...")
    ps.publish_without_callback(
        topic=RTC_TOPIC["SPORT_MOD"],
        data={"header": {"identity": {"id": 2, "api_id": 7002}}, "parameter": ""},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )

    await asyncio.sleep(8)
    await conn.disconnect()

asyncio.run(main())
