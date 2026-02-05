"""
Echo Archery Detection System - Arrow Detector
Computer vision engine for detecting arrow positions
"""

import cv2
import numpy as np
import time
import logging
from datetime import datetime
import config

logger = logging.getLogger(__name__)


class ArrowDetector:
    """Detects arrows and calculates their positions on target"""
    
    def __init__(self, target_size='122cm'):
        """
        Initialize arrow detector
        
        Args:
            target_size (str): Target size ('80cm' or '122cm')
        """
        self.target_size = target_size
        self.target_config = config.TARGET_SIZES[target_size]
        
        # Calibration data
        self.is_calibrated = False
        self.reference_frame = None
        self.target_center = None  # (x, y) in pixels
        self.target_radius = None  # radius in pixels
        self.pixels_per_cm = None  # conversion factor
        
        # Detection state
        self.arrows = []  # List of detected arrow positions
        self.last_detection_time = 0
        self.change_frame_count = 0
        
        logger.info(f"Arrow detector initialized for {target_size} target")
    
    def calibrate(self, frame):
        """
        Calibrate detector with empty target image
        
        Args:
            frame (numpy.ndarray): RGB image of empty target
        
        Returns:
            dict: Calibration results with status and detected parameters
        """
        logger.info("Starting calibration...")
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (config.BLUR_KERNEL_SIZE, config.BLUR_KERNEL_SIZE), 0)
            
            # Detect circles (target rings)
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=config.HOUGH_DP,
                minDist=config.HOUGH_MIN_DIST,
                param1=config.HOUGH_PARAM1,
                param2=config.HOUGH_PARAM2,
                minRadius=config.HOUGH_MIN_RADIUS,
                maxRadius=config.HOUGH_MAX_RADIUS
            )
            
            if circles is None or len(circles[0]) == 0:
                logger.error("No target circles detected in calibration image")
                return {
                    'success': False,
                    'message': 'No target detected. Ensure target is visible and well-lit.',
                    'circles_found': 0
                }
            
            # Find the largest circle (outermost ring)
            circles = np.round(circles[0, :]).astype(int)
            largest_circle = max(circles, key=lambda c: c[2])  # Max by radius
            
            center_x, center_y, radius = largest_circle
            
            # Calculate pixels per centimeter
            target_diameter_cm = self.target_config['diameter']
            pixels_per_cm = (radius * 2) / target_diameter_cm
            
            # Store calibration data
            self.target_center = (center_x, center_y)
            self.target_radius = radius
            self.pixels_per_cm = pixels_per_cm
            
            # Store reference frame for arrow detection
            self.reference_frame = gray.copy()
            
            self.is_calibrated = True
            
            logger.info(f"Calibration successful: center=({center_x}, {center_y}), "
                       f"radius={radius}px, scale={pixels_per_cm:.2f}px/cm")
            
            # Save debug image if enabled
            if config.SAVE_DEBUG_IMAGES:
                debug_frame = frame.copy()
                cv2.circle(debug_frame, (center_x, center_y), radius, (0, 255, 0), 3)
                cv2.circle(debug_frame, (center_x, center_y), 5, (255, 0, 0), -1)
                
                debug_path = f"{config.DEBUG_IMAGE_DIR}/calibration_{int(time.time())}.jpg"
                cv2.imwrite(debug_path, cv2.cvtColor(debug_frame, cv2.COLOR_RGB2BGR))
                logger.debug(f"Debug image saved: {debug_path}")
            
            return {
                'success': True,
                'message': 'Calibration successful',
                'center': (center_x, center_y),
                'radius': radius,
                'pixels_per_cm': pixels_per_cm,
                'circles_found': len(circles),
                'target_size': self.target_size
            }
            
        except Exception as e:
            logger.error(f"Calibration failed: {e}")
            return {
                'success': False,
                'message': f'Calibration error: {str(e)}',
                'circles_found': 0
            }
    
    def detect_arrows(self, frame):
        """
        Detect new arrows in the current frame
        
        Args:
            frame (numpy.ndarray): Current RGB image
        
        Returns:
            dict: Detection results with new arrows found
        """
        if not self.is_calibrated:
            return {
                'success': False,
                'message': 'Detector not calibrated',
                'new_arrows': []
            }
        
        # Check cooldown
        if time.time() - self.last_detection_time < config.DETECTION_COOLDOWN:
            return {
                'success': False,
                'message': 'Detection cooldown active',
                'new_arrows': []
            }
        
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
            
            # Compute difference from reference frame
            diff = cv2.absdiff(self.reference_frame, gray)
            
            # Apply threshold
            _, thresh = cv2.threshold(diff, config.DETECTION_THRESHOLD, 255, cv2.THRESH_BINARY)
            
            # Morphological operations to clean up
            kernel = np.ones((config.MORPH_KERNEL_SIZE, config.MORPH_KERNEL_SIZE), np.uint8)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=config.MORPH_ITERATIONS)
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=config.MORPH_ITERATIONS)
            
            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            new_arrows = []
            
            for contour in contours:
                area = cv2.contourArea(contour)
                
                # Filter by area
                if area < config.MIN_ARROW_AREA or area > config.MAX_ARROW_AREA:
                    continue
                
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)
                
                # Arrow shaft should be elongated
                aspect_ratio = max(w, h) / max(min(w, h), 1)
                if aspect_ratio < 2.0:  # Arrow should be at least 2:1 ratio
                    continue
                
                # Find the point closest to target center (arrow tip)
                # Reshape contour for distance calculation
                contour_points = contour.reshape(-1, 2)
                
                # Calculate distances to target center
                distances = np.sqrt(
                    (contour_points[:, 0] - self.target_center[0])**2 +
                    (contour_points[:, 1] - self.target_center[1])**2
                )
                
                # Arrow tip is the point closest to center
                tip_idx = np.argmin(distances)
                tip_x, tip_y = contour_points[tip_idx]
                
                # Convert pixel position to centimeters from center
                dx_px = tip_x - self.target_center[0]
                dy_px = tip_y - self.target_center[1]
                
                dx_cm = dx_px / self.pixels_per_cm
                dy_cm = dy_px / self.pixels_per_cm
                
                # Calculate distance and angle
                distance_cm = np.sqrt(dx_cm**2 + dy_cm**2)
                angle_rad = np.arctan2(dy_cm, dx_cm)
                angle_deg = np.degrees(angle_rad)
                
                # Normalize angle to 0-360
                if angle_deg < 0:
                    angle_deg += 360
                
                # Calculate score
                score = self._calculate_score(distance_cm)
                
                # Check if this is a new arrow (not too close to existing ones)
                if self._is_new_arrow(dx_cm, dy_cm):
                    arrow_data = {
                        'id': len(self.arrows) + len(new_arrows) + 1,
                        'x_cm': round(dx_cm, 2),
                        'y_cm': round(dy_cm, 2),
                        'distance_cm': round(distance_cm, 2),
                        'angle_deg': round(angle_deg, 1),
                        'score': score,
                        'timestamp': datetime.now().isoformat(),
                        'pixel_x': int(tip_x),
                        'pixel_y': int(tip_y)
                    }
                    
                    new_arrows.append(arrow_data)
                    logger.info(f"New arrow detected: {arrow_data}")
            
            # Add new arrows to collection
            if new_arrows:
                self.arrows.extend(new_arrows)
                self.last_detection_time = time.time()
                
                # Save debug image
                if config.SAVE_DEBUG_IMAGES:
                    self._save_debug_detection(frame, new_arrows)
            
            return {
                'success': True,
                'message': f'Found {len(new_arrows)} new arrow(s)',
                'new_arrows': new_arrows,
                'total_arrows': len(self.arrows)
            }
            
        except Exception as e:
            logger.error(f"Arrow detection failed: {e}")
            return {
                'success': False,
                'message': f'Detection error: {str(e)}',
                'new_arrows': []
            }
    
    def _calculate_score(self, distance_cm):
        """
        Calculate score based on distance from center
        
        Args:
            distance_cm (float): Distance from center in centimeters
        
        Returns:
            int: Score (0-10)
        """
        for ring in self.target_config['rings']:
            if distance_cm <= ring['radius_cm']:
                return ring['score']
        
        return 0  # Miss
    
    def _is_new_arrow(self, x_cm, y_cm):
        """
        Check if position represents a new arrow
        
        Args:
            x_cm (float): X position in cm
            y_cm (float): Y position in cm
        
        Returns:
            bool: True if this is a new arrow position
        """
        for arrow in self.arrows:
            dx = x_cm - arrow['x_cm']
            dy = y_cm - arrow['y_cm']
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < config.MIN_ARROW_DISTANCE_CM:
                return False  # Too close to existing arrow
        
        return True
    
    def _save_debug_detection(self, frame, new_arrows):
        """Save debug image with detected arrows marked"""
        debug_frame = frame.copy()
        
        # Draw target center and radius
        cv2.circle(debug_frame, self.target_center, self.target_radius, (0, 255, 0), 2)
        cv2.circle(debug_frame, self.target_center, 5, (0, 255, 0), -1)
        
        # Draw all arrows
        for arrow in self.arrows:
            pos = (arrow['pixel_x'], arrow['pixel_y'])
            cv2.circle(debug_frame, pos, 8, (255, 0, 0), -1)
            cv2.putText(debug_frame, str(arrow['id']), 
                       (pos[0] + 15, pos[1]), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)
        
        # Highlight new arrows
        for arrow in new_arrows:
            pos = (arrow['pixel_x'], arrow['pixel_y'])
            cv2.circle(debug_frame, pos, 12, (0, 0, 255), 3)
        
        debug_path = f"{config.DEBUG_IMAGE_DIR}/detection_{int(time.time())}.jpg"
        cv2.imwrite(debug_path, cv2.cvtColor(debug_frame, cv2.COLOR_RGB2BGR))
    
    def get_all_arrows(self):
        """
        Get all detected arrows
        
        Returns:
            list: All arrow data
        """
        return self.arrows
    
    def get_statistics(self):
        """
        Calculate session statistics
        
        Returns:
            dict: Statistics including average, best, etc.
        """
        if not self.arrows:
            return {
                'total_arrows': 0,
                'total_score': 0,
                'average_score': 0,
                'average_distance': 0,
                'best_arrow': None
            }
        
        distances = [a['distance_cm'] for a in self.arrows]
        scores = [a['score'] for a in self.arrows]
        
        best_arrow = min(self.arrows, key=lambda a: a['distance_cm'])
        
        return {
            'total_arrows': len(self.arrows),
            'total_score': sum(scores),
            'average_score': round(np.mean(scores), 2),
            'average_distance': round(np.mean(distances), 2),
            'best_arrow': best_arrow,
            'worst_arrow': max(self.arrows, key=lambda a: a['distance_cm'])
        }
    
    def reset(self):
        """Reset all detected arrows"""
        self.arrows = []
        self.last_detection_time = 0
        logger.info("Arrow detection reset")
    
    def get_status(self):
        """
        Get detector status
        
        Returns:
            dict: Current detector state
        """
        return {
            'calibrated': self.is_calibrated,
            'target_size': self.target_size,
            'arrows_detected': len(self.arrows),
            'target_center': self.target_center,
            'target_radius': self.target_radius,
            'pixels_per_cm': self.pixels_per_cm
        }
