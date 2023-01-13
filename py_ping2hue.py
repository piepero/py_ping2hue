import os
from time import sleep

import requests
from dotenv import load_dotenv
from loguru import logger
from ping3 import ping

load_dotenv()

HUE_BRIDGE_ADDRESS = os.getenv("HUE_BRIDGE_ADDRESS")
HUE_API_KEY = os.getenv("HUE_API_KEY")

PING_GREEN = 0.05
PING_RED = 0.40

HUE_VAL_GREEN = (65535 // 3) + 3000  # green, shifted 3000 towards cyan
HUE_VAL_RED = 0

HUE_LIGHT_NUMBER = 1


def update_light(hue_val):
    """Send the new hue value to the selected light.

    On/Off, Brightness and Saturation are not changed, so that the
    light can be dimmed or turned off independently.
    """
    url = (
        f"http://{HUE_BRIDGE_ADDRESS}/api/{HUE_API_KEY}/lights/{HUE_LIGHT_NUMBER}/state"
    )
    data = {"hue": hue_val}

    r = requests.put(url, json=data)


def collect_pings(num_of_pings: int, sleep_time_s: float = 1):
    """Collect num_of_pings pings and return the mean value."""
    total_time = 0
    losses = 0
    for _ in range(num_of_pings):
        p = ping("google.com", timeout=1, unit="s")
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


def ping_to_hue(ping_in_s: float) -> int:
    """Calculate a hue value from the ping value"""
    if ping_in_s <= PING_GREEN:
        return HUE_VAL_GREEN
    if ping_in_s >= PING_RED:
        return HUE_VAL_RED

    return int(
        HUE_VAL_GREEN * (1.0 - (ping_in_s - PING_GREEN) / (PING_RED - PING_GREEN))
    )


def main() -> None:
    while True:
        update_light(ping_to_hue(collect_pings(5)))


if __name__ == "__main__":
    main()
