import gi
import sys
from screeninfo import get_monitors
import cv2
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject

# Initialize GStreamer
Gst.init(None)

# Function to read RTSP URLs from a file
def read_rtsp_urls(filename):
    urls = []
    try:
        with open(filename, 'r') as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"Error: File {filename} not found.")
    return urls

# Function to create a GStreamer pipeline for each RTSP URL

def create_pipeline(url):
    pipeline_str = f"rtspsrc location={url} latency=200 ! rtph265depay ! decodebin ! videoconvert ! appsink name=appsink0"
    pipeline = Gst.parse_launch(pipeline_str)
    return pipeline

# Main function
def main(monitor_index=0):
    rtsp_urls = read_rtsp_urls('rtsp_urls.txt')
    
    if len(rtsp_urls) != 4:
        print("Error: Exactly 4 RTSP URLs are required in the file.")
        return

    # Create GStreamer pipelines for each RTSP URL
    pipelines = [create_pipeline(url) for url in rtsp_urls]
    
    # Get the screen dimensions
    monitors = get_monitors()
    if monitor_index >= len(monitors):
        print(f"Error: Monitor index {monitor_index} is out of range. Using default monitor 0.")
        monitor_index = 0
    monitor = monitors[monitor_index]
    screen_width = monitor.width
    screen_height = monitor.height
    print(f"Selected Monitor {monitor_index}: Width = {screen_width}, Height = {screen_height}")

    # Set each pipeline to the playing state
    for pipeline in pipelines:
        print(f"Attempting to set pipeline to PLAYING state for URL: {pipeline.get_name()}")
        ret = pipeline.set_state(Gst.State.PLAYING)
        print(f"State change result for URL: {pipeline.get_name()} - {ret}")
        if ret == Gst.StateChangeReturn.FAILURE:
            print(f"Error: Unable to set the pipeline to PLAYING state for URL: {pipeline.get_name()}")

    # Main loop to read frames from pipelines and display them
    while True:
        frames = []
        for i, pipeline in enumerate(pipelines):
            appsink = pipeline.get_by_name('appsink0')
            if not appsink:
                print(f"Error: Unable to find appsink for pipeline {pipeline.get_name()}")
                frames.append(np.zeros((480, 640, 3), dtype=np.uint8))
                continue
            sample = appsink.emit('pull-sample')
            if sample:
                buffer = sample.get_buffer()
#                print(f"Buffer PTS: {buffer.pts}, DTS: {buffer.dts}, Duration: {buffer.duration}, Offset: {buffer.offset}, Size: {buffer.get_size()}")
                caps = sample.get_caps()
#                print(f"Capabilities for stream {i + 1}: {caps.to_string()}")
                width = caps.get_structure(0).get_value('width')
                height = caps.get_structure(0).get_value('height')
                timestamp = buffer.pts / Gst.SECOND
 #               print(f"Stream {i + 1}: Width = {width}, Height = {height}, Timestamp = {timestamp}")
                
                # Extract the frame and convert it to numpy array
  #              print(f"Buffer size: {buffer.get_size()}")
   #             print(f"Width: {width}, Height: {height}, Expected size: {height * width * 3}")
                success, info = buffer.map(Gst.MapFlags.READ)
                if success:
                    data = buffer.extract_dup(0, buffer.get_size())
                    frame = np.frombuffer(data, np.uint8)
#                    print(f"Frame length: {len(frame)}, Buffer length: {buffer.get_size()}")
                    num_pixels = height * width
                    if len(frame) == num_pixels * 3:
                        # RGB format
 #                       print(f"Reshaping frame to RGB with dimensions ({height}, {width}, 3)")
                        frame = frame.reshape((height, width, 3))
                    elif caps.get_structure(0).get_value('format') == 'NV12':
                        # NV12 format with possible padding
                        padded_width = 768  # Adjust this value as per the actual padded width received
                        padded_height = 512  # Adjust this value as per the actual padded height received
                        expected_size = padded_width * padded_height * 3 // 2
                        if len(frame) == expected_size:
#                            print(f"Handling NV12 format with padded dimensions ({padded_height}, {padded_width})")
                            # Reshape to Y plane and UV plane
                            y_plane = frame[:padded_width * padded_height].reshape((padded_height, padded_width))
                            uv_plane = frame[padded_width * padded_height:].reshape((padded_height // 2, padded_width))
                            # Crop to valid region
                            y_valid = y_plane[:height, :width]
                            uv_valid = uv_plane[:height // 2, :width]
                            # Merge Y and UV planes and convert to BGR
                            yuv_cropped = np.vstack((y_valid, uv_valid))
                            frame = cv2.cvtColor(yuv_cropped, cv2.COLOR_YUV2BGR_NV12)
                        else:
                            print(f"Warning: NV12 frame size mismatch. Expected {expected_size}, but got {len(frame)}")
                            frame = np.zeros((height, width, 3), dtype=np.uint8)
                    elif len(frame) == num_pixels:
                        # Grayscale format
                        print(f"Reshaping frame to Grayscale with dimensions ({height}, {width})")
                        frame = frame.reshape((height, width))
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
                    else:
                        print(f"Warning: Unexpected frame size {len(frame)} for dimensions ({height}, {width}), Buffer length: {buffer.get_size()}")
                frames.append(frame)
            else:
                frames.append(np.zeros((480, 640, 3), dtype=np.uint8))

        # Ensure we have exactly four frames
        while len(frames) < 4:
            frames.append(np.zeros((480, 640, 3), dtype=np.uint8))
        # Stack frames into a 2x2 grid
        top_row = np.hstack((frames[0], frames[1]))
        bottom_row = np.hstack((frames[2], frames[3]))
        grid_frame = np.vstack((top_row, bottom_row))

        # Resize grid to fit the screen while maintaining aspect ratio
        grid_frame_height, grid_frame_width = grid_frame.shape[:2]
        aspect_ratio = grid_frame_width / grid_frame_height
        if screen_width / screen_height > aspect_ratio:
            new_height = screen_height
            new_width = int(aspect_ratio * new_height)
        else:
            new_width = screen_width
            new_height = int(new_width / aspect_ratio)
        grid_frame = cv2.resize(grid_frame, (new_width, new_height))

        # Display the grid
        cv2.imshow('Surveillance Camera Grid', grid_frame)

        # Exit when 'q' key is pressed or window is closed
        if cv2.waitKey(1) & 0xFF == ord('q') or cv2.getWindowProperty('Surveillance Camera Grid', cv2.WND_PROP_VISIBLE) < 1:
            break

    # Set all pipelines to NULL state before exiting
    for pipeline in pipelines:
        pipeline.set_state(Gst.State.NULL)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    monitor_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(monitor_index)