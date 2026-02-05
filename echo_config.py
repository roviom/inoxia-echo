"""
Echo Archery Detection System - Configuration
Version: 1.0
"""

import os

# ============================================
# SYSTEM CONFIGURATION
# ============================================

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DIR = os.path.join(BASE_DIR, 'sessions')

# Web server settings
WEB_HOST = '0.0.0.0'  # Listen on all interfaces
WEB_PORT = 80
DEBUG = False

# Ensure session directory exists
os.makedirs(SESSION_DIR, exist_ok=True)

# ============================================
# CAMERA CONFIGURATION
# ============================================

# Camera resolution (width, height)
# Higher resolution = better accuracy but slower processing
CAMERA_RESOLUTION = (1920, 1080)  # Full HD

# Camera frame rate
CAMERA_FPS = 10

# Camera rotation (0, 90, 180, 270)
CAMERA_ROTATION = 0

# Auto-exposure and white balance
CAMERA_AUTO_EXPOSURE = True
CAMERA_AUTO_WHITE_BALANCE = True

# ============================================
# TARGET SPECIFICATIONS
# ============================================

# Supported target sizes (in centimeters)
TARGET_SIZES = {
    '80cm': {
        'diameter': 80,
        'rings': [
            {'score': 10, 'radius_cm': 4.0, 'color': 'gold'},
            {'score': 9, 'radius_cm': 8.0, 'color': 'gold'},
            {'score': 8, 'radius_cm': 16.0, 'color': 'red'},
            {'score': 7, 'radius_cm': 24.0, 'color': 'red'},
            {'score': 6, 'radius_cm': 32.0, 'color': 'blue'},
            {'score': 5, 'radius_cm': 40.0, 'color': 'blue'},
        ]
    },
    '122cm': {
        'diameter': 122,
        'rings': [
            {'score': 10, 'radius_cm': 6.1, 'color': 'gold'},
            {'score': 9, 'radius_cm': 12.2, 'color': 'gold'},
            {'score': 8, 'radius_cm': 24.4, 'color': 'red'},
            {'score': 7, 'radius_cm': 36.6, 'color': 'red'},
            {'score': 6, 'radius_cm': 48.8, 'color': 'blue'},
            {'score': 5, 'radius_cm': 61.0, 'color': 'blue'},
        ]
    }
}

# Default target size
DEFAULT_TARGET_SIZE = '122cm'

# ============================================
# DETECTION PARAMETERS
# ============================================

# Arrow detection sensitivity
# Higher = more sensitive but more false positives
DETECTION_THRESHOLD = 25  # 0-255, pixel difference threshold

# Minimum contour area for arrow detection (pixels)
MIN_ARROW_AREA = 100

# Maximum contour area (to filter out large changes)
MAX_ARROW_AREA = 50000

# Minimum distance between arrows (cm) to be considered separate
MIN_ARROW_DISTANCE_CM = 3.0

# Detection cooldown (seconds) - ignore changes this soon after detection
DETECTION_COOLDOWN = 1.0

# Frame differencing: number of frames to average for stable reference
REFERENCE_FRAME_AVERAGING = 5

# Motion detection: minimum frames with change before triggering
MIN_CHANGE_FRAMES = 2

# ============================================
# CIRCLE DETECTION (Hough Transform)
# ============================================

# Hough Circle parameters for target ring detection
HOUGH_DP = 1.2              # Inverse ratio of accumulator resolution
HOUGH_MIN_DIST = 100        # Minimum distance between circle centers
HOUGH_PARAM1 = 50          # Canny edge detector threshold
HOUGH_PARAM2 = 30          # Accumulator threshold
HOUGH_MIN_RADIUS = 50      # Minimum circle radius (pixels)
HOUGH_MAX_RADIUS = 800     # Maximum circle radius (pixels)

# ============================================
# IMAGE PROCESSING
# ============================================

# Gaussian blur kernel size (must be odd)
BLUR_KERNEL_SIZE = 5

# Morphological operations
MORPH_KERNEL_SIZE = 3
MORPH_ITERATIONS = 2

# Canny edge detection
CANNY_THRESHOLD1 = 50
CANNY_THRESHOLD2 = 150

# ============================================
# CALIBRATION
# ============================================

# Number of calibration frames to capture
CALIBRATION_FRAMES = 10

# Acceptable circle detection tolerance (pixels)
CIRCLE_DETECTION_TOLERANCE = 20

# Minimum confidence for automatic calibration (0.0-1.0)
MIN_CALIBRATION_CONFIDENCE = 0.7

# ============================================
# PERFORMANCE
# ============================================

# Maximum frames to keep in memory
MAX_FRAME_BUFFER = 30

# Image downscaling for faster processing (1.0 = no scaling)
PROCESSING_SCALE = 0.5  # Process at half resolution for speed

# Enable GPU acceleration if available
USE_GPU = False  # Set to True if OpenCV compiled with CUDA

# ============================================
# LOGGING
# ============================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# Log file location
LOG_FILE = os.path.join(BASE_DIR, 'echo.log')

# Maximum log file size (bytes)
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB

# Number of backup log files
LOG_BACKUP_COUNT = 3

# ============================================
# SESSION MANAGEMENT
# ============================================

# Auto-save session interval (seconds)
AUTO_SAVE_INTERVAL = 10

# Session file format
SESSION_FILE_FORMAT = 'json'  # json or csv

# Maximum sessions to keep
MAX_SESSIONS = 100

# ============================================
# ADVANCED SETTINGS
# ============================================

# Perspective correction
ENABLE_PERSPECTIVE_CORRECTION = True

# Sub-pixel accuracy for arrow detection
ENABLE_SUBPIXEL_ACCURACY = True

# Multi-threading for processing
ENABLE_THREADING = True
MAX_WORKER_THREADS = 2

# Arrow color detection (experimental)
ENABLE_COLOR_DETECTION = False
ARROW_COLORS = ['red', 'blue', 'yellow', 'green', 'black', 'white']

# ============================================
# SAFETY & VALIDATION
# ============================================

# Maximum arrows to track per session
MAX_ARROWS_PER_SESSION = 1000

# Validate arrow positions (reject impossible positions)
VALIDATE_POSITIONS = True

# Maximum arrow speed (cm/frame) - reject if faster (likely false positive)
MAX_ARROW_SPEED = 50.0

# ============================================
# WEB INTERFACE
# ============================================

# Refresh rate for live view (milliseconds)
WEB_REFRESH_RATE = 1000

# Show camera preview in web interface
SHOW_CAMERA_PREVIEW = True

# Preview image quality (1-100)
PREVIEW_QUALITY = 80

# Preview image size
PREVIEW_SIZE = (640, 480)

# ============================================
# DEBUGGING
# ============================================

# Save debug images
SAVE_DEBUG_IMAGES = False
DEBUG_IMAGE_DIR = os.path.join(BASE_DIR, 'debug_images')

if SAVE_DEBUG_IMAGES:
    os.makedirs(DEBUG_IMAGE_DIR, exist_ok=True)

# Show detection visualization
SHOW_DETECTION_OVERLAY = True

# Print timing information
SHOW_TIMING_INFO = False
