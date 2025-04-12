import subprocess
import logging
import time
import os
import threading
import cv2
import re
from typing import Dict, Tuple, List, Optional

logger = logging.getLogger(__name__)

def test_rtsp_connection(url: str, timeout: int = 10) -> Dict:
    """
    Test RTSP connection and return detailed diagnostics
    
    Args:
        url: RTSP URL to test
        timeout: Timeout in seconds
        
    Returns:
        Dictionary with test results
    """
    results = {
        "url": url,
        "success": False,
        "connection_success": False,
        "authentication_success": False,
        "stream_received": False,
        "errors": [],
        "warnings": [],
        "codec": "unknown",
        "resolution": "unknown",
        "stream_info": {},
        "diagnostic_steps": []
    }
    
    # Step 1: Check if URL format is valid
    if not url.startswith("rtsp://"):
        results["errors"].append("Invalid URL format - must start with rtsp://")
        return results
    
    # Extract components from URL for testing
    url_parts = parse_rtsp_url(url)
    results["url_parts"] = url_parts
    
    # Step 2: Check if host is reachable
    results["diagnostic_steps"].append("Testing host reachability...")
    if "host" in url_parts:
        host_check = check_host_reachable(url_parts["host"])
        results["host_reachable"] = host_check["success"]
        if not host_check["success"]:
            results["errors"].append(f"Host {url_parts['host']} is not reachable: {host_check['error']}")
    
    # Step 3: Test with FFprobe
    results["diagnostic_steps"].append("Testing with FFprobe...")
    ffprobe_available = check_ffprobe_available()
    if ffprobe_available:
        ffprobe_results = test_with_ffprobe(url, timeout)
        results.update(ffprobe_results)
        if ffprobe_results["success"]:
            results["connection_success"] = True
            results["authentication_success"] = True
            results["stream_received"] = True
    else:
        results["warnings"].append("FFprobe not available - skipping detailed stream analysis")
    
    # Step 4: Test with OpenCV (as fallback or additional test)
    results["diagnostic_steps"].append("Testing with OpenCV...")
    opencv_results = test_with_opencv(url, timeout)
    results["opencv_results"] = opencv_results
    
    # If FFprobe failed but OpenCV worked, update overall success
    if not results["success"] and opencv_results["success"]:
        results["success"] = True
        results["connection_success"] = True
        results["authentication_success"] = True
        results["stream_received"] = True
        results["codec"] = opencv_results.get("codec", "unknown")
        results["resolution"] = opencv_results.get("resolution", "unknown")
    
    # Final success determination
    results["success"] = results["connection_success"] and results["stream_received"]
    
    # Add recommendations based on errors
    if not results["success"]:
        results["recommendations"] = generate_recommendations(results)
    
    return results

def parse_rtsp_url(url: str) -> Dict:
    """Parse RTSP URL into components"""
    parts = {}
    # Basic parsing
    match = re.match(r'rtsp://(?:([^:@]+):([^@]+)@)?([^:/]+)(?::(\d+))?(?:/(.+))?', url)
    if match:
        username, password, host, port, path = match.groups()
        parts["host"] = host
        if port:
            parts["port"] = int(port)
        else:
            parts["port"] = 554  # Default RTSP port
        
        if username:
            parts["username"] = username
        if password:
            parts["password"] = "********"  # Hide actual password in logs
        if path:
            parts["path"] = path
    return parts

def check_host_reachable(host: str) -> Dict:
    """Check if host is reachable via ping"""
    result = {"success": False, "error": ""}
    try:
        # Ping command depends on OS
        if os.name == 'nt':  # Windows
            ping_cmd = ["ping", "-n", "2", "-w", "1000", host]
        else:  # Linux/Mac
            ping_cmd = ["ping", "-c", "2", "-W", "1", host]
        
        proc = subprocess.run(ping_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3)
        result["success"] = proc.returncode == 0
        if not result["success"]:
            result["error"] = "Host did not respond to ping"
    except subprocess.TimeoutExpired:
        result["error"] = "Ping timed out"
    except Exception as e:
        result["error"] = str(e)
    
    return result

