# HOBEIAN ZG-204ZX 24 GHz mmWave presence sensor

**Fingerprint:** `_TZE200_w0ap83qu` / `ZG-204ZX` — some units enumerate with the generic
Tuya model id `TS0601` instead, so the quirk matches both.
**Quirk:** [`quirks/zg204zx.py`](../quirks/zg204zx.py)
**Upstream status:** not yet submitted. See [Relationship to the ZG-204ZM](#relationship-to-the-zg-204zm-and-issue-5006).

## What this adds

Out of the box ZHA has no quirk for this device, so it loads as a bare
`zigpy.device.Device`. The Tuya manufacturer cluster `0xEF00` is never decoded and **none
of the radar tuning is reachable** — you get presence and the environmental sensors, and
no way to adjust how the radar behaves.

The standard ZCL clusters the device also implements already work without any quirk:

| Cluster | Provides |
|---|---|
| `0x0406` | occupancy |
| `0x0400` | illuminance |
| `0x0402` | temperature |
| `0x0405` | humidity |
| `0x0500` | IAS zone |
| `0x0001` | battery |

**This quirk therefore only *adds* the configuration datapoints.** No cluster is
replaced, so your existing entity IDs and history survive.

## Datapoint map

| DP | Meaning | Exposed by this quirk |
|---|---|---|
| 1 | presence | no — `0x0406` already covers it |
| 2 | static detection sensitivity (0–10) | **yes** |
| 4 | detection distance (÷100, metres) | **yes** |
| 101 | humidity | no — `0x0405` already covers it |
| 102 | fading time (0–28800 s) | **yes** |
| 103 | anti-interference (on/off) | **yes** |
| 104 | humidity calibration | no |
| 105 | temperature calibration (÷10) | no |
| 106 | illuminance | no — `0x0400` already covers it |
| 107 | illuminance interval (1–720 min) | **yes** |
| 108 | indicator LED (on/off) | **yes** |
| 109 | temperature unit | no |
| 110 | battery | no — `0x0001` already covers it |
| 111 | temperature (÷10) | no |
| 123 | motion detection sensitivity (0–10) | **yes** |

Map derived from `zigbee-herdsman-converters`, `src/devices/tuya.ts`, definition
`ZG-204ZX`, and confirmed against a live device.

## The settings, explained

This is a **battery-powered** radar. Several of these settings trade battery life for
responsiveness, so they are worth understanding rather than maxing out.

### Static detection sensitivity (0–10)

**The setting that matters most.** How hard the radar works to keep seeing someone who is
*motionless* — reading, working at a desk, sleeping. At that point it is detecting
breathing and micro-movement, which is a far weaker signal than someone walking.

- Too low → the lights go off while you are still in the room. This is the classic
  complaint and this is the cure.
- Too high → a moving curtain, a fan, or warm air rising off a radiator reads as a person.

Start around 7–8 for a room where people sit still. Raise it only after you have set the
detection distance correctly, otherwise you are amplifying a room you didn't mean to watch.

### Static detection distance (0–5 m, 0.1 m steps)

The maximum range at which *static* presence counts. 24 GHz radar penetrates plasterboard
and glass happily, so at the 5 m maximum a bedroom sensor may well be watching the landing
or the room next door.

**Set this before touching sensitivity.** If you get phantom occupancy in an empty room,
pull the distance back to roughly the far wall first.

### Motion detection sensitivity (0–10)

How easily *gross* movement — someone walking in — trips it. Much easier to detect than
stillness, so the middle of the range is normally correct and there is rarely a reason to
change it. If entry detection is slow, look at fading time and placement first.

### Fading time (0–28800 s)

How long the sensor keeps reporting "occupied" after the last detection before it clears.
This is the real occupancy timeout.

If presence flickers off while you are still there, **raise this before raising
sensitivity** — it is the cheaper fix and it cannot introduce false positives. 60 s is
brisk; 120–300 s suits a bedroom or study.

### Illuminance interval (1–720 min)

How often the sensor reports lux. At 1 minute it is transmitting constantly, on a battery.
Unless you have automations reacting to light minute by minute, 10–15 minutes will
noticeably extend battery life.

### Anti-interference (on/off)

Suppresses cross-talk from another 24 GHz radar nearby or a strong RF source, at some cost
to sensitivity. Worth having on if two radars share a room or face each other through a
wall. If this is the only radar in the area, try it **off** and see whether static
detection improves.

### LED indicator (on/off)

The blink LED on the device. Cosmetic. Off in a bedroom.

## Tuning order

Symptoms map to settings in a specific order. Working down this list beats turning
everything up:

**"It drops me while I'm sitting still"**
1. Raise **fading time**
2. Raise **static detection sensitivity**
3. Consider turning **anti-interference** off

**"It thinks someone's there when the room is empty"**
1. Lower **static detection distance** — you are probably seeing through a wall
2. Lower **static detection sensitivity**
3. Check for a fan, radiator, or curtain in the beam

## Two entities that are not from this quirk

You will also see **Occupied to unoccupied delay** and **Unoccupied to occupied delay** on
the device. Those are the generic ZCL occupancy attributes from cluster `0x0406`, not
supplied here. On this hardware they appear not to be wired through to the Tuya MCU, and
changing them has no observable effect. **Fading time (DP 102) is the setting that
actually controls the timeout.**

## Relationship to the ZG-204ZM, and issue 5006

The draft quirk in
[zha-device-handlers issue #5006](https://github.com/zigpy/zha-device-handlers/issues/5006)
targets the sibling **ZG-204ZM** and is **wrong for the ZG-204ZX**:

- It maps DP 101 to "human motion state". On the ZG-204ZX, **DP 101 is humidity**.
- It reads battery from DP 121. On the ZG-204ZX, **battery is DP 110** — and is already
  covered by the standard `0x0001` cluster, so it needs no mapping at all.
- There is no human-motion-state datapoint on the ZG-204ZX.

If you have a ZG-204ZM, use that issue's map. If you have a ZG-204ZX, use this one.

## A note for anyone editing this quirk

Every v2 entity needs a `translation_key` **or** a `device_class`.
`EntityMetadata.__attrs_post_init__` raises `ValueError` otherwise, and `fallback_name`
alone does **not** satisfy it. A single omission makes the whole module fail to import,
which silently takes out every other quirk in the folder.
