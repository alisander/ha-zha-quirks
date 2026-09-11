"""Zemismart ZM16EL-03/33 curtain motor - adds battery + motor fault.

Matches every `_TZE200_68nvbio9` / TS0601 curtain motor.

The stock quirk for these motors is `zhaquirks.tuya.ts0601_cover:TuyaMoesCover0601`,
a v1 CustomDevice that maps only the cover control and position datapoints. The
motors also report battery (DP 13) and motor fault (DP 12), which that quirk
ignores, so neither is visible in Home Assistant.

Custom quirks are inserted at the FRONT of the zha registry and `match_entry()`
returns the first hit, so this quirk REPLACES TuyaMoesCover0601 for every motor
it matches - the cover itself therefore has to be re-declared here. Spreading
that across a house full of blinds is a real risk, so it was first proven on one
motor via `.filter()` with an IEEE allowlist, then widened to all six, and only
then was the filter removed for release.

Datapoints confirmed by live capture on 2026-09-10, with `zigpy` at debug while
a motor was moving (a Tuya query-data returns only DP 12):

    DP  1  enum   control: open / stop / close
    DP  2  value  target position   (observed 0 when closing)
    DP  3  value  current position  (observed 68 mid-travel)
    DP 12  bitmap motor fault       (observed 0 = healthy, on all 6 motors)
    DP 13  value  battery %         (observed 100)

Position inversion is pinned empirically, not guessed: with raw DP 3 = 68 the
stock quirk showed the cover at position 68. ZHA holds covers as percent-CLOSED
and HA displays percent-OPEN, so DP 68 -> HA 68 requires the 100-x inversion.
`invert=True` (the builder default) therefore reproduces the stock behaviour
exactly.

BATTERY REPORTING IS SPORADIC - see docs/zemismart-zm16el.md. DP 13 is a plain
int32 percentage and a motor on USB charge reports a normal figure (one unit read
40% before charging and 100% after), but the motor does NOT send DP 13 on every
travel: in one test it arrived ~45 s after travel finished, and on a second move
90 s later it never came at all. The battery entity is therefore "last value
seen, whenever that was" with no freshness guarantee. Do not build a low-battery
alert on it without a staleness guard.

Written against zha-quirks 2.2.2 (Home Assistant 2026.8.1).
"""

from zhaquirks.builder import BinarySensorDeviceClass, EntityType
from zhaquirks.tuya.builder import TuyaQuirkBuilder

(
    TuyaQuirkBuilder("_TZE200_68nvbio9", "TS0601")
    .tuya_cover(
        control_dp=1,
        position_state_dp=3,
        position_control_dp=2,
        invert=True,
    )
    .tuya_binary_sensor(
        dp_id=12,
        attribute_name="motor_fault",
        entity_type=EntityType.DIAGNOSTIC,
        device_class=BinarySensorDeviceClass.PROBLEM,
        fallback_name="Motor fault",
    )
    .tuya_battery(dp_id=13)
    .skip_configuration()
    .add_to_registry()
)
