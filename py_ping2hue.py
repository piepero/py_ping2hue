"""py_ping2hue.py

Keep pinging a host machine and color one or more
Philips Hue lights according to the outcome.
"""

from dataclasses import dataclass
from functools import partial
from pathlib import Path
from time import sleep

import tomllib
from loguru import logger
from ping3 import ping

from schedfunc import SchedFunc
from simplehue import SimpleHue

cfg = tomllib.loads(Path("config.toml").read_text(encoding="utf-8"))
# assign config values to "constants" to improve code legibility
HUE_BRIDGE_ADDRESS = cfg["bridge"]["host"]
HUE_API_KEY = cfg["bridge"]["api_key"]
HUE_LIGHT_IDS = cfg["lights"]["ids"]
PING_HOST = cfg["ping"]["host"]
PING_GREEN = cfg["ping_range"]["green"]
PING_RED = cfg["ping_range"]["red"]
PACKET_LOSS_FACTOR = cfg["ping_range"]["loss_factor"]

# hue color values
HUE_VAL_GREEN = (65535 // 3) + 3000  # green, shifted 3000 towards cyan
HUE_VAL_RED = 0


@dataclass
class MultiPingResult:
    """Result of multiple pings."""

    ping_attempts: int
    mean_response_time: float
    lost_packets: int


def calculate_quality(ping_result: MultiPingResult) -> float:
    """Calculate a ping quality (from 1.0 to 0.0) from the ping_result."""

    # The quality is 1.0 for pings of PING_GREEN or better,
    # 0.0 for pings of PING_RED or worse,
    # and a linear value from 1.0 to 0.0 in between.
    if ping_result.mean_response_time <= PING_GREEN:
        quality = 1.0
    elif ping_result.mean_response_time >= PING_RED:
        quality = 0.0
    else:
        quality = 1 - (ping_result.mean_response_time - PING_GREEN) / (
            PING_RED - PING_GREEN
        )

    # Then, for each packet loss, we reduce the result by a configurable factor
    for _ in range(ping_result.lost_packets):
        quality *= PACKET_LOSS_FACTOR

    return quality


def collect_pings(num_of_pings: int, sleep_time_s: float = 1) -> MultiPingResult:
    """Collect num_of_pings pings and return the mean value and number of lost
    packets.
    """

    total_time = 0
    losses = 0

    for _ in range(num_of_pings):
        sleep(sleep_time_s)
        p = ping(PING_HOST, timeout=1, unit="s")
        if not p:
            losses += 1
            continue
        total_time += p

    if losses < num_of_pings:
        mean_time = total_time / (num_of_pings - losses)
    else:
        mean_time = 9999  # all packets lost

    return MultiPingResult(
        ping_attempts=num_of_pings,
        mean_response_time=mean_time,
        lost_packets=losses,
    )


def calc_hue(quality: float) -> int:
    """Calculate a hue value from the ping quality value."""

    return int(HUE_VAL_GREEN * quality + HUE_VAL_RED)


def calc_bri(quality: float) -> int:
    """Calculate hue brightness from the ping value.

    The better the quality, the lower the brightness.
    """
    return int(128 * (1 - quality))


def init_on_off_scheduler(hue: SimpleHue) -> list[SchedFunc]:

    if "auto_switch" not in cfg:
        return list()

    schedulers = list()

    if "on" in cfg["auto_switch"]:
        on_func = partial(hue.set_lights_state, HUE_LIGHT_IDS, {"on": True})
        for event in cfg["auto_switch"]["on"]:
            logger.debug(event)
            schedulers.append(
                SchedFunc(
                    isoweekdays=event.get("isoweekdays", [1, 2, 3, 4, 5, 6]),
                    hour=event["hour"],
                    minute=event.get("minute", 0),
                    second=event.get("second", 0),
                    func=on_func,
                )
            )

    if "off" in cfg["auto_switch"]:
        off_func = partial(hue.set_lights_state, HUE_LIGHT_IDS, {"on": False})
        for event in cfg["auto_switch"]["off"]:
            schedulers.append(
                SchedFunc(
                    isoweekdays=event.get("isoweekdays", [1, 2, 3, 4, 5, 6]),
                    hour=event["hour"],
                    minute=event.get("minute", 0),
                    second=event.get("second", 0),
                    func=off_func,
                )
            )

    return schedulers


def main() -> None:
    """Main loop."""

    my_hue = SimpleHue(HUE_BRIDGE_ADDRESS, HUE_API_KEY)

    on_off_schedulers = init_on_off_scheduler(my_hue)

    while True:

        for s in on_off_schedulers:
            s.process()

        ping_result = collect_pings(5)

        q = calculate_quality(ping_result)

        new_hue = calc_hue(q)
        new_bri = calc_bri(q)

        logger.debug(
            f"performed {ping_result.ping_attempts} pings "
            f"with {ping_result.lost_packets} losses and "
            f"a mean response time of {1000 * ping_result.mean_response_time:.0f} ms"
            f" (hue={new_hue}, bri={new_bri})"
        )

        new_state = {"hue": new_hue, "bri": new_bri, "sat": 255}

        my_hue.set_lights_state(HUE_LIGHT_IDS, new_state)


if __name__ == "__main__":
    main()
    main()
