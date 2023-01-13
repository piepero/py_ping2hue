# py_ping2hue

Change the hue of a ```Philips Hue``` light depending to the current ping value.

The color of the light will shift from green, past yellow and orange, to red as the ping worsens.

# Motivation

Since we are currently suffering from a unreliable internet connection, the phrase "Is the internet down again?" is frequently heard at our home.

To easier answer this question, I have whipped up this little script that pings a server and colors one of our Philips Hue lights based on the current response time.

I try to keep the script both fairly straightforward to help people who want to base their own code on this example, and sufficiently flexible to make it useful on its own.
