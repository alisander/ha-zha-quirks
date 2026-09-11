# Zemismart ZM16EL-03/33 curtain motor

**Fingerprint:** `_TZE200_68nvbio9` / `TS0601`
**Quirk:** [`quirks/zm16el_cover.py`](../quirks/zm16el_cover.py)
**Upstream status:** not yet submitted

## What this adds

Home Assistant already drives these motors through the stock quirk
`zhaquirks.tuya.ts0601_cover:TuyaMoesCover0601`. That quirk maps only the cover control
and position datapoints, so the motor's **battery level** and **motor fault** are
invisible even though the hardware reports both.

This quirk adds:

| Entity | Type | Source |
|---|---|---|
| Battery | sensor, `%` | DP 13 |
| Motor fault | binary_sensor, `problem`, diagnostic | DP 12 |

The cover entity itself is re-declared identically, because a custom quirk replaces the
stock one entirely (see the warning in the [README](../README.md#a-warning-about-replacing-stock-quirks)).
Position behaviour, entity IDs and history are unchanged.

## Datapoint map

| DP | Type | Meaning | Observed |
|---|---|---|---|
| 1 | enum | control: open / stop / close | — |
| 2 | value | target position | 0 when closing |
| 3 | value | current position | 68 mid-travel |
| 12 | bitmap | motor fault | 0 = healthy, on all six units tested |
| 13 | value | battery % | int32, 0–100 |

A Tuya query-data (`0x03`) against these motors returns **only DP 12**. Everything else
has to be observed while the motor is actually doing something.

## Position inversion

`invert=True` is not a guess. With raw DP 3 = 68, the stock quirk showed the cover at
position 68 in Home Assistant. ZHA stores covers as percent-**closed** and Home Assistant
displays percent-**open**, so reproducing that mapping requires the `100 - x` inversion.
The builder default `invert=True` therefore matches stock behaviour exactly. If you
change it, your blinds will read backwards.

## Battery reporting: read this before building an alert

Verified by live capture on 2026-09-11 across six motors. Three findings, all of which
matter if you intend to automate on this sensor.

### DP 13 is a plain battery percentage

The raw frame, captured with `zigpy` at debug while a motor finished moving:

```
[0x304A:1:0xef00] Received ZCL frame: '09 61 02 00 01 0d 02 00 04 00 00 00 64'
                                                   ^^ ^^       ^^^^^^^^^^^
                                                 DP 13  type 0x02   0x64 = 100
[0x304a:1:0xef00] Received value 100 for attribute 0x000d
```

Tuya type `0x02` is a 4-byte integer value. Not an enum, not a bitmask, not a status code.

### A motor on USB charge reports a normal percentage, and there is no charging flag

One unit read **40%** the evening before the test, sat on its charger overnight, and
reported **100%** after the test move. The figure tracks real pack charge.

Across the entire capture window the motor emitted only DP 2, DP 3 and DP 13 — no
charging state, no power-source datapoint, nothing. **This firmware has no charging
indicator to expose**, so no quirk can surface one.

### DP 13 is sent sporadically, NOT on every travel

This is the trap.

| Test | Action | Battery frame |
|---|---|---|
| 1 | moved 100% → 60% → 100% | arrived ~45 s **after** travel finished |
| 2 | moved 100% → 70% → 100%, 90 s later | **never arrived** — only DP 2 and DP 3 |

Separately, three motors driven by the same command reported battery within two seconds
of each other, then went silent for a full day of ordinary daily use.

**The battery entity is therefore "last value seen, whenever that was", with no freshness
guarantee.** Home Assistant's `last_reported` is the only honest indicator of age, and it
can be days old on a motor being used every morning.

### What this means for automations

A naive low-battery automation will misfire:

```yaml
# DON'T: one bad sample pins this below the threshold forever,
# and a "for:" hold makes the alert *more* certain, not less.
triggers:
  - trigger: numeric_state
    entity_id: sensor.curtain_battery
    below: 20
    for: "00:30:00"
```

Because the value is frozen rather than refreshed, the hold is always satisfied. Guard on
staleness as well as value — require that the reading is recent before believing it:

```yaml
conditions:
  - condition: template
    value_template: >
      {{ (now() - states.sensor.curtain_battery.last_reported).total_seconds() < 172800 }}
```

A single anomalous end-of-travel reading is realistic: one unit in the test fleet reported
`0` at the end of a close while two identical motors on the same command reported `100`,
and that `0` then persisted indefinitely because nothing refreshed it.

## Capture method

To reproduce any of this on your own motors:

1. Turn on debug logging, either in `configuration.yaml` or via the `logger.set_level`
   action:

   ```yaml
   action: logger.set_level
   data:
     zigpy: debug
     zigpy.zcl: debug
     zhaquirks: debug
   ```

2. Move the cover and wait at least 60 s after travel completes.

3. Read the log (**Settings → System → Logs → Load full logs**) and search for your
   device's network address, e.g. `0x304A`, which is shown on the ZHA device page under
   Zigbee Info as `nwk`.

4. Decoded datapoints appear as
   `[0x304a:1:0xef00] Received value <n> for attribute 0x000d`, and the raw bytes as
   `Received ZCL frame: '...'`.

5. **Turn debug back off** — these logs are enormous.
