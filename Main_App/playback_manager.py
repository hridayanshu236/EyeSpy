"""
Playback Manager Module
Handles video/camera playback in a separate thread
"""

import threading
import time
import queue
import cv2
from pathlib import Path


class PlaybackManager:
    """Manages video/camera playback and frame queue"""
    
    def __init__(self, frame_queue_size=4):
        """
        Initialize playback manager
        
        Args:
            frame_queue_size: Maximum size of frame queue
        """
        self.playback_thread = None
        self.playback_stop = threading.Event()
        self.playback_pause = threading.Event()
        self.frame_queue = queue.Queue(maxsize=frame_queue_size)
        
        self.source_path = None
        self.is_running = False
    
    def start_playback(self, source_type, source_path, detector=None, conf_thresh=0.3):
        """
        Start playback from source
        
        Args:
            source_type: Type of source (video_file, video_folder, camera)
            source_path: Path to source or camera index
            detector: CheatDetector instance for running detection
            conf_thresh: Confidence threshold for detection
        """
        if self.playback_thread and self.playback_thread.is_alive():
            # Already running, just resume
            self.playback_pause.clear()
            return True
        
        # Reset controls
        self.playback_stop.clear()
        self.playback_pause.clear()
        self.source_path = source_path
        
        # Start worker thread
        self.playback_thread = threading.Thread(
            target=self._playback_worker,
            args=(source_type, source_path, detector, conf_thresh),
            daemon=True
        )
        self.playback_thread.start()
        self.is_running = True
        return True
    
    def toggle_pause(self):
        """Toggle pause state"""
        if not self.playback_thread or not self.playback_thread.is_alive():
            return False
        
        if not self.playback_pause.is_set():
            self.playback_pause.set()
            return True  # Now paused
        else:
            self.playback_pause.clear()
            return False  # Now playing
    
    def stop_playback(self):
        """Stop playback gracefully"""
        if not self.playback_thread:
            return
        
        self.playback_stop.set()
        self.playback_pause.clear()
        self.is_running = False
    
    def terminate_playback(self):
        """Aggressively terminate playback"""
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_stop.set()
            self.playback_pause.clear()
        self.is_running = False
    
    def get_frame(self):
        """
        Get next frame from queue (non-blocking)
        
        Returns:
            Tuple of (frame, src_name, frame_idx, detections) or None
        """
        try:
            if not self.frame_queue.empty():
                return self.frame_queue.get_nowait()
        except queue.Empty:
            pass
        return None
    
    def clear_queue(self):
        """Clear the frame queue"""
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
    
    def _playback_worker(self, source_type, source_path, detector, conf_thresh):
        """
        Worker thread: reads frames and runs detection
        
        Args:
            source_type: Type of source
            source_path: Path to source
            detector: CheatDetector instance
            conf_thresh: Confidence threshold
        """
        cap = None
        files_iter = []
        
        # Prepare capture objects based on source type
        if source_type == "video_file":
            cap = cv2.VideoCapture(str(source_path))
            files_iter = [(str(source_path), cap)]
        elif source_type == "video_folder":
            p = Path(source_path)
            vids = [x for x in p.iterdir() if x.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]]
            if not vids:
                return
            files_iter = [(str(v), cv2.VideoCapture(str(v))) for v in vids]
        elif source_type == "camera":
            cap = cv2.VideoCapture(int(source_path))
            files_iter = [("camera", cap)]
        else:
            return
        
        # Process each video source
        for src_name, cap_obj in files_iter:
            if self.playback_stop.is_set():
                break
            
            cap = cap_obj
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            delay = 1.0 / fps
            frame_idx = 0
            
            while cap.isOpened() and not self.playback_stop.is_set():
                # Handle pause
                if self.playback_pause.is_set():
                    time.sleep(0.15)
                    continue
                
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_idx += 1
                
                # Run detection if detector provided
                detections = []
                if detector:
                    try:
                        detections = detector.detect_frame(frame, conf_thresh=conf_thresh)
                    except Exception as e:
                        print(f"Detection error: {e}")
                        detections = []
                
                # Push frame to queue (non-blocking)
                try:
                    if not self.frame_queue.full():
                        self.frame_queue.put((frame.copy(), src_name, frame_idx, detections))
                except Exception as e:
                    print(f"Queue error: {e}")
                
                # Pacing to match video FPS
                time.sleep(max(0.001, delay * 0.5))
            
            # Release per-file capture
            try:
                cap.release()
            except Exception:
                pass
            
            if self.playback_stop.is_set():
                break
        
        self.is_running = False


class FrameSampler:
    """Helper class for sampling single frames from various sources"""
    
    @staticmethod
    def sample_from_image_folder(folder_path):
        """
        Sample a random image from folder
        
        Returns:
            Tuple of (frame, info_dict) or (None, {})
        """
        import random
        p = Path(folder_path)
        images = [x for x in p.iterdir() if x.suffix.lower() in [".jpg", ".jpeg", ".png", ".bmp"]]
        if not images:
            return None, {}
        
        chosen = random.choice(images)
        img = cv2.imread(str(chosen))
        return img, {"source_type": "image_folder", "source_desc": str(chosen)}
    
    @staticmethod
    def sample_from_video_folder(folder_path):
        """
        Sample a random frame from a random video in folder
        
        Returns:
            Tuple of (frame, info_dict) or (None, {})
        """
        import random
        p = Path(folder_path)
        vids = [x for x in p.iterdir() if x.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]]
        if not vids:
            return None, {}
        
        chosen = random.choice(vids)
        return FrameSampler._sample_from_video(chosen)
    
    @staticmethod
    def sample_from_video_file(video_path):
        """
        Sample a random frame from video file
        
        Returns:
            Tuple of (frame, info_dict) or (None, {})
        """
        return FrameSampler._sample_from_video(video_path)
    
    @staticmethod
    def _sample_from_video(video_path):
        """Internal helper to sample from a video file"""
        import random
        cap = cv2.VideoCapture(str(video_path))
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        
        if total <= 0:
            ret, frm = cap.read()
            cap.release()
            if not ret:
                return None, {}
            return frm, {"source_type": "video", "source_desc": str(video_path)}
        
        idx = random.randint(0, max(0, total - 1))
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frm = cap.read()
        cap.release()
        
        if not ret:
            return None, {}
        
        return frm, {"source_type": "video", "source_desc": f"{video_path} @frame {idx}"}
    
    @staticmethod
    def sample_from_camera(camera_index):
        """
        Sample a frame from camera
        
        Returns:
            Tuple of (frame, info_dict) or (None, {})
        """
        cap = cv2.VideoCapture(int(camera_index))
        if not cap.isOpened():
            cap.release()
            raise RuntimeError("Cannot open camera")
        
        frame = None
        # Read a few frames to let camera stabilize
        for i in range(10):
            ret, frm = cap.read()
            if not ret:
                break
            frame = frm
        
        cap.release()
        
        if frame is None:
            return None, {}
        
        return frame, {"source_type": "camera", "source_desc": f"camera_{camera_index}_frame10"}
