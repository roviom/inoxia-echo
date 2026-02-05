"""
Echo Archery Detection System - Main Application
Flask web server with automatic arrow detection
"""

import os
import sys
import time
import json
import logging
from logging.handlers import RotatingFileHandler
from threading import Thread, Event
from datetime import datetime
from flask import Flask, render_template, jsonify, request, Response
import cv2
import numpy as np

import config
from camera_manager import CameraManager
from detector import ArrowDetector

# Setup logging
def setup_logging():
    """Configure logging"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.MAX_LOG_SIZE,
        backupCount=config.LOG_BACKUP_COUNT
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

setup_logging()
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'echo-archery-2024'

# Global objects
camera_manager = None
detector = None
auto_detect_active = False
auto_detect_thread = None
auto_detect_event = Event()
session_start_time = None


def initialize_system():
    """Initialize camera and detector"""
    global camera_manager, detector, session_start_time
    
    try:
        logger.info("Initializing Echo system...")
        
        # Initialize camera
        camera_manager = CameraManager()
        
        # Test camera
        if not camera_manager.test_camera():
            raise Exception("Camera test failed")
        
        # Initialize detector with default target size
        detector = ArrowDetector(target_size=config.DEFAULT_TARGET_SIZE)
        
        session_start_time = datetime.now()
        
        logger.info("Echo system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        return False


def auto_detect_worker():
    """Background worker for automatic arrow detection"""
    global auto_detect_active
    
    logger.info("Auto-detection worker started")
    
    while auto_detect_active and not auto_detect_event.is_set():
        try:
            if detector and detector.is_calibrated:
                # Capture frame
                frame = camera_manager.capture_frame()
                
                if frame is not None:
                    # Detect arrows
                    result = detector.detect_arrows(frame)
                    
                    if result['success'] and result['new_arrows']:
                        logger.info(f"Auto-detected {len(result['new_arrows'])} new arrow(s)")
            
            # Wait before next detection
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            logger.error(f"Auto-detection error: {e}")
            time.sleep(1)
    
    logger.info("Auto-detection worker stopped")


# ============================================
# WEB ROUTES
# ============================================

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/status')
def api_status():
    """Get system status"""
    status = {
        'system': 'Echo Archery Detection v1.0',
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': (datetime.now() - session_start_time).total_seconds() if session_start_time else 0,
        'camera': camera_manager.get_camera_info() if camera_manager else {'status': 'not_initialized'},
        'detector': detector.get_status() if detector else {'calibrated': False},
        'auto_detect_active': auto_detect_active
    }
    
    if detector:
        status['statistics'] = detector.get_statistics()
    
    return jsonify(status)


@app.route('/api/calibrate', methods=['POST'])
def api_calibrate():
    """Calibrate detector with current view"""
    if not camera_manager or not detector:
        return jsonify({'success': False, 'message': 'System not initialized'}), 500
    
    try:
        # Get target size from request
        data = request.get_json() or {}
        target_size = data.get('target_size', config.DEFAULT_TARGET_SIZE)
        
        # Update detector target size if changed
        if target_size != detector.target_size:
            global detector
            detector = ArrowDetector(target_size=target_size)
            logger.info(f"Detector reconfigured for {target_size} target")
        
        # Capture calibration frame
        logger.info("Capturing calibration frame...")
        frame = camera_manager.capture_multiple_frames(config.CALIBRATION_FRAMES)
        
        if frame is None:
            return jsonify({'success': False, 'message': 'Failed to capture calibration frame'}), 500
        
        # Calibrate detector
        result = detector.calibrate(frame)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Calibration failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/detect', methods=['POST'])
def api_detect():
    """Manually trigger arrow detection"""
    if not camera_manager or not detector:
        return jsonify({'success': False, 'message': 'System not initialized'}), 500
    
    if not detector.is_calibrated:
        return jsonify({'success': False, 'message': 'Detector not calibrated'}), 400
    
    try:
        # Capture current frame
        frame = camera_manager.capture_frame()
        
        if frame is None:
            return jsonify({'success': False, 'message': 'Failed to capture frame'}), 500
        
        # Detect arrows
        result = detector.detect_arrows(frame)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/arrows')
def api_arrows():
    """Get all detected arrows"""
    if not detector:
        return jsonify({'success': False, 'message': 'System not initialized'}), 500
    
    arrows = detector.get_all_arrows()
    stats = detector.get_statistics()
    
    return jsonify({
        'success': True,
        'arrows': arrows,
        'statistics': stats
    })


@app.route('/api/auto-detect', methods=['POST'])
def api_auto_detect():
    """Toggle automatic arrow detection"""
    global auto_detect_active, auto_detect_thread
    
    if not detector or not detector.is_calibrated:
        return jsonify({'success': False, 'message': 'Detector not calibrated'}), 400
    
    data = request.get_json() or {}
    enable = data.get('enable', not auto_detect_active)
    
    if enable and not auto_detect_active:
        # Start auto-detection
        auto_detect_active = True
        auto_detect_event.clear()
        auto_detect_thread = Thread(target=auto_detect_worker, daemon=True)
        auto_detect_thread.start()
        logger.info("Auto-detection started")
        
        return jsonify({'success': True, 'message': 'Auto-detection started', 'active': True})
        
    elif not enable and auto_detect_active:
        # Stop auto-detection
        auto_detect_active = False
        auto_detect_event.set()
        if auto_detect_thread:
            auto_detect_thread.join(timeout=3)
        logger.info("Auto-detection stopped")
        
        return jsonify({'success': True, 'message': 'Auto-detection stopped', 'active': False})
    
    return jsonify({'success': True, 'active': auto_detect_active})


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset all detected arrows"""
    if not detector:
        return jsonify({'success': False, 'message': 'System not initialized'}), 500
    
    detector.reset()
    
    return jsonify({'success': True, 'message': 'All arrows reset'})


