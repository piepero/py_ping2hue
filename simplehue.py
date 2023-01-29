from collections.abc import Iterable

import requests
from loguru import logger


class SimpleHue:

    host: str
    api_key: str

    def __init__(self, host: str, api_key: str):
        self.host = host
        self.api_key = api_key

    def set_light_state(self, light: int, new_state: dict):
        """Request to change the state of multiple lights."""
        try:
            url = f"http://{self.host}/api/{self.api_key}/lights/{light}/state"
            logger.debug(f"url: {url}")
            requests.put(url, json=new_state)
        except (requests.ConnectionError, requests.Timeout):
            logger.exception("Error sending request to bride!")
            pass

    def set_lights_state(self, lights: Iterable[int], new_state: dict):
        """Request to change the state of a single light."""
        for light in lights:
            self.set_light_state(light, new_state)
