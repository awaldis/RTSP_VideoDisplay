#!/bin/bash

# A gstreamer/bash script that displays an RTSP video feed.
# Intended for development and debugging, not production deployment.
# The actual RTSP URL strings are kept in a separate file for privacy.

# Read in the URL string(s).
# The number after the quote is the line number read.
rtsp_url=$(sed '1q;d' rtsp_urls.txt)

gst-launch-1.0 rtspsrc location=$rtsp_url latency=200 ! rtph265depay ! h265parse ! decodebin ! videoconvert ! autovideosink

