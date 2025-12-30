"""
Detection Processor Module
Handles detection processing, top-N tracking, and file saving
"""

import os
import csv
import time
import heapq
import math
from pathlib import Path
import cv2


class DetectionProcessor:
    """
    Processes detections, maintains top-N heap, and saves flagged frames
    """
    
    def __init__(self, output_dir, flagged_dir, log_csv, top_n=20, 
                 max_entries_per_person=50, save_gap_seconds=2):
        """
        Initialize detection processor
        
        Args:
            output_dir: Path object for output directory
            flagged_dir: Path object for flagged frames directory
            log_csv: Path object for CSV log file
            top_n: Number of top detections to keep
            max_entries_per_person: Maximum saved frames per student
            save_gap_seconds: Minimum seconds between saves for same student
        """
        self.output_dir = Path(output_dir)
        self.flagged_dir = Path(flagged_dir)
        self.log_csv = Path(log_csv)
        self.top_n = top_n
        self.max_entries_per_person = max_entries_per_person
        self.save_gap_seconds = save_gap_seconds
        
        # Top-N heap: stores tuples (conf, uid, data_dict)
        self.top_heap = []
        self.top_uid = 0
        self.saved_files = {}  # uid -> {paths: [...], rolls: [...]}
        self.person_entries = {}  # roll -> list of {uid, timestamp, filepath, conf}
        
        # Initialize directories and CSV
        self._initialize_output()
    
    def _initialize_output(self):
        """Create output directories and CSV file if needed"""
        self.output_dir.mkdir(exist_ok=True)
        self.flagged_dir.mkdir(parents=True, exist_ok=True)
        
        if not self.log_csv.exists():
            with open(self.log_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "frame_file", "source_info", 
                    "student_name", "student_roll", "conf_score", 
                    "bbox_center_x", "bbox_center_y"
                ])
    
    def get_top_count(self):
        """Get current number of top detections saved"""
        return len(self.top_heap)
    
    def process_detection(self, det, frame_bgr, mapper, src_name, frame_idx):
        """
        Process a single detection: find nearest students and consider for top-N
        
        Args:
            det: Detection dictionary with keys x1, y1, x2, y2, conf
            frame_bgr: BGR frame image (numpy array)
            mapper: CoordinateMapper instance
            src_name: Source name/description
            frame_idx: Frame index
            
        Returns:
            List of (student, detection) tuples that were flagged
        """
        conf = float(det.get("conf", 0.0))
        
        # Calculate bbox center and diagonal
        w = det["x2"] - det["x1"]
        h = det["y2"] - det["y1"]
        bbox_diag = math.hypot(w, h)
        max_dist = bbox_diag * 1.2
        
        cx = int((det["x1"] + det["x2"]) / 2)
        cy = int((det["y1"] + det["y2"]) / 2)
        
        # Find nearest students
        nearest = mapper.nearest_n_students(cx, cy, n=2, max_distance=max_dist)
        
        if not nearest:
            return []
        
        # Determine which rolls are eligible for saving
        now_ts = time.time()
        eligible_rolls = []
        
        for roll, dist in nearest:
            entries = self.person_entries.get(roll, [])
            
            # Check time gap
            if entries and (now_ts - entries[-1]["timestamp"] < self.save_gap_seconds):
                continue
            
            # Check max entries
            if len(entries) >= self.max_entries_per_person:
                continue
            
            eligible_rolls.append(roll)
        
        # If no eligible rolls, skip
        if not eligible_rolls:
            if nearest:
                print(f"[INFO] Detection for rolls {nearest} skipped due to save_gap or max_entries")
            return []
        
        # Consider for top-N heap
        self._consider_top_candidate(det, frame_bgr, src_name, frame_idx, eligible_rolls, mapper, now_ts)
        
        # Return flagged students for UI display
        flagged = []
        for roll in eligible_rolls:
            stu = mapper.mapped_student_objects.get(roll)
            if stu:
                flagged.append((stu, det))
        
        return flagged
    
    def _consider_top_candidate(self, det, frame_bgr, src_name, frame_idx, eligible_rolls, mapper, now_ts):
        """Consider detection as candidate for top-N heap"""
        conf = float(det.get("conf", 0.0))
        
        # If heap not full, push new candidate
        if len(self.top_heap) < self.top_n:
            uid = self._new_uid()
            heapq.heappush(self.top_heap, (conf, uid))
            
            # Save per-student files
            saved_paths = []
            for roll in eligible_rolls:
                path = self._save_detection_for_roll(frame_bgr, det, roll, uid, mapper)
                if path:
                    saved_paths.append(path)
                    # Record in per-person list
                    self.person_entries.setdefault(roll, []).append({
                        "uid": uid,
                        "timestamp": now_ts,
                        "filepath": str(path),
                        "conf": conf
                    })
            
            self.saved_files[uid] = {"paths": saved_paths, "rolls": eligible_rolls}
            
            # Log entries
            self._log_detection_entries(det, src_name, frame_idx, eligible_rolls, saved_paths, mapper)
            return
        
        # Heap full: check if this candidate beats the smallest
        smallest_conf, smallest_uid = self.top_heap[0]
        if conf > smallest_conf:
            # Pop smallest
            _, popped_uid = heapq.heappop(self.top_heap)
            
            # Delete files for popped detection
            self._remove_saved_uid(popped_uid)
            
            # Push new candidate
            uid = self._new_uid()
            heapq.heappush(self.top_heap, (conf, uid))
            
            saved_paths = []
            for roll in eligible_rolls:
                path = self._save_detection_for_roll(frame_bgr, det, roll, uid, mapper)
                if path:
                    saved_paths.append(path)
                    self.person_entries.setdefault(roll, []).append({
                        "uid": uid,
                        "timestamp": now_ts,
                        "filepath": str(path),
                        "conf": conf
                    })
            
            self.saved_files[uid] = {"paths": saved_paths, "rolls": eligible_rolls}
            self._log_detection_entries(det, src_name, frame_idx, eligible_rolls, saved_paths, mapper)
    
    def _new_uid(self):
        """Generate new unique ID"""
        self.top_uid += 1
        return self.top_uid
    
    def _save_detection_for_roll(self, frame_bgr, det, roll, uid, mapper):
        """
        Save detection frame for a specific student
        
        Returns:
            Path to saved file or None on failure
        """
        try:
            stu = mapper.mapped_student_objects.get(roll)
            if not stu:
                return None
            
            # Create per-student folder
            safe_name = f"{stu.name.replace(' ', '_')}_{stu.roll}"
            person_dir = self.flagged_dir / safe_name
            person_dir.mkdir(parents=True, exist_ok=True)
            
            # Create filename
            ts = int(time.time())
            fname = person_dir / f"top_{uid}_{safe_name}_{ts}.jpg"
            
            # Create image with bbox
            img_copy = frame_bgr.copy()
            x1 = int(det.get("x1", 0))
            y1 = int(det.get("y1", 0))
            x2 = int(det.get("x2", img_copy.shape[1] - 1))
            y2 = int(det.get("y2", img_copy.shape[0] - 1))
            
            # Clamp to image bounds
            h, w = img_copy.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)
            
            # Draw bbox and label
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"Cheating {det.get('conf', 0.0) * 100:.1f}%"
            cv2.putText(img_copy, label, (x1, max(12, y1 - 6)), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Save file
            success = cv2.imwrite(str(fname), img_copy)
            if not success:
                print(f"[ERROR] cv2.imwrite failed for {fname}")
                return None
            
            return fname
        except Exception as ex:
            print(f"[ERROR] _save_detection_for_roll exception: {ex}")
            return None
    
    def _remove_saved_uid(self, uid):
        """Remove files and entries for given uid"""
        try:
            info = self.saved_files.get(uid)
            if not info:
                return
            
            paths = info.get("paths", [])
            rolls = info.get("rolls", [])
            
            # Delete files
            for p in paths:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            
            # Remove from person_entries
            for roll in rolls:
                entries = self.person_entries.get(roll, [])
                new_list = [e for e in entries if e.get("uid") != uid]
                if new_list:
                    self.person_entries[roll] = new_list
                else:
                    self.person_entries.pop(roll, None)
            
            # Remove from saved_files
            self.saved_files.pop(uid, None)
        except Exception as ex:
            print(f"[ERROR] _remove_saved_uid: {ex}")
    
    def _log_detection_entries(self, det, src_name, frame_idx, rolls, frame_file_paths, mapper):
        """Log detection entries to CSV"""
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for i, roll in enumerate(rolls):
                stu = mapper.mapped_student_objects.get(roll)
                if not stu:
                    continue
                
                frame_path = frame_file_paths[i] if i < len(frame_file_paths) else ""
                cx = int((det["x1"] + det["x2"]) / 2)
                cy = int((det["y1"] + det["y2"]) / 2)
                
                writer.writerow([
                    ts, str(frame_path), f"{src_name}@{frame_idx}",
                    stu.name, stu.roll, det.get("conf", 0.0), cx, cy
                ])
    
    def save_sample_detection(self, frame_bgr, detections, mapper):
        """
        Save a sampled frame with detections (not part of top-N)
        
        Returns:
            Tuple of (save_path, flagged_list) where flagged_list is [(student, det), ...]
        """
        save_path = self.flagged_dir / f"flagged_sample_{int(time.time())}.jpg"
        
        # Find flagged students
        flagged = []
        for det in detections:
            w = det["x2"] - det["x1"]
            h = det["y2"] - det["y1"]
            bbox_diag = math.hypot(w, h)
            max_dist = bbox_diag * 1.2
            
            cx = int((det["x1"] + det["x2"]) / 2)
            cy = int((det["y1"] + det["y2"]) / 2)
            nearest = mapper.nearest_n_students(cx, cy, n=2, max_distance=max_dist)
            
            for roll, dist in nearest:
                stu = mapper.mapped_student_objects.get(roll)
                if stu:
                    flagged.append((stu, det))
        
        # Save image with boxes
        img_copy = frame_bgr.copy()
        for det in detections:
            x1, y1, x2, y2 = int(det["x1"]), int(det["y1"]), int(det["x2"]), int(det["y2"])
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(img_copy, f"Cheating {det.get('conf', 0.0) * 100:.1f}%", 
                       (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        cv2.imwrite(str(save_path), img_copy)
        
        # Log entries
        with open(self.log_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for stu, det in flagged:
                cx = int((det["x1"] + det["x2"]) / 2)
                cy = int((det["y1"] + det["y2"]) / 2)
                writer.writerow([
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    str(save_path),
                    "sample",
                    stu.name,
                    stu.roll,
                    det.get("conf", 0.0),
                    cx,
                    cy
                ])
        
        return save_path, flagged    
    def get_flagged_students_summary(self, mapper):
        """
        Get summary of flagged students with frame counts
        
        Returns:
            Dictionary {roll: {'name': str, 'count': int}}
        """
        flagged_summary = {}
        
        for roll, entries in self.person_entries.items():
            if entries:  # Only include students with at least one flagged frame
                stu = mapper.mapped_student_objects.get(roll)
                if stu:
                    flagged_summary[roll] = {
                        'name': stu.name,
                        'count': len(entries)
                    }
        
        return flagged_summary