@app.route('/api/preview')
def api_preview():
    """Get current camera preview as JPEG"""
    if not camera_manager:
        return Response("Camera not initialized", status=500)
    
    try:
        frame = camera_manager.get_preview_frame()
        
        if frame is None:
            return Response("Failed to capture preview", status=500)
        
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Draw target overlay if calibrated
        if detector and detector.is_calibrated:
            # Scale coordinates to preview size
            scale_x = config.PREVIEW_SIZE[0] / config.CAMERA_RESOLUTION[0]
            scale_y = config.PREVIEW_SIZE[1] / config.CAMERA_RESOLUTION[1]
            
            center_x = int(detector.target_center[0] * scale_x)
            center_y = int(detector.target_center[1] * scale_y)
            radius = int(detector.target_radius * scale_x)
            
            # Draw target circle
            cv2.circle(frame_bgr, (center_x, center_y), radius, (0, 255, 0), 2)
            cv2.circle(frame_bgr, (center_x, center_y), 5, (0, 255, 0), -1)
            
            # Draw arrows
            for arrow in detector.get_all_arrows():
                arrow_x = int(arrow['pixel_x'] * scale_x)
                arrow_y = int(arrow['pixel_y'] * scale_y)
                cv2.circle(frame_bgr, (arrow_x, arrow_y), 6, (0, 0, 255), -1)
                cv2.putText(frame_bgr, str(arrow['id']), 
                           (arrow_x + 10, arrow_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Encode as JPEG
        _, jpeg = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, config.PREVIEW_QUALITY])
        
        return Response(jpeg.tobytes(), mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Preview generation failed: {e}")
        return Response("Preview error", status=500)


@app.route('/api/shutdown', methods=['POST'])
def api_shutdown():
    """Safely shutdown the system"""
    logger.info("Shutdown requested via API")
    
    # Stop auto-detection
    global auto_detect_active
    auto_detect_active = False
    auto_detect_event.set()
    
    # Close camera
    if camera_manager:
        camera_manager.close()
    
    # Trigger system shutdown
    def shutdown_system():
        time.sleep(2)  # Give time for response to be sent
        os.system('sudo shutdown -h now')
    
    Thread(target=shutdown_system, daemon=True).start()
    
    return jsonify({'success': True, 'message': 'System shutting down...'})


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Echo Archery Detection System Starting")
    logger.info("=" * 60)
    
    # Initialize system
    if not initialize_system():
        logger.error("Failed to initialize system. Exiting.")
        sys.exit(1)
    
    # Start Flask server
    logger.info(f"Starting web server on {config.WEB_HOST}:{config.WEB_PORT}")
    logger.info("Access web interface at: http://10.0.0.1")
    
    try:
        app.run(
            host=config.WEB_HOST,
            port=config.WEB_PORT,
            debug=config.DEBUG,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        if camera_manager:
            camera_manager.close()
        logger.info("Echo system stopped")
