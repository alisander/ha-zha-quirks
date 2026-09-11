"""HOBEIAN ZG-204ZX / _TZE200_w0ap83qu - 24GHz mmWave presence + T/H/lux sensor.

Stock ZHA has no quirk for this device (it loads as a bare `zigpy.device.Device`),
so the Tuya manufacturer cluster 0xEF00 is never decoded and none of the radar
tuning is reachable. The standard ZCL clusters the device also implements
(0x0400 illuminance, 0x0402 temperature, 0x0405 humidity, 0x0406 occupancy,
0x0500 IAS zone, 0x0001 power) already work without a quirk.

This quirk therefore only ADDS the configuration datapoints and deliberately
leaves the working sensors alone - no cluster is replaced, so existing entity
ids and history are preserved.

Datapoint map taken from zigbee-herdsman-converters, src/devices/tuya.ts,
definition `ZG-204ZX` (fingerprint TS0601 / _TZE200_w0ap83qu):

    DP   1  presence                       (standard 0x0406 already covers this)
    DP   2  static_detection_sensitivity    0-10        <- added
    DP   4  detection_distance              /100, metres <- added
    DP 101  humidity                       (standard 0x0405 already covers this)
    DP 102  fading_time                     0-28800 s   <- added
    DP 103  anti_interference               on/off      <- added
    DP 104  humidity_calibration
    DP 105  temperature_calibration         /10
    DP 106  illuminance                    (standard 0x0400 already covers this)
    DP 107  illuminance_interval            1-720 min   <- added
    DP 108  indicator (LED)                 on/off      <- added
    DP 109  temperature_unit
    DP 110  battery                        (standard 0x0001 already covers this)
    DP 111  temperature                     /10
    DP 123  motion_detection_sensitivity    0-10        <- added

Note: the draft quirk in zha-device-handlers issue #5006 is for the sibling
ZG-204ZM and maps DP 101 to "human motion state" and battery to DP 121. On the
ZG-204ZX those are wrong - DP 101 is humidity, and there is no human-motion-state
datapoint at all. This map is the ZG-204ZX one.

Every v2 entity needs a translation_key OR a device_class - EntityMetadata
__attrs_post_init__ raises ValueError otherwise, and fallback_name alone does
NOT satisfy it. That mistake made the whole module fail to import.

Written against zha-quirks 2.2.2 (Home Assistant 2026.8.1).
"""

import zigpy.types as t

from zhaquirks.builder import (
    EntityType,
    NumberDeviceClass,
    UnitOfLength,
    UnitOfTime,
)
from zhaquirks.tuya.builder import TuyaQuirkBuilder

(
    TuyaQuirkBuilder("_TZE200_w0ap83qu", "ZG-204ZX")
    # some units of this model enumerate with the generic Tuya model id instead
    .applies_to("_TZE200_w0ap83qu", "TS0601")
    # --- the setting that actually matters for holding a still person ---
    .tuya_number(
        dp_id=2,
        attribute_name="static_detection_sensitivity",
        type=t.uint16_t,
        min_value=0,
        max_value=10,
        step=1,
        translation_key="static_detection_sensitivity",
        fallback_name="Static detection sensitivity",
    )
    .tuya_number(
        dp_id=4,
        attribute_name="detection_distance",
        type=t.uint16_t,
        device_class=NumberDeviceClass.DISTANCE,
        unit=UnitOfLength.METERS,
        min_value=0,
        max_value=5,
        step=0.1,
        multiplier=0.01,
        translation_key="static_detection_distance",
        fallback_name="Detection distance",
    )
    .tuya_number(
        dp_id=102,
        attribute_name="presence_timeout",
        type=t.uint16_t,
        device_class=NumberDeviceClass.DURATION,
        unit=UnitOfTime.SECONDS,
        min_value=0,
        max_value=28800,
        step=1,
        translation_key="fading_time",
        fallback_name="Fading time",
    )
    .tuya_number(
        dp_id=123,
        attribute_name="motion_detection_sensitivity",
        type=t.uint16_t,
        min_value=0,
        max_value=10,
        step=1,
        translation_key="motion_detection_sensitivity",
        fallback_name="Motion detection sensitivity",
    )
    .tuya_number(
        dp_id=107,
        attribute_name="illuminance_interval",
        type=t.uint16_t,
        unit=UnitOfTime.MINUTES,
        min_value=1,
        max_value=720,
        step=1,
        translation_key="illuminance_interval",
        fallback_name="Illuminance interval",
    )
    .tuya_switch(
        dp_id=103,
        attribute_name="anti_interference",
        entity_type=EntityType.CONFIG,
        translation_key="anti_interference",
        fallback_name="Anti interference",
    )
    .tuya_switch(
        dp_id=108,
        attribute_name="indicator",
        entity_type=EntityType.CONFIG,
        translation_key="led_indicator",
        fallback_name="LED indicator",
    )
    .skip_configuration()
    .add_to_registry()
)
