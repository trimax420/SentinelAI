import cv2
import numpy as np
import logging
import time
import subprocess
import os
import threading
from queue import Queue, Empty
from typing import Tuple, Optional, Dict, List

logger = logging.getLogger(__name__)

class HEVCStreamHandler:
    """
    Specialized handler for HEVC/H.265 high-resolution streams
    
    This class helps handle high-resolution HEVC streams by:
    1. Using OpenCV's CAP_FFMPEG backend for more reliable HEVC decoding
    2. Implementing frame buffering to prevent reference frame errors
    3. Providing adaptive resolution downscaling
    4. Handling stream reconnection and error recovery
    """
    
    def __init__(
        self, 
        source: str, 
        target_width: int = 640,
        target_height: int = 360,
        buffer_size: int = 5,
        use_ffmpeg: bool = True,
        ffmpeg_path: str = "ffmpeg"
    ):
        """
        Initialize the HEVC stream handler
        
        Args:
            source: RTSP URL or file path
            target_width: Target width for resizing
            target_height: Target height for resizing
            buffer_size: Size of the frame buffer
            use_ffmpeg: Whether to use FFmpeg for decoding (more robust for HEVC)
            ffmpeg_path: Path to FFmpeg executable
        """
        self.source = source
        self.target_width = target_width
        self.target_height = target_height
        self.buffer_size = buffer_size
        self.use_ffmpeg = use_ffmpeg
        self.ffmpeg_path = ffmpeg_path
        
        self.frame_buffer = Queue(maxsize=buffer_size)
        self.stop_event = threading.Event()
        self.is_running = False
        
        # Statistics
        self.stats = {
            "frames_read": 0,
            "frames_processed": 0,
            "reconnects": 0,
            "last_fps": 0,
            "original_width": 0,
            "original_height": 0,
            "decoder": "opencv_ffmpeg"
        }
        
        # Start the capture thread
        self.capture_thread = None
    
    def start(self):
        """Start the capture thread"""
        if self.is_running:
            return
            
        self.stop_event.clear()
        self.is_running = True
        
        # Use the opencv capture thread which works better based on test-feed.py
        self.capture_thread = threading.Thread(
            target=self._opencv_capture_thread,
            daemon=True
        )
            
        self.capture_thread.start()
        logger.info(f"Started HEVC stream handler for {self.source}")
    
    def stop(self):
        """Stop the capture thread"""
        if not self.is_running:
            return
            
        self.stop_event.set()
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=3.0)
            
        # Clear the queue
        while not self.frame_buffer.empty():
            try:
                _ = self.frame_buffer.get_nowait()
            except Empty:
                break
                
        logger.info(f"Stopped HEVC stream handler for {self.source}")
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read a frame from the buffer
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.is_running:
            return False, None
            
        try:
            frame = self.frame_buffer.get(timeout=2.0)
            return True, frame
        except Empty:
            return False, None
    
    def get_stats(self) -> Dict:
        """Get stream statistics"""
        return self.stats
    
    def _opencv_capture_thread(self):
        """OpenCV capture thread implementation - based on successful test-feed.py implementation"""
        cap = None
        last_frame_time = time.time()
        frames_count = 0
        reconnect_delay = 1.0  # Initial reconnect delay
        max_reconnect_delay = 10.0  # Maximum reconnect delay
        
        while not self.stop_event.is_set():
            if cap is None or not cap.isOpened():
                try:
                    # Use FFMPEG backend with RTSP transport via TCP - exactly like test-feed.py
                    logger.info(f"Opening stream with OpenCV CAP_FFMPEG: {self.source}")
                    cap = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)
                    
                    # Set buffer size - same as test-feed.py
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)
                    
                    # Configure hardware acceleration if available
                    cap.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
                    
                    # Check if opened successfully
                    if not cap.isOpened():
                        logger.warning(f"Failed to open stream: {self.source}")
                        time.sleep(reconnect_delay)
                        reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                        self.stats["reconnects"] += 1
                        continue
                    
                    # Reset reconnect delay on successful connection
                    reconnect_delay = 1.0
                    
                    # Get original stream dimensions
                    self.stats["original_width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    self.stats["original_height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    logger.info(f"Stream opened successfully: {self.source} - Resolution: "
                               f"{self.stats['original_width']}x{self.stats['original_height']}")
                    
                except Exception as e:
                    logger.error(f"Error opening stream: {str(e)}")
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                    self.stats["reconnects"] += 1
                    continue
            
            # Read frame
            try:
                ret, frame = cap.read()
                
                if not ret:
                    logger.warning(f"Failed to read frame from stream: {self.source}")
                    cap.release()
                    cap = None
                    time.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                    self.stats["reconnects"] += 1
                    continue
                
                # Reset reconnect delay on successful frame read
                reconnect_delay = 1.0
                
                # Resize frame if needed
                if frame.shape[1] != self.target_width or frame.shape[0] != self.target_height:
                    frame = cv2.resize(frame, (self.target_width, self.target_height))
                
                # Put frame in buffer, discard oldest if full
                if self.frame_buffer.full():
                    try:
                        _ = self.frame_buffer.get_nowait()
                    except Empty:
                        pass
                
                self.frame_buffer.put(frame)
                self.stats["frames_read"] += 1
                frames_count += 1
                
                # Calculate FPS every second
                now = time.time()
                if now - last_frame_time >= 1.0:
                    self.stats["last_fps"] = frames_count / (now - last_frame_time)
                    frames_count = 0
                    last_frame_time = now
                
            except Exception as e:
                logger.error(f"Error reading frame: {str(e)}")
                if cap is not None:
                    cap.release()
                    cap = None
                time.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
                self.stats["reconnects"] += 1
        
        # Clean up
        if cap is not None:
            cap.release()


# Helper function to check if a stream is HEVC encoded
def is_hevc_stream(source: str) -> bool:
    """
    Check if a video stream is using HEVC/H.265 encoding
    
    Args:
        source: Stream URL or file path
        
    Returns:
        True if the stream uses HEVC encoding
    """
    try:
        # Check if ffprobe is available
        try:
            subprocess.run(["ffprobe", "-version"], capture_output=True, timeout=2)
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.warning("ffprobe not found in PATH. Cannot detect HEVC streams. You may need to install FFmpeg.")
            # If we can't detect, assume high-resolution streams might be HEVC
            if source.startswith(("rtsp://", "http://", "https://")) or source.endswith((".mp4", ".mkv", ".hevc", ".265")):
                # For network streams or files with likely HEVC extensions, return True
                logger.info(f"Unable to check codec, assuming source might be HEVC based on URL/path: {source}")
                return True
            return False
            
        # Use FFprobe to check codec
        command = [
            "ffprobe",
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=codec_name",
            "-of", "default=noprint_wrappers=1:nokey=1",
            source
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        codec = result.stdout.strip().lower()
        
        return codec in ["hevc", "h265"]
    except Exception as e:
        logger.error(f"Error checking codec: {str(e)}")
        # Default to False if we can't check
        return False


# Helper function to create an appropriate stream handler
def create_stream_handler(
    source: str,
    target_width: int = 640,
    target_height: int = 360,
    force_ffmpeg: bool = False
) -> Tuple[cv2.VideoCapture, Dict]:
    """
    Create an appropriate stream handler for the given source
    
    Args:
        source: Stream URL or file path
        target_width: Target width for processing
        target_height: Target height for processing
        force_ffmpeg: Whether to force using FFmpeg even for non-HEVC streams
        
    Returns:
        Tuple of (capture object, stream info)
    """
    stream_info = {
        "source": source,
        "target_resolution": f"{target_width}x{target_height}",
        "handler_type": "standard"
    }
    
    # Check if we have FFmpeg available
    ffmpeg_available = False
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=2)
        ffmpeg_available = True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.warning("FFmpeg not found in PATH. Using OpenCV for all streams.")
        ffmpeg_available = False
    
    # If FFmpeg isn't available, use OpenCV regardless of stream type
    if not ffmpeg_available:
        logger.info(f"Using standard OpenCV handler for {source} (FFmpeg not available)")
        capture = cv2.VideoCapture(source)
        
        # Configure capture for better performance with OpenCV's built-in decoder
        capture.set(cv2.CAP_PROP_BUFFERSIZE, 5)
        capture.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
        
        # For high-resolution sources, we still need to resize after capture
        if capture.isOpened():
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            stream_info["original_resolution"] = f"{width}x{height}"
            stream_info["handler_type"] = "opencv_standard"
            
            # Add a note about high resolution
            if width > 1920 or height > 1080:
                logger.warning(f"High-resolution stream ({width}x{height}) detected but FFmpeg not available. "
                              f"Performance may be affected.")
        
        return capture, stream_info
    
    # With FFmpeg available, check if this is a high-resolution or HEVC stream
    if ffmpeg_available and (force_ffmpeg or is_hevc_stream(source)):
        logger.info(f"Using specialized HEVC handler for {source}")
        
        # Create and start HEVC handler
        handler = HEVCStreamHandler(
            source=source,
            target_width=target_width,
            target_height=target_height,
            use_ffmpeg=True
        )
        handler.start()
        
        # Create a custom capture object that uses our handler
        capture = _HEVCCapture(handler)
        
        stream_info["handler_type"] = "hevc_ffmpeg"
        return capture, stream_info
    
    # Standard OpenCV handling for non-HEVC streams
    logger.info(f"Using standard OpenCV handler for {source}")
    capture = cv2.VideoCapture(source)
    
    # Configure capture for better performance
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 5)
    capture.set(cv2.CAP_PROP_HW_ACCELERATION, cv2.VIDEO_ACCELERATION_ANY)
    
    # Check width/height
    if capture.isOpened():
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        stream_info["original_resolution"] = f"{width}x{height}"
    
    stream_info["handler_type"] = "opencv_standard"
    return capture, stream_info


class _HEVCCapture:
    """
    Custom capture class that wraps HEVCStreamHandler to provide a cv2.VideoCapture-like interface
    """
    def __init__(self, handler: HEVCStreamHandler):
        self.handler = handler
        
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame"""
        return self.handler.read()
        
    def isOpened(self) -> bool:
        """Check if the stream is opened"""
        return self.handler.is_running
        
    def release(self):
        """Release resources"""
        self.handler.stop()
        
    def get(self, prop_id):
        """Get a property (limited support)"""
        stats = self.handler.get_stats()
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return stats.get("original_width", 0)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return stats.get("original_height", 0)
        elif prop_id == cv2.CAP_PROP_FPS:
            return stats.get("last_fps", 30)
        return 0
        
    def set(self, prop_id, value):
        """Set a property (limited support)"""
        # Most properties can't be changed after initialization
        return False