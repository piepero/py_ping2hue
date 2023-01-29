# py_ping2hue

Changes the hue and the brightness of one or more ```Philips Hue``` lights depending on the current ping value.

The color of the light will shift from green, past yellow and orange, to red as the ping worsens and/or more packets are lost.
The brightness will increase from a minimum of 0 (minimal Hue brightness, for green) to 128 (half max. brightness, for red).

The script does not turn the lamps on or off on its own. You can simply turn off the lamp and keep the script running.

# Motivation

Since we are currently suffering from intermittent unreliable internet connections, the phrase "Is the internet down again?" is frequently heard at our home.

To easier answer this question, I have whipped up this little script that pings a server and colors one of our Philips Hue lights based on the current response time. The script is running on a Raspberry Pi.

# Features

- changes hue and brightness of one or more Philips Hue lights depending on ping results
- optionally turn those lights on and off automatically at specified times

# Configuration

Copy ```sample_config.toml``` to ```config.toml``` and enter the necessary configuration values, especially the bridge parameters (see [Get Started - Philips Hue Developer Program](https://developers.meethue.com/develop/get-started-2/)) and the lamp ID numbers.
Finding the correct IDs is currently left as an exercise to the reader...

# Roadmap

Some possible improvements to the script include:
- configurable update period
- configurable min and max brightness and the ability to disable brightness changes
- support for light names, groups, and rooms
