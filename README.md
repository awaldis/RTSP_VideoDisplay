# RTSP_VideoDisplay
A project that enables the automatic display of multiple camera video feeds via RTSP.  The goal is to minimize the need for user interaction by reading a predefined camera configuration file.

## disp_cams.py
Displays a 2x2 grid of live camera video using gstreamer and OpenCV.  This seemed to work but there were issues with old frames being displayed.

## rtsp_single_display.sh
Displays a single camera feed from a bash command line.  This seems to work but I had trouble trying expand it to show four camera feeds simultaneously.  It is still useful for examining the RTSP and RTP messaging with Wireshark.

## rtsp_Interactive.ipynb
An interactive Python notebook that allows single-step control of RTSP requests.  In conjunction with Wireshark, this is useful for debugging and developing intuition of how the requests ultimately trigger the camera video stream.

