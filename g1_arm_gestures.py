"""
Unitree G1 EDU — WebRTC Arm Gesture Control
Firmware 1.4.5 confirmed working.

Requires: pip install unitree_webrtc_connect

Usage:
    python3 g1_arm_gestures.py

Before running:
    - Robot must be in stable state (damping or standing)
    - Close the Unitree app completely — single WebRTC session only
    - Use BT remote to enter operation/standing mode for gestures to execute visibly
"""

import asyncio
import json
import sys

import os
from dotenv import load_dotenv
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
load_dotenv(os.path.expanduser("~/brewbert_brain/.env"))
AES_KEY = os.environ.get("UNITREE_AES_KEY")
from unitree_webrtc_connect.constants import WebRTCConnectionMethod, DATA_CHANNEL_TYPE

# RockChip IP — do not change
ROCKHIP_IP = "192.168.123.161"

# Correct WebRTC topic for arm service on G1
# NOTE: rt/api/sport/request, rt/api/loco/request do NOT work for arm on G1
ARM_TOPIC = "rt/api/arm/request"

# Built-in gesture IDs
GESTURE_WAVE         = 25   # wave_under_head — low subtle wave
GESTURE_HEART        = 33   # right_hand_on_heart — warmth/gratitude
GESTURE_HANDS_UP     = 15   # both_hands_up — excitement
GESTURE_HAND_UP      = 23   # right_hand_up — acknowledgment
GESTURE_MAKE_HEART   = 20   # make_heart_with_both_hands — joy
GESTURE_REFUSE       = 22   # refuse — use sparingly
GESTURE_RELEASE      = 99   # release_arm — always call after gesture


async def get_action_list(ps, msg_id=1):
    """Get all available gestures — built-in and custom."""
    result = {}

    channel_ref = [None]

    def on_response(msg):
        if msg.get('type') == 'res':
            data = msg.get('data', {})
            if isinstance(data, dict):
                identity = data.get('header', {}).get('identity', {})
                if identity.get('api_id') == 7107:
                    raw = data.get('data', '')
                    if raw:
                        result['data'] = json.loads(raw)

    ps.publish_without_callback(
        topic=ARM_TOPIC,
        data={"header": {"identity": {"id": msg_id, "api_id": 7107}},
              "parameter": ""},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )
    await asyncio.sleep(2)
    return result.get('data')


async def execute_builtin(ps, gesture_id, msg_id=1):
    """Execute a built-in gesture by numeric ID."""
    ps.publish_without_callback(
        topic=ARM_TOPIC,
        data={"header": {"identity": {"id": msg_id, "api_id": 7106}},
              "parameter": json.dumps({"data": gesture_id})},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )


async def execute_custom(ps, action_name, msg_id=1):
    """
    Execute a custom gesture by name via api_id 7112.
    Custom gestures are recorded in the Unitree app training mode.
    This api_id is undocumented in the official SDK.
    """
    ps.publish_without_callback(
        topic=ARM_TOPIC,
        data={"header": {"identity": {"id": msg_id, "api_id": 7112}},
              "parameter": json.dumps({"action_name": action_name})},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )


async def release_arm(ps, msg_id=99):
    """Release arm back to neutral. Always call after gestures."""
    await execute_builtin(ps, GESTURE_RELEASE, msg_id)


async def main():
    print("Connecting to G1 RockChip via WebRTC...")
    print("Make sure Unitree app is closed and robot is stable.\n")

    conn = UnitreeWebRTCConnection(
        WebRTCConnectionMethod.LocalSTA,
        ip=ROCKHIP_IP,
        aes_128_key=AES_KEY,
        device_type="G1"
    )
    await conn.connect()

    if not conn.isConnected:
        print("Connection failed.")
        return

    await asyncio.sleep(1)
    ps = conn.datachannel.pub_sub

    # Log all responses
    channel = conn.datachannel.channel

    @channel.on("message")
    async def on_response(message):
        try:
            if isinstance(message, str):
                parsed = json.loads(message)
                if parsed.get('type') in ('res', 'err'):
                    print(f"  << {parsed.get('type').upper()}: "
                          f"api_id={parsed.get('data', {}).get('header', {}).get('identity', {}).get('api_id')} "
                          f"code={parsed.get('data', {}).get('header', {}).get('status', {}).get('code')}")
        except Exception:
            pass

    # Step 1 — Get action list
    print("Fetching gesture list...")
    ps.publish_without_callback(
        topic=ARM_TOPIC,
        data={"header": {"identity": {"id": 1, "api_id": 7107}}, "parameter": ""},
        msg_type=DATA_CHANNEL_TYPE["REQUEST"]
    )
    await asyncio.sleep(2)

    # Step 2 — Built-in wave
    # Robot must be in standing/operation mode for visible motion
    print("\nExecuting built-in wave (id=25) — watch robot...")
    await execute_builtin(ps, GESTURE_WAVE, msg_id=2)
    await asyncio.sleep(6)

    # Step 3 — Release
    print("Releasing arm...")
    await release_arm(ps, msg_id=3)
    await asyncio.sleep(2)

    # Step 4 — Custom gesture by name
    # Replace "lowwave" with any custom gesture name from your action list
    custom_gesture = "lowwave"
    print(f"\nExecuting custom gesture '{custom_gesture}' via api_id 7112 — watch robot...")
    await execute_custom(ps, custom_gesture, msg_id=4)
    await asyncio.sleep(15)

    # Step 5 — Final release
    print("Final release...")
    await release_arm(ps, msg_id=5)
    await asyncio.sleep(2)

    print("\nDone.")
    await conn.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