def check_ffprobe_available() -> bool:
    """Check if ffprobe is available on the system"""
    try:
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def test_with_ffprobe(url: str, timeout: int) -> Dict:
    """Test RTSP stream with FFprobe for detailed information"""
    results = {
        "success": False,
        "errors": [],
        "codec": "unknown",
        "resolution": "unknown",
        "stream_info": {}
    }
    
    try:
        # Command to get stream information
        cmd = [
            "ffprobe",
            "-v", "warning",
            "-show_entries", "stream=width,height,codec_name,codec_long_name",
            "-of", "default=noprint_wrappers=1",
            "-rtsp_transport", "tcp",   # Force TCP for better reliability
            "-stimeout", "5000000",     # 5 seconds timeout in microseconds
            "-i", url
        ]
        
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, text=True)
        stderr = proc.stderr
        stdout = proc.stdout
        
        if proc.returncode != 0:
            # Check for specific error patterns
            if "401 Unauthorized" in stderr:
                results["errors"].append("Authentication failed (401 Unauthorized)")
                results["authentication_success"] = False
            elif "Connection refused" in stderr:
                results["errors"].append("Connection refused - check if port is correct and open")
            elif "Immediate exit requested" in stderr:
                results["errors"].append("RTSP server disconnected immediately")
            elif "Unknown error occurred" in stderr:
                results["errors"].append("Unknown server error")
            else:
                results["errors"].append(f"FFprobe error: {stderr.strip()}")
            return results
        
        # Parse successful output
        if "codec_name=" in stdout:
            codec_match = re.search(r'codec_name=(\w+)', stdout)
            if codec_match:
                results["codec"] = codec_match.group(1)
        
        width_match = re.search(r'width=(\d+)', stdout)
        height_match = re.search(r'height=(\d+)', stdout)
        if width_match and height_match:
            width = width_match.group(1)
            height = height_match.group(1)
            results["resolution"] = f"{width}x{height}"
            results["stream_info"]["width"] = int(width)
            results["stream_info"]["height"] = int(height)
        
        # If we got here, connection was successful
        results["success"] = True
        
    except subprocess.TimeoutExpired:
        results["errors"].append(f"FFprobe timed out after {timeout} seconds")
    except Exception as e:
        results["errors"].append(f"Error testing with FFprobe: {str(e)}")
    
    return results

def test_with_opencv(url: str, timeout: int) -> Dict:
    """Test RTSP stream with OpenCV"""
    results = {
        "success": False,
        "errors": [],
        "frames_received": 0,
        "resolution": "unknown"
    }
    
    # Run in a separate thread with timeout
    thread_result = {}
    
    def _opencv_test_thread():
        try:
            # Set some special options for RTSP
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp|stimeout;5000000"
            
            cap = cv2.VideoCapture(url)
            if not cap.isOpened():
                thread_result["error"] = "Failed to open stream"
                return
            
            # Try to read some frames
            frames_received = 0
            start_time = time.time()
            max_duration = min(timeout, 5)  # Don't run longer than timeout or 5 seconds
            
            while time.time() - start_time < max_duration:
                ret, frame = cap.read()
                if ret:
                    frames_received += 1
                    if frames_received == 1:
                        # Get resolution from first frame
                        height, width = frame.shape[:2]
                        thread_result["resolution"] = f"{width}x{height}"
                        thread_result["width"] = width
                        thread_result["height"] = height
                else:
                    # If we failed to read a frame after receiving some, break
                    if frames_received > 0:
                        break
                    time.sleep(0.1)
            
            cap.release()
            thread_result["frames_received"] = frames_received
            thread_result["success"] = frames_received > 0
            
        except Exception as e:
            thread_result["error"] = str(e)
            thread_result["success"] = False
    
    # Start thread and wait for it
    thread = threading.Thread(target=_opencv_test_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    # Check results
    if thread.is_alive():
        # Thread is still running, timeout occurred
        results["errors"].append(f"OpenCV test timed out after {timeout} seconds")
        return results
    
    # Get results from thread
    results["success"] = thread_result.get("success", False)
    results["frames_received"] = thread_result.get("frames_received", 0)
    
    if "resolution" in thread_result:
        results["resolution"] = thread_result["resolution"]
    
    if "error" in thread_result:
        results["errors"].append(thread_result["error"])
    
    return results

def generate_recommendations(results: Dict) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    # Authentication issues
    if any("401 Unauthorized" in err for err in results.get("errors", [])):
        recommendations.append("Check username and password in the RTSP URL")
        recommendations.append("Verify that the user has permission to access this camera")
    
    # Connection issues
    if not results.get("connection_success", False):
        recommendations.append("Verify the camera IP address is correct")
        recommendations.append("Check if the RTSP port (usually 554) is open on the camera")
        recommendations.append("Ensure there are no firewalls blocking the connection")
    
    # Stream format issues
    if results.get("connection_success", False) and not results.get("stream_received", False):
        recommendations.append("The camera may not support the requested stream format")
        recommendations.append("Try a different stream path (e.g., /stream, /live, /h264, etc.)")
    
    # General recommendations
    if not results.get("host_reachable", True):
        recommendations.append("The camera IP address is not responding to ping")
        recommendations.append("Check if the camera is powered on and connected to the network")
    
    # If no specific recommendations, give general advice
    if not recommendations:
        recommendations.append("Try accessing the camera through its web interface to verify it's working")
        recommendations.append("Check the camera's documentation for the correct RTSP URL format")
        recommendations.append("Try restarting the camera")
    
    return recommendations

def fix_rtsp_url(url: str) -> str:
    """
    Attempt to fix common issues with RTSP URLs
    
    Args:
        url: RTSP URL to fix
        
    Returns:
        Fixed URL or original if no fix needed
    """
    # Already correct format
    if url.startswith("rtsp://"):
        # Extract components
        parts = parse_rtsp_url(url)
        
        # Check for common issues
        if "port" not in parts and ":" not in parts["host"]:
            # Add default port if missing
            host_part = url.split("@")[-1].split("/")[0]
            if ":" not in host_part:
                url = url.replace(host_part, f"{host_part}:554")
        
        return url
    
    # Try to fix URL format
    if "://" not in url:
        # Assume it's missing the protocol
        return f"rtsp://{url}"
    
    # Unknown format, return as-is
    return url