"""
Audio track investigation for Unitree G1 EDU firmware 1.4.5.
Result: Zero audio frames received — G1 does not send mic audio over WebRTC.
The WebRTC audio transceiver is sendrecv but G1 does not negotiate an audio stream.

G1 mic audio is accessible via:
- DDS topic rt/audio_msg (ASR text output)
- UDP multicast 239.168.123.161:5555 (raw PCM16 16kHz mono, gated by vendor wake mode)

Note: WebRTC audio SEND to G1 speaker has not been fully tested.
"""

import asyncio
import sys
import numpy as np

import os
from dotenv import load_dotenv
from unitree_webrtc_connect.webrtc_driver import UnitreeWebRTCConnection
load_dotenv(os.path.expanduser("~/brewbert_brain/.env"))
AES_KEY = os.environ.get("UNITREE_AES_KEY")
from unitree_webrtc_connect.constants import WebRTCConnectionMethod

frame_count = 0

async def on_audio_frame(frame):
    global frame_count
    frame_count += 1
    arr = frame.to_ndarray()
    if frame_count <= 3 or frame_count % 50 == 0:
        print(f"  AUDIO FRAME #{frame_count}: "
              f"rate={frame.sample_rate}Hz "
              f"shape={arr.shape} "
              f"max_amplitude={np.abs(arr).max()}")

async def main():
    conn = UnitreeWebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.123.161", aes_128_key=AES_KEY, device_type="G1")
    await conn.connect()
    await asyncio.sleep(0.5)

    conn.audio.add_track_callback(on_audio_frame)

    print("Enabling audio channel...")
    conn.datachannel.switchAudioChannel(True)

    print("Listening 15s — talk near the robot mic...")
    for i in range(15):
        await asyncio.sleep(1)
        print(f"  t={i+1}s — frames: {frame_count}")

    print(f"\nTotal frames received: {frame_count}")
    if frame_count == 0:
        print("RESULT: No audio frames — G1 1.4.5 does not send mic audio over WebRTC")
    else:
        print("RESULT: Audio frames received — WebRTC mic access works on this firmware")

    await conn.disconnect()

asyncio.run(main())
