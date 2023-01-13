import os
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

# hue color values
HUE_VAL_GREEN = (65535 // 3) + 3000  # green, shifted 3000 towards cyan
HUE_VAL_RED = 0


def calculate_quality(response_time: float) -> float:
    """Calculate ping quality (float from 1.0 to 0.0) from the response_time.

    The quality is 1.0 for pings of PING_GREEN or better,
    0.0 for pings of PING_RED or worse,
    and a linear value from 1.0 to 0.0 in between."""
    if response_time <= PING_GREEN:
        return 1.0
    if response_time >= PING_RED:
        return 0.0
    return 1 - (response_time - PING_GREEN) / (PING_RED - PING_GREEN)


def update_lights(hue_val: int, hue_bri: int) -> None:
    """Send the new hue value to all configured lights.

    The on/off state is not changed, so that the
    light can be turned on and off independently.
    """

    for l_id in HUE_LIGHT_IDS:
        url = f"http://{HUE_BRIDGE_ADDRESS}/api/{HUE_API_KEY}/lights/{l_id}/state"
        data = {"hue": hue_val, "bri": hue_bri, "sat": 255}
        requests.put(url, json=data)


def collect_pings(num_of_pings: int, sleep_time_s: float = 1):
    """Collect num_of_pings pings and return the mean value."""
    total_time = 0
    losses = 0
    for _ in range(num_of_pings):
        p = ping(PING_HOST, timeout=1, unit="s")
        # count packet losses like a "red ping"
        if not p:
            losses += 1
            p = PING_RED
        total_time += p
        sleep(sleep_time_s)
    mean_time = total_time / num_of_pings
    logger.debug(
        f"mean of {num_of_pings} pings with {losses} losses: {1000 * mean_time:.0f} ms"
    )
    return mean_time


def calc_hue(quality: float) -> int:
    """Calculate a hue value from the ping quality value."""

    return int(HUE_VAL_GREEN * quality + HUE_VAL_RED)


def calc_bri(quality: float) -> int:
    """Calculate hue brightness from the ping value.

    The better the quality, the lower the brightness.
    """
    # TODO: make configurable
    return int(128 * (1 - quality))


def main() -> None:
    """Main loop."""
    while True:
        q = calculate_quality(collect_pings(5))
        update_lights(calc_hue(q), calc_bri(q))


if __name__ == "__main__":
    main()
