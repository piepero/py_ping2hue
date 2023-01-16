"""py_ping2hue.py

Keep pinging a host machine and color one or more
Philips Hue lights according to the outcome.
"""

from dataclasses import dataclass
from pathlib import Path
from time import sleep

import requests
from loguru import logger
from ping3 import ping

try:
    import tomllib
except ImportError:
    import tomli as tomllib

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


def update_light(light: int, hue: int, bri: int) -> None:
    """Set hue and brightness value to the selected light."""

    url = f"http://{HUE_BRIDGE_ADDRESS}/api/{HUE_API_KEY}/lights/{light}/state"
    data = {"hue": hue, "bri": bri, "sat": 255}
    try:
        requests.put(url, json=data)
    except (requests.ConnectionError, requests.Timeout):
        pass


def collect_pings(num_of_pings: int, sleep_time_s: float = 1) -> MultiPingResult:
    """Collect num_of_pings pings and return the mean value and number of lost packets."""

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


def main() -> None:
    """Main loop."""

    while True:

        ping_result = collect_pings(5)

        q = calculate_quality(ping_result)

        new_hue = calc_hue(q)
        new_bri = calc_bri(q)

        logger.debug(
            f"performed {ping_result.ping_attempts} pings "
            f"with {ping_result.lost_packets} losses and a mean response time of {1000 * ping_result.mean_response_time:.0f} ms"
            f" (hue={new_hue}, bri={new_bri})"
        )

        for l_id in HUE_LIGHT_IDS:
            update_light(light=l_id, hue=new_hue, bri=new_bri)


if __name__ == "__main__":
    main()
