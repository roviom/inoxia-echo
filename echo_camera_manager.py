"""
Echo Archery Detection System - Camera Manager
Handles Raspberry Pi Camera Module 3 interface
"""

import time
import logging
from threading import Lock
from picamera2 import Picamera2
from picamera2.configuration import CameraConfiguration
import numpy as np
import config

logger = logging.getLogger(__name__)


class CameraManager:
    """Manages the Raspberry Pi Camera Module 3"""
    
    def __init__(self):
        """Initialize camera manager"""
        self.camera = None
        self.lock = Lock()
        self.is_initialized = False
        self.current_frame = None
        self.frame_count = 0
        
        logger.info("Initializing camera manager...")
        self._init_camera()
    
    def _init_camera(self):
        """Initialize the camera hardware"""
        try:
            # Create Picamera2 instance
            self.camera = Picamera2()
            
            # Configure camera
            camera_config = self.camera.create_still_configuration(
                main={
                    "size": config.CAMERA_RESOLUTION,
                    "format": "RGB888"
                },
                buffer_count=2
            )
            
            self.camera.configure(camera_config)
            
            # Set camera controls
            controls = {}
            
            if config.CAMERA_AUTO_EXPOSURE:
                controls["AeEnable"] = True
            
            if config.CAMERA_AUTO_WHITE_BALANCE:
                controls["AwbEnable"] = True
            
            if controls:
                self.camera.set_controls(controls)
            
            # Start camera
            self.camera.start()
            
            # Allow camera to warm up
            time.sleep(2)
            
            self.is_initialized = True
            logger.info(f"Camera initialized successfully at {config.CAMERA_RESOLUTION}")
            
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.is_initialized = False
            raise
    
    def capture_frame(self):
        """
        Capture a single frame from the camera
        
        Returns:
            numpy.ndarray: RGB image array, or None if capture fails
        """
        if not self.is_initialized:
            logger.error("Camera not initialized")
            return None
        
        try:
            with self.lock:
                # Capture frame
                frame = self.camera.capture_array()
                
                # Apply rotation if configured
                if config.CAMERA_ROTATION == 90:
                    frame = np.rot90(frame, k=1)
                elif config.CAMERA_ROTATION == 180:
                    frame = np.rot90(frame, k=2)
                elif config.CAMERA_ROTATION == 270:
                    frame = np.rot90(frame, k=3)
                
                self.current_frame = frame.copy()
                self.frame_count += 1
                
                return frame
                
        except Exception as e:
            logger.error(f"Failed to capture frame: {e}")
            return None
    
    def capture_multiple_frames(self, count=5):
        """
        Capture multiple frames and return average
        
        Args:
            count (int): Number of frames to capture
        
        Returns:
            numpy.ndarray: Averaged frame, or None if capture fails
        """
        frames = []
        
        for i in range(count):
            frame = self.capture_frame()
            if frame is not None:
                frames.append(frame)
            time.sleep(0.1)  # Small delay between frames
        
        if not frames:
            return None
        
        # Average frames to reduce noise
        avg_frame = np.mean(frames, axis=0).astype(np.uint8)
        return avg_frame
    
    def get_preview_frame(self):
        """
        Get a lower-resolution preview frame
        
        Returns:
            numpy.ndarray: Preview image, or None if not available
        """
        if self.current_frame is None:
            self.capture_frame()
        
        if self.current_frame is None:
            return None
        
        # Resize to preview size
        import cv2
        preview = cv2.resize(
            self.current_frame,
            config.PREVIEW_SIZE,
            interpolation=cv2.INTER_AREA
        )
        
        return preview
    
    def get_camera_info(self):
        """
        Get camera information
        
        Returns:
            dict: Camera properties and settings
        """
        if not self.is_initialized:
            return {"status": "not_initialized"}
        
        try:
            # Get camera properties
            camera_props = self.camera.camera_properties
            
            info = {
                "status": "active",
                "model": camera_props.get("Model", "Unknown"),
                "resolution": config.CAMERA_RESOLUTION,
                "rotation": config.CAMERA_ROTATION,
                "frames_captured": self.frame_count,
                "auto_exposure": config.CAMERA_AUTO_EXPOSURE,
                "auto_white_balance": config.CAMERA_AUTO_WHITE_BALANCE
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_camera(self):
        """
        Test camera by capturing a test frame
        
        Returns:
            bool: True if camera is working, False otherwise
        """
        try:
            frame = self.capture_frame()
            if frame is not None and frame.size > 0:
                logger.info("Camera test successful")
                return True
            else:
                logger.error("Camera test failed: empty frame")
                return False
        except Exception as e:
            logger.error(f"Camera test failed: {e}")
            return False
    
    def close(self):
        """Clean up and close camera"""
        try:
            if self.camera is not None:
                self.camera.stop()
                self.camera.close()
                logger.info("Camera closed successfully")
        except Exception as e:
            logger.error(f"Error closing camera: {e}")
        
        self.is_initialized = False
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor"""
        self.close()
