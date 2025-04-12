import cv2
import time
import argparse
import sys

def test_rtsp_feed(rtsp_url, timeout=30, show_video=True):
    """
    Test an RTSP feed by connecting to it and optionally displaying the video stream
    
    Parameters:
    - rtsp_url (str): The RTSP URL to test
    - timeout (int): Number of seconds to wait before timing out if no frames are received
    - show_video (bool): Whether to display the video feed in a window
    
    Returns:
    - bool: True if connection was successful, False otherwise
    """
    print(f"Attempting to connect to RTSP stream: {rtsp_url}")
    
    # Use FFMPEG backend with RTSP transport via TCP
    cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
    
    # Some additional options that may help with certain streams
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)  # Set buffer size
    
    # Check if connection was successful
    if not cap.isOpened():
        print("Failed to open RTSP stream")
        return False
    
    print("Connection established. Attempting to receive frames...")
    
    start_time = time.time()
    frame_count = 0
    ret = False
    
    while True:
        # Check if timeout has been reached
        if time.time() - start_time > timeout and frame_count == 0:
            print(f"Timeout reached ({timeout} seconds). No frames received.")
            break
        
        # Try to read a frame
        ret, frame = cap.read()
        
        if not ret:
            if frame_count == 0:
                print("Could not read any frames from the stream")
                time.sleep(0.5)  # Wait a bit before trying again
                continue
            else:
                print("Stream ended or disconnected")
                break
        
        frame_count += 1
        
        # If this is the first frame, report success
        if frame_count == 1:
            print("Successfully received first frame!")
            print(f"Frame dimensions: {frame.shape[1]}x{frame.shape[0]}")
        
        # Display the frame if requested
        if show_video:
            cv2.imshow('RTSP Stream', frame)
            
            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("User terminated the stream")
                break
    
    # Clean up
    cap.release()
    if show_video:
        cv2.destroyAllWindows()
    
    # Report results
    if frame_count > 0:
        print(f"Success! Received {frame_count} frames.")
        return True
    else:
        print("Failed to receive any frames from the stream.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test an RTSP stream')
    parser.add_argument('url', help='RTSP URL to test')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds (default: 30)')
    parser.add_argument('--no-video', action='store_true', help='Do not display video window')
    
    args = parser.parse_args()
    
    try:
        success = test_rtsp_feed(args.url, args.timeout, not args.no_video)
        sys.exit(0 if success else 1)vs
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)