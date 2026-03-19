# Unitree G1 EDU — WebRTC Arm Control & Gesture Research

Undocumented WebRTC API findings for the **Unitree G1 EDU humanoid robot (firmware 1.4.5)**.

Covers arm service topic discovery, built-in gesture execution, and custom gesture execution by name via `rt/api/arm/request` — none of which are documented in the official SDK or the `unitree_webrtc_connect` library.

Companion findings to [unitree_webrtc_connect issue filed here](https://github.com/legion1581/unitree_webrtc_connect/issues/).

---

## Background

The official Unitree Python SDK (`G1ArmActionClient`) only exposes built-in gestures via numeric IDs over DDS. Custom gestures recorded in the Unitree app cannot be triggered programmatically via the public SDK — attempts return error 7403.

This research found that custom gestures **are** accessible via the WebRTC channel using `api_id 7112` with an `action_name` parameter, on the topic `rt/api/arm/request`.

---

## Requirements

- Unitree G1 EDU, firmware 1.4.5
- Python 3.8+
- `unitree_webrtc_connect` library
```bash
pip install unitree_webrtc_connect
```

---

## Key Findings

| Finding | Detail |
|---------|--------|
| Correct arm topic | `rt/api/arm/request` |
| Response topic | `rt/api/arm/response` |
| Built-in gesture execution | `api_id 7106`, parameter `{"data": <int_id>}` |
| Custom gesture by name | `api_id 7112`, parameter `{"action_name": "<name>"}` |
| Get action list | `api_id 7107` |
| Release arm | `api_id 7106`, parameter `{"data": 99}` |
| Audio track (mic) | Not available on G1 1.4.5 — zero frames received |
| Sport commands via WebRTC | Return 3203 on G1 — Go2 only |
| Firmware 1.4.5 | Confirmed working (library docs only list 1.4.0) |

---

## Gesture Library (Built-in)

| ID | Name | Notes |
|----|------|-------|
| 25 | wave_under_head | Low subtle wave |
| 33 | right_hand_on_heart | Warmth/gratitude |
| 15 | both_hands_up | Excitement |
| 23 | right_hand_up | Acknowledgment |
| 20 | make_heart_with_both_hands | Joy |
| 22 | refuse | Use sparingly |
| 99 | release_arm | Always call after gesture |

Custom gestures are recorded via the Unitree app training mode and appear in `GetActionList` results.

---

## Important Notes

- **Single WebRTC session only** — close the Unitree app before connecting
- **BT remote required** to enter operation/standing mode on G1 (WebRTC sport commands return 3203)
- The RockChip only allows one WebRTC client at a time — app disconnects when script connects
- Always call `release_arm` (data=99) after each gesture
- Connect in stable damping state — 504 timeout occurs during FSM transitions

---

## Files

| File | Purpose |
|------|---------|
| `g1_arm_gestures.py` | Clean working example — connect, list gestures, fire wave and custom gesture |
| `test_webrtc_safe.py` | Read-only probe — FSM state, service state, no motion |
| `test_arm_topic.py` | Topic discovery script — found `rt/api/arm/request` |
| `test_webrtc_audio.py` | Audio track investigation — confirmed no mic audio on G1 1.4.5 |

---

## Credits

- `unitree_webrtc_connect` by [legion1581](https://github.com/legion1581/unitree_webrtc_connect) — the WebRTC driver that made this possible
- Research conducted as part of the Brewbert voice assistant project on G1 EDU
