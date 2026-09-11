# ha-zha-quirks

Custom [ZHA](https://www.home-assistant.io/integrations/zha/) quirks for Zigbee devices
that Home Assistant does not fully support out of the box.

Every quirk here was written against a real device and every datapoint was confirmed by
live packet capture, not copied from a datasheet. Where a published map was wrong, the
device docs say so and show what the hardware actually sent.

## Supported devices

| Device | Zigbee fingerprint | What the quirk adds | Docs |
|---|---|---|---|
| Zemismart ZM16EL-03/33 curtain motor | `_TZE200_68nvbio9` / `TS0601` | Battery %, motor fault | [docs](docs/zemismart-zm16el-curtain.md) |
| HOBEIAN ZG-204ZX 24 GHz mmWave presence sensor | `_TZE200_w0ap83qu` / `ZG-204ZX` (some units enumerate as `TS0601`) | Radar tuning: static + motion sensitivity, detection distance, fading time, illuminance interval, anti-interference, LED | [docs](docs/hobeian-zg204zx-radar.md) |

Find your device's fingerprint in Home Assistant under
**Settings → Devices & Services → ZHA → the device → Zigbee Info**. The `manufacturer`
and `model` shown there must match a row above exactly.

## Installation

ZHA loads custom quirks from a single folder that you nominate in `configuration.yaml`.

**1. Create the folder** on your Home Assistant config volume, for example:

```
/config/custom_zha_quirks/
```

**2. Copy in the quirks you want** from [`quirks/`](quirks/). Copy the `.py` files
themselves, not the folder — one flat directory of modules:

```
/config/custom_zha_quirks/
├── zm16el_cover.py
└── zg204zx.py
```

**3. Point ZHA at the folder** in `configuration.yaml`:

```yaml
zha:
  custom_quirks_path: /config/custom_zha_quirks/
```

**4. Restart Home Assistant.** Quirks are only loaded at startup — a ZHA reload alone
is not always enough, and editing a quirk file has no effect until you restart.

You do **not** need to re-pair, re-interview, or delete the device. Existing entity IDs
and history are preserved unless a device doc explicitly says otherwise.

### Verifying it applied

On the device page in ZHA, check **Zigbee Info**. `Quirk applied` should be `true` and
`Quirk class` should name a `zhaquirks.tuya.builder` entry rather than
`zigpy.device.Device` or a stock quirk class. The new entities appear on the device
page, most of them under **Configuration** or **Diagnostic**.

If nothing changed, see [Troubleshooting](#troubleshooting).

## Compatibility

Written and tested against **zha-quirks 2.2.2**, shipped in **Home Assistant 2026.8.1**.

These use the v2 `TuyaQuirkBuilder` API, which is not stable across major zha-quirks
releases. If a quirk stops loading after a Home Assistant upgrade, check the log for an
import error before assuming the device is at fault — the API, not the hardware, is the
usual cause.

## Troubleshooting

**Nothing changed after restarting.** Confirm `custom_quirks_path` points at the folder
*containing* the `.py` files, that the path is readable by Home Assistant, and that you
restarted rather than reloaded.

**A quirk fails to import and the whole folder goes quiet.** One bad module can stop the
others loading. Search the Home Assistant log for `zhaquirks` or the module name:

```
Settings → System → Logs → Load full logs
```

then search for `custom_zha_quirks`.

**The device is matched but the entities are missing.** Every v2 entity needs a
`translation_key` **or** a `device_class`. `fallback_name` alone does not satisfy
`EntityMetadata`, and the module raises `ValueError` on import if one is missing. This is
the single most common way these quirks break when edited.

**A stock quirk is winning.** Custom quirks are inserted at the *front* of the registry
and `match_entry()` returns the first hit, so a custom quirk normally replaces the stock
one. If it isn't applying at all, your device's manufacturer string almost certainly
differs — check Zigbee Info against the table above.

## A warning about replacing stock quirks

A custom quirk **replaces** the stock quirk for every device it matches, which means it
must re-declare everything the stock quirk provided. Get that wrong and you don't lose
one entity, you lose them across every matching device in the house at once.

If you are adapting these for a fleet, do what was done here: scope the quirk to a single
device first with an IEEE allowlist, confirm it behaves, then widen.

```python
import zigpy.device

ALLOWLIST = ("aa:bb:cc:dd:ee:ff:00:11",)

def is_allowed(device: zigpy.device.Device) -> bool:
    return str(device.ieee).lower() in ALLOWLIST

(
    TuyaQuirkBuilder("_TZE200_xxxxxxxx", "TS0601")
    .filter(is_allowed)
    ...
)
```

Remove the `.filter()` once you are satisfied.

## Upstreaming

The right long-term home for a working quirk is
[zigpy/zha-device-handlers](https://github.com/zigpy/zha-device-handlers), where it ships
inside Home Assistant and nobody has to install anything. Quirks here are offered
upstream where they are general enough; each device doc records its upstream status.

## Contributing

Issues and PRs welcome, particularly:

- Additional manufacturer IDs for a device already listed (same hardware, different
  Tuya batch — these often enumerate under a different `_TZE200_*` string).
- Corrections backed by a packet capture. Please include the raw frame, not just the
  decoded value; see the device docs for the capture method.

## Licence

[Apache License 2.0](LICENSE).
