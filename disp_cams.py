import cv2
import imutils
import numpy as np
import os
import sys
from screeninfo import get_monitors

# Function to read RTSP URLs from a file
def read_rtsp_urls(filename):
    urls = []
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            urls = [line.strip() for line in file.readlines() if line.strip()]
    return urls

# Main function
def main(monitor_index=0):
    rtsp_urls = read_rtsp_urls('rtsp_urls.txt')
    
    if len(rtsp_urls) != 4:
        print("Error: Exactly 4 RTSP URLs are required in the file.")
        return

    # Initialize video capture objects for each URL
    captures = [cv2.VideoCapture(url) for url in rtsp_urls]
    
    # Print the width and height of each RTSP stream
    for i, capture in enumerate(captures):
        if capture.isOpened():
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Stream {i + 1}: Width = {width}, Height = {height}")
        else:
            print(f"Stream {i + 1}: Unable to open stream.")
    
    # Get the screen dimensions
    monitors = get_monitors()
    if monitor_index >= len(monitors):
        print(f"Error: Monitor index {monitor_index} is out of range. Using default monitor 0.")
        monitor_index = 0
    monitor = monitors[monitor_index]
    screen_width = monitor.width
    screen_height = monitor.height
    print(f"Selected Monitor {monitor_index}: Width = {screen_width}, Height = {screen_height}")

    while True:
        frames = []
        for i, capture in enumerate(captures):
            # Skip old frames and only grab the latest frame
            capture.grab()
            ret, frame = capture.retrieve()
            if not ret:
                frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Blank frame if no video
            frame = imutils.resize(frame, width=int(screen_width / 2))
            frames.append(frame)

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

    # Release all video captures and destroy windows
    for capture in captures:
        capture.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    monitor_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(monitor_index)