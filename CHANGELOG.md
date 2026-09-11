# Changelog

## 2026-09-11

### Added
- `zm16el_cover.py` — Zemismart ZM16EL-03/33 curtain motor (`_TZE200_68nvbio9` / `TS0601`):
  battery (DP 13) and motor fault (DP 12), with the cover re-declared to match stock
  behaviour.
- `zg204zx.py` — HOBEIAN ZG-204ZX mmWave presence sensor (`_TZE200_w0ap83qu`): static and
  motion detection sensitivity, detection distance, fading time, illuminance interval,
  anti-interference, LED indicator.
- Device documentation covering datapoint maps, the settings, and the capture method used
  to confirm each datapoint.

### Notes
- Documented that the ZM16EL sends DP 13 sporadically rather than on every travel, and
  that a naive low-battery automation will misfire as a result.
- Documented that ZG-204ZX datapoints differ from the ZG-204ZM draft in
  zha-device-handlers issue #5006.
