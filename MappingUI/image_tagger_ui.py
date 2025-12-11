import os
import random
import csv
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image
import cv2
import numpy as np
import threading
import queue
import heapq
import shutil
import math
from Mapper import CoordinateMapper
from canvas_manager import CanvasManager
from list_manager import ListManager
from dialogs import AddStudentDialog, prompt_edit_student
from file_manager import save_mapper_dialog, load_mapper_dialog, import_students_from_csv
from export_csv import export_students_to_csv
from Student import Student
from cheat_detector import CheatDetector

# UI constants
APP_FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 11, "bold")

OUTPUT_DIR = Path("output")
FLAGGED_DIR = OUTPUT_DIR / "flagged_frames"
LOG_CSV = OUTPUT_DIR / "flagged_log.csv"
WEIGHTS_DEFAULT = "./weights/bestone.pt"

# Top-N to keep
TOP_N = 20

class ImageTaggerUI:
    def __init__(self, image_path=None):
        self.mapper = CoordinateMapper()

        self.root = tk.Tk()
        self.root.title("Cheating Detection")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 650)
        self.max_entries_per_person = 50   # number of saved frames per student (change as needed)
        self.save_gap_seconds = 2        # minimum seconds between saved frames for the same student
        self.person_entries = {} 

        # current image/frame (image coords)
        self.current_frame_bgr = None   # numpy BGR of currently sampled/frame
        self.current_frame_pil = None

        # detector & settings
        self.detector = None
        self.model_path = WEIGHTS_DEFAULT
        self.conf_thresh = tk.DoubleVar(value=0.30)

        # playback controls
        self.playback_thread = None
        self.playback_stop = threading.Event()
        self.playback_pause = threading.Event()  # when set -> paused
        self.frame_queue = queue.Queue(maxsize=4)  # frames from reader -> main thread (display)
        self.result_queue = queue.Queue(maxsize=8)  # detection results for processing

        # top-n heap: store tuples (conf, uid, data_dict)
        self.top_heap = []
        self.top_uid = 0
        self.saved_files = {}  # uid -> filepath

        # UI components
        self.paned = tk.PanedWindow(self.root, sashrelief=tk.RAISED, sashwidth=6)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4,8))

        # Left: canvas
        self.canvas_frame = tk.Frame(self.paned, bd=1, relief=tk.SOLID)
        self.paned.add(self.canvas_frame, minsize=600)

        # Right: controls
        self.right_frame = tk.Frame(self.paned, bd=1, relief=tk.FLAT, width=380)
        self.paned.add(self.right_frame, minsize=300)

        # Placeholder image
        if image_path and os.path.isfile(image_path):
            pil = Image.open(image_path)
        else:
            pil = Image.new("RGB", (800, 600), color=(200,200,200))
        self.canvas_manager = CanvasManager(self.canvas_frame, pil, fit_within=(1000,800))
        self.canvas_manager.bind_left_click(self._on_canvas_left_click_display)
        self.canvas_manager.bind_right_click(self._on_canvas_right_click_display)

        list_container = tk.Frame(self.right_frame, padx=10, pady=10)
        list_container.pack(fill=tk.BOTH, expand=True)
        self.list_manager = ListManager(list_container)

        self._build_controls()

        self.status_bar = tk.Label(self.root, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Segoe UI", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self._bind_shortcuts()

        # directories
        OUTPUT_DIR.mkdir(exist_ok=True)
        FLAGGED_DIR.mkdir(parents=True, exist_ok=True)
        if not LOG_CSV.exists():
            with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "frame_file", "source_info", "student_name", "student_roll", "conf_score", "bbox_center_x", "bbox_center_y"])

        # schedule GUI polling for frame/result queues
        self.root.after(30, self._poll_queues)

    def _build_controls(self):
        # (student management, file ops omitted here — copy from earlier version)
        counts_frame = tk.Frame(self.right_frame, padx=10, pady=6)
        counts_frame.pack(fill=tk.X)
        self.counts_label = tk.Label(counts_frame, text="Unmapped: 0 | Mapped: 0", font=("Segoe UI", 9))
        self.counts_label.pack(side=tk.RIGHT)

        ctrl_frame = tk.Frame(self.right_frame, padx=10, pady=6)
        ctrl_frame.pack(fill=tk.X)

        # Search/filter on unmapped
        search_frame = tk.Frame(ctrl_frame)
        search_frame.pack(fill=tk.X, pady=(2,8))
        tk.Label(search_frame, text="Search Unmapped:", font=APP_FONT).pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=APP_FONT)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8,0))
        search_entry.bind("<KeyRelease>", lambda e: self._apply_unmapped_filter())
        tk.Button(search_frame, text="Clear", command=self._clear_search, font=("Segoe UI",9)).pack(side=tk.LEFT, padx=6)

        # Student management buttons
        group_frame = tk.Frame(self.right_frame, padx=10, pady=6)
        group_frame.pack(fill=tk.X)
        tk.Label(group_frame, text="Student Management", font=TITLE_FONT).pack(anchor="w")
        btn_frame = tk.Frame(group_frame)
        btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(btn_frame, text="➕ Add Student", command=self.open_add_student_dialog, bg="#90EE90", font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="✏️ Edit Student", command=self.edit_student_ui, bg="#FFD700", font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="🗑️ Remove Student", command=self.remove_student_ui, bg="#FFA07A", font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        # mapping tools
        tk.Label(group_frame, text="Mapping Tools", font=TITLE_FONT).pack(anchor="w", pady=(8,0))
        map_btn_frame = tk.Frame(group_frame)
        map_btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(map_btn_frame, text="🔄 Clear All Mappings", command=self.clear_all_mappings, bg="#DC143C", fg="white", font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(map_btn_frame, text="🧾 Remove Selected Mapping", command=self.remove_selected_mapping, bg="#FFA500", font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        # file ops
        tk.Label(group_frame, text="File Operations", font=TITLE_FONT).pack(anchor="w", pady=(8,0))
        file_btn_frame = tk.Frame(group_frame)
        file_btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(file_btn_frame, text="💾 Save Project", bg="#87CEEB", command=self.save_data, font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(file_btn_frame, text="📂 Load Project", bg="#87CEEB", command=self.load_data, font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(file_btn_frame, text="📥 Add from CSV", bg="#ADD8E6", command=self.import_from_csv, font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(file_btn_frame, text="📤 Export CSV", bg="#98FB98", command=self.export_to_csv, font=APP_FONT).pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        # detection controls
        tk.Label(self.right_frame, text="Cheating Detection & Playback", font=TITLE_FONT).pack(anchor="w", padx=10, pady=(8,0))
        model_frame = tk.Frame(self.right_frame, padx=10, pady=6)
        model_frame.pack(fill=tk.X)

        mp_frame = tk.Frame(model_frame)
        mp_frame.pack(fill=tk.X, pady=(2,4))
        tk.Label(mp_frame, text="Weights:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.model_path_var = tk.StringVar(value=self.model_path)
        tk.Entry(mp_frame, textvariable=self.model_path_var, font=("Segoe UI",9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6,6))
        tk.Button(mp_frame, text="Load", command=self._load_detector, font=("Segoe UI",9)).pack(side=tk.LEFT)

        ct_frame = tk.Frame(model_frame)
        ct_frame.pack(fill=tk.X)
        tk.Label(ct_frame, text="Conf Threshold:", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        tk.Spinbox(ct_frame, from_=0.05, to=1.0, increment=0.05, textvariable=self.conf_thresh, format="%.2f", width=6).pack(side=tk.LEFT, padx=(6,0))

        src_frame = tk.Frame(model_frame)
        src_frame.pack(fill=tk.X, pady=(8,4))
        self.source_type = tk.StringVar(value="video_file")
        tk.Radiobutton(src_frame, text="Image Folder", variable=self.source_type, value="image_folder").grid(row=0, column=0, sticky="w")
        tk.Radiobutton(src_frame, text="Video Folder", variable=self.source_type, value="video_folder").grid(row=0, column=1, sticky="w")
        tk.Radiobutton(src_frame, text="Video File", variable=self.source_type, value="video_file").grid(row=1, column=0, sticky="w")
        tk.Radiobutton(src_frame, text="Camera (realtime)", variable=self.source_type, value="camera").grid(row=1, column=1, sticky="w")

        act_frame = tk.Frame(model_frame)
        act_frame.pack(fill=tk.X, pady=(6,4))
        tk.Button(act_frame, text="Select Path", command=self._select_source_path, font=("Segoe UI",9)).pack(side=tk.LEFT, padx=2)
        tk.Button(act_frame, text="Sample Frame", command=self._sample_frame_once, font=("Segoe UI",9)).pack(side=tk.LEFT, padx=2)
        tk.Button(act_frame, text="Detect On Sample", command=self._detect_on_sample, bg="#FF6B6B", font=("Segoe UI",9)).pack(side=tk.LEFT, padx=2)

        # playback controls for video/camera
        play_frame = tk.Frame(model_frame)
        play_frame.pack(fill=tk.X, pady=(6,4))
        tk.Button(play_frame, text="▶ Play", command=self._start_playback, bg="#90EE90").pack(side=tk.LEFT, padx=2)
        tk.Button(play_frame, text="⏸ Pause", command=self._toggle_pause, bg="#FFD700").pack(side=tk.LEFT, padx=2)
        tk.Button(play_frame, text="⏹ Stop", command=self._stop_playback, bg="#FFA07A").pack(side=tk.LEFT, padx=2)
        tk.Button(play_frame, text="Terminate Stream", command=self._terminate_playback, bg="#DC143C", fg="white").pack(side=tk.LEFT, padx=2)

        self.source_label = tk.Label(self.right_frame, text="Source: (not selected)", anchor="w", fg="gray")
        self.source_label.pack(fill=tk.X, padx=12)

        # small info about top-n saved
        self.topn_label = tk.Label(self.right_frame, text=f"Top saved detections: {len(self.top_heap)}/{TOP_N}", anchor="w", fg="blue")
        self.topn_label.pack(fill=tk.X, padx=12, pady=(4,0))

    # ----- Shortcuts -----
    def _bind_shortcuts(self):
        self.root.bind_all("<Control-s>", lambda e: self.save_data())
        self.root.bind_all("<Control-o>", lambda e: self.load_data())
        self.root.bind_all("<Control-i>", lambda e: self.import_from_csv())
        self.root.bind_all("<Control-n>", lambda e: self.open_add_student_dialog())
        self.root.bind_all("<Control-e>", lambda e: self.export_to_csv())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected_mapping())

    # ----- Detector helpers -----
    def _load_detector(self):
        path = self.model_path_var.get().strip()
        if not path:
            messagebox.showerror("Error", "Please provide a path to the weights file.")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Error", f"Weights file not found: {path}")
            return
        try:
            self.detector = CheatDetector(path)
            self.status_bar.config(text=f"Loaded model: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model:\n{e}")
            self.detector = None

    def _select_source_path(self):
        st = self.source_type.get()
        if st == "image_folder":
            path = filedialog.askdirectory(title="Select Image Folder")
            if path:
                self.source_path = path
                self.source_label.config(text=f"Source: Image Folder -> {path}")
        elif st == "video_folder":
            path = filedialog.askdirectory(title="Select Video Folder")
            if path:
                self.source_path = path
                self.source_label.config(text=f"Source: Video Folder -> {path}")
        elif st == "video_file":
            path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video files","*.mp4 *.mov *.avi *.mkv"),("All files","*.*")])
            if path:
                self.source_path = path
                self.source_label.config(text=f"Source: Video File -> {path}")
        elif st == "camera":
            idx = simpledialog.askinteger("Camera Index", "Enter camera index (default 0):", initialvalue=0, parent=self.root)
            if idx is None:
                return
            self.source_path = int(idx)
            self.source_label.config(text=f"Source: Camera index -> {idx}")

    # ----- Sampling one-off frame (image/video folder or camera) -----
    def _sample_frame_once(self):
        st = self.source_type.get()
        if not hasattr(self, "source_path") or self.source_path is None:
            messagebox.showerror("Error", "Select source path/index first")
            return

        try:
            res = self._fetch_single_frame(st, self.source_path)

            # res should be a tuple (frame, info). Handle None or (None, ...)
            if not res or res[0] is None:
                messagebox.showinfo("No Frame", "Could not sample a frame from the selected source.")
                return

            frame, info = res

            # set the sampled frame into the UI
            self._set_current_frame(frame, info)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to sample frame:\n{e}")
            return


    def _fetch_single_frame(self, st, source):
        if st == "image_folder":
            p = Path(source)
            images = [x for x in p.iterdir() if x.suffix.lower() in [".jpg",".jpeg",".png",".bmp"]]
            if not images:
                return None, {}
            chosen = random.choice(images)
            img = cv2.imread(str(chosen))
            return img, {"source_type":"image_folder","source_desc":str(chosen)}
        elif st == "video_folder":
            p = Path(source)
            vids = [x for x in p.iterdir() if x.suffix.lower() in [".mp4",".avi",".mov",".mkv"]]
            if not vids:
                return None, {}
            chosen = random.choice(vids)
            cap = cv2.VideoCapture(str(chosen))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if total <= 0:
                ret, frm = cap.read()
                cap.release()
                if not ret:
                    return None, {}
                return frm, {"source_type":"video_folder","source_desc":str(chosen)}
            idx = random.randint(0, max(0, total-1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frm = cap.read()
            cap.release()
            if not ret:
                return None, {}
            return frm, {"source_type":"video_folder","source_desc":f"{chosen} @frame {idx}"}
        elif st == "video_file":
            chosen = Path(source)
            cap = cv2.VideoCapture(str(chosen))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
            if total <= 0:
                ret, frm = cap.read()
                cap.release()
                if not ret:
                    return None, {}
                return frm, {"source_type":"video_file","source_desc":str(chosen)}
            idx = random.randint(0, max(0, total-1))
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frm = cap.read()
            cap.release()
            if not ret:
                return None, {}
            return frm, {"source_type":"video_file","source_desc":f"{chosen} @frame {idx}"}
        elif st == "camera":
            cap = cv2.VideoCapture(int(source))
            if not cap.isOpened():
                cap.release()
                raise RuntimeError("Cannot open camera")
            frame = None
            for i in range(10):
                ret, frm = cap.read()
                if not ret:
                    break
                frame = frm
            cap.release()
            if frame is None:
                return None, {}
            return frame, {"source_type":"camera","source_desc":f"camera_{source}_frame10"}
        return None, {}
    
    def _update_topn_label(self): 
        """Update the UI label that shows how many top detections are saved.""" 
        try: self.topn_label.config(text=f"Top saved detections: {len(self.top_heap)}/{TOP_N}")
        except Exception: print("")

    def _set_current_frame(self, frame_bgr, info):
        self.current_frame_bgr = frame_bgr.copy()
        self.current_frame_pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        self.current_frame_info = info
        # update canvas with current frame (scaled to fit)
        self.canvas_manager.set_image(self.current_frame_pil, fit_within=(1000,800))
        self.canvas_manager.redraw_all_markers(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        self.status_bar.config(text=f"Sampled frame from {info.get('source_type')}: {info.get('source_desc')}")

    def _detect_on_sample(self):
        if self.current_frame_bgr is None:
            messagebox.showerror("Error", "Please sample a frame first")
            return
        if self.detector is None:
            path = self.model_path_var.get().strip()
            if not path or not os.path.isfile(path):
                messagebox.showerror("Error", "Model not loaded or invalid path")
                return
            self.detector = CheatDetector(path)
        conf = float(self.conf_thresh.get())
        dets = self.detector.detect_frame(self.current_frame_bgr, conf_thresh=conf)
        if not dets:
            messagebox.showinfo("No detections", "No cheating detections found")
            return
        # draw on canvas (display)
        self.canvas_manager.draw_detections(dets, color="red")
        # flag nearest students and save only bounding boxes image (no markers)
        flagged = []
        for det in dets:
            # bounding box size
            w = det["x2"] - det["x1"]
            h = det["y2"] - det["y1"]

            bbox_diag = math.hypot(w, h)

            # Distance threshold = 1.2 × diagonal of bbox
            max_dist = bbox_diag * 1.2
            cx = int((det["x1"] + det["x2"]) / 2)
            cy = int((det["y1"] + det["y2"]) / 2)
            nearest = self.mapper.nearest_n_students(cx, cy, n=2, max_distance=max_dist)

            for roll, dist in nearest:
                stu = self.mapper.mapped_student_objects.get(roll)
                if stu:
                    flagged.append((stu, det))
                    # also show flags on canvas (visual only)
                    sx, sy = self.mapper.mapped_students.get(roll)
                    self.canvas_manager.draw_flag_for_student(sx, sy, stu.name, color="orange")
        # For sampled frame we save immediately as it is not part of streaming top-n
        save_path = FLAGGED_DIR / f"flagged_sample_{int(time.time())}.jpg"
        # Save image with only boxes + labels
        img_copy = self.current_frame_bgr.copy()
        for det in dets:
            x1,y1,x2,y2 = int(det["x1"]),int(det["y1"]),int(det["x2"]),int(det["y2"])
            cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 2)
            cv2.putText(img_copy, f"Cheating {det.get('conf',0.0)*100:.1f}%", (x1, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        cv2.imwrite(str(save_path), img_copy)
        # log entries for each flagged student
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for stu, det in flagged:
                writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), str(save_path), str(self.current_frame_info), stu.name, stu.roll, det.get("conf",0.0), int((det["x1"]+det["x2"])/2), int((det["y1"]+det["y2"])/2)])
        messagebox.showinfo("Saved", f"Saved flagged frame: {save_path}")

    # ----- Playback (video/camera) management -----
    def _start_playback(self):
        if not hasattr(self, "source_path") or self.source_path is None:
            messagebox.showerror("Error", "Select source first")
            return
        if self.playback_thread and self.playback_thread.is_alive():
            # already running
            self.playback_pause.clear()
            self.status_bar.config(text="Resuming playback")
            return
        # reset controls
        self.playback_stop.clear()
        self.playback_pause.clear()
        st = self.source_type.get()
        self.playback_thread = threading.Thread(target=self._playback_worker, args=(st, self.source_path), daemon=True)
        self.playback_thread.start()
        self.status_bar.config(text="Playback started")

    def _toggle_pause(self):
        if not self.playback_thread or not self.playback_thread.is_alive():
            return
        if not self.playback_pause.is_set():
            self.playback_pause.set()
            self.status_bar.config(text="Playback paused")
        else:
            self.playback_pause.clear()
            self.status_bar.config(text="Playback resumed")

    def _stop_playback(self):
        if not self.playback_thread:
            return
        self.playback_stop.set()
        self.playback_pause.clear()
        self.status_bar.config(text="Playback stopping...")

    def _terminate_playback(self):
        # aggressive termination
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_stop.set()
            self.playback_pause.clear()
        self.status_bar.config(text="Playback terminated by user")

    def _playback_worker(self, st, source):
        """
        Worker thread: reads frames from selected source and puts them into frame_queue.
        Also runs detector inline (to reduce queue switching) and puts detection results into result_queue.
        """
        cap = None 
        files_iter = [] 
        if st == "video_file":
            cap = cv2.VideoCapture(str(source))
            files_iter = [(str(source), cap)]
        elif st == "video_folder":
            p = Path(source)
            vids = [x for x in p.iterdir() if x.suffix.lower() in [".mp4",".avi",".mov",".mkv"]]
            if not vids:
                self.status_bar.config(text="No videos in folder")
                return
            files_iter = []
            for v in vids:
                files_iter.append((str(v), cv2.VideoCapture(str(v))))
        elif st == "camera":
            cap = cv2.VideoCapture(int(source))
            files_iter = [("camera", cap)]
        else:
            # unsupported for playback
            self.status_bar.config(text="Playback only supports video_file/video_folder/camera")
            return

        # ensure detector loaded
        if self.detector is None:
            path = self.model_path_var.get().strip()
            if not path or not os.path.isfile(path):
                self.status_bar.config(text="Detector not loaded or invalid path")
                return
            self.detector = CheatDetector(path)

        conf_thresh = float(self.conf_thresh.get())

        for src_name, cap_obj in files_iter:
            if self.playback_stop.is_set():
                break
            cap = cap_obj
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            delay = 1.0 / fps
            frame_idx = 0
            while cap.isOpened() and not self.playback_stop.is_set():
                if self.playback_pause.is_set():
                    time.sleep(0.15)
                    continue
                ret, frame = cap.read()
                if not ret:
                    break
                frame_idx += 1
                # run detection on frame (blocking here — heavy)
                try:
                    detections = self.detector.detect_frame(frame, conf_thresh=conf_thresh)
                except Exception as e:
                    detections = []
                # process detections: find nearest students and create entries
                if detections:
                    for det in detections:
                        cx = int((det["x1"]+det["x2"])/2)
                        cy = int((det["y1"]+det["y2"])/2)
                        nearest = self.mapper.nearest_n_students(cx, cy, n=2)
                        # if any mapped students found, create flagged log records
                        if nearest:
                            # store candidate for top-n (use det['conf'])
                            self._consider_top_candidate(det, frame.copy(), src_name, frame_idx, nearest)
                            # also draw flags on canvas later when frame displayed (but saved frame will have only boxes)
                # push frame and detections for display in main thread (non-blocking)
                try:
                    if not self.frame_queue.full():
                        self.frame_queue.put((frame.copy(), src_name, frame_idx, detections))
                except Exception:
                    pass
                # pacing
                time.sleep(max(0.001, delay * 0.5))  # small sleep to allow GUI updates
            # release per-file capture
            try:
                cap.release()
            except Exception:
                pass
            if self.playback_stop.is_set():
                break

        self.status_bar.config(text="Playback worker completed")
        # mark thread finished
        
    def _save_detection_for_roll(self, frame_bgr, det, roll, uid):
        """
        Save a copy of the detection frame containing only bbox+label into the student's folder.
        Returns the saved pathlib.Path or None on failure.
        """
        try:
            stu = self.mapper.mapped_student_objects.get(roll)
            if not stu:
                return None

            # Create per-student folder: NAME_ROLL (safe filename)
            safe_name = f"{stu.name.replace(' ', '_')}_{stu.roll}"
            person_dir = FLAGGED_DIR / safe_name
            person_dir.mkdir(parents=True, exist_ok=True)

            # prepare filename
            ts = int(time.time())
            fname = person_dir / f"top_{uid}_{safe_name}_{ts}.jpg"

            # create image with only bbox (single bbox here)
            img_copy = frame_bgr.copy()
            x1 = int(det.get("x1", 0))
            y1 = int(det.get("y1", 0))
            x2 = int(det.get("x2", img_copy.shape[1] - 1))
            y2 = int(det.get("y2", img_copy.shape[0] - 1))

            # clamp coordinates to image bounds
            h, w = img_copy.shape[:2]
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w - 1, x2), min(h - 1, y2)

            # draw bbox and label
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), (0, 0, 255), 2)
            label = f"Cheating {det.get('conf', 0.0) * 100:.1f}%"
            cv2.putText(img_copy, label, (x1, max(12, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            # Write directly and check success
            success = cv2.imwrite(str(fname), img_copy)
            if not success:
                print(f"[ERROR] cv2.imwrite failed for {fname}")
                return None

            return fname
        except Exception as ex:
            print(f"[ERROR] _save_detection_for_roll exception: {ex}")
            return None

    def _remove_saved_uid(self, uid):
        """
        Remove files recorded for uid and remove corresponding entries from person_entries.
        """
        try:
            info = self.saved_files.get(uid)
            if not info:
                return
            paths = info.get("paths", [])
            rolls = info.get("rolls", [])
            # delete files
            for p in paths:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            # remove entries from person_entries lists matching this uid
            for roll in rolls:
                entries = self.person_entries.get(roll, [])
                new_list = [e for e in entries if e.get("uid") != uid]
                if new_list:
                    self.person_entries[roll] = new_list
                else:
                    # remove key if empty
                    self.person_entries.pop(roll, None)
            # remove from saved_files mapping
            self.saved_files.pop(uid, None)
        except Exception:
            pass

    def _consider_top_candidate(self, det, frame_bgr, src_name, frame_idx, nearest):
        conf = float(det.get("conf", 0.0))
        now_ts = time.time()

        # Determine which rolls are eligible (respecting max_entries_per_person & time gap)
        eligible_rolls = []
        for roll, dist in nearest:
            entries = self.person_entries.get(roll, [])

            # skip if too soon
            if entries and (now_ts - entries[-1]["timestamp"] < self.save_gap_seconds):
                continue

            # skip if reached max
            if len(entries) >= self.max_entries_per_person:
                continue

            eligible_rolls.append(roll)

        # NEW: if nearest students exist but none eligible → LOG WHY
        if nearest and not eligible_rolls:
            print(f"[INFO] Detection for rolls {nearest} skipped due to save_gap or max_entries")
            return

        # If heap not full, push new candidate (store conf and uid)
        if len(self.top_heap) < TOP_N:
            uid = self._new_uid()
            heapq.heappush(self.top_heap, (conf, uid))
            # Save per-student files and record
            saved_paths = []
            for roll in eligible_rolls:
                path = self._save_detection_for_roll(frame_bgr, det, roll, uid)
                if path:
                    saved_paths.append(path)
                    # record in per-person list
                    self.person_entries.setdefault(roll, []).append({
                        "uid": uid,
                        "timestamp": now_ts,
                        "filepath": str(path),
                        "conf": conf
                    })
            self.saved_files[uid] = {"paths": saved_paths, "rolls": eligible_rolls}
            # log entries
            self._log_detection_entries(det, frame_bgr, src_name, frame_idx, eligible_rolls, saved_paths)
            self._update_topn_label()
            return

        # Heap full: check if this candidate beats the smallest
        smallest_conf, smallest_uid = self.top_heap[0]
        if conf > smallest_conf:
            # pop smallest
            _, popped_uid = heapq.heappop(self.top_heap)
            # delete saved files for popped_uid and remove entries from person_entries
            self._remove_saved_uid(popped_uid)
            # push new candidate
            uid = self._new_uid()
            heapq.heappush(self.top_heap, (conf, uid))
            saved_paths = []
            for roll in eligible_rolls:
                path = self._save_detection_for_roll(frame_bgr, det, roll, uid)
                if path:
                    saved_paths.append(path)
                    self.person_entries.setdefault(roll, []).append({
                        "uid": uid,
                        "timestamp": now_ts,
                        "filepath": str(path),
                        "conf": conf
                    })
            self.saved_files[uid] = {"paths": saved_paths, "rolls": eligible_rolls}
            self._log_detection_entries(det, frame_bgr, src_name, frame_idx, eligible_rolls, saved_paths)
            self._update_topn_label()

    def _new_uid(self):
        self.top_uid += 1
        return self.top_uid

    def _save_detection_frame(self, frame_bgr, detections, out_path):
        """
        Save image with only detection bounding boxes and labels as requested (no student markers).
        """
        img_copy = frame_bgr.copy()
        for det in detections:
            x1,y1,x2,y2 = int(det["x1"]),int(det["y1"]),int(det["x2"]),int(det["y2"])
            cv2.rectangle(img_copy, (x1,y1), (x2,y2), (0,0,255), 2)
            cv2.putText(img_copy, f"Cheating {det.get('conf',0.0)*100:.1f}%", (x1, y1-6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)
        cv2.imwrite(str(out_path), img_copy)

    def _log_detection_entries(self, det, frame_bgr, src_name, frame_idx, rolls, frame_file_paths):
        """
        Log entries to LOG_CSV for each student (roll) and the corresponding saved frame path.
        rolls: list of roll strings
        frame_file_paths: list of saved file paths in same order as rolls
        """
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for i, roll in enumerate(rolls):
                stu = self.mapper.mapped_student_objects.get(roll)
                if not stu:
                    continue
                frame_path = frame_file_paths[i] if i < len(frame_file_paths) else ""
                writer.writerow([ts, str(frame_path), f"{src_name}@{frame_idx}", stu.name, stu.roll, det.get("conf",0.0), int((det["x1"]+det["x2"])/2), int((det["y1"]+det["y2"])/2)])

    def _poll_queues(self):
        """
        Poll the frame_queue to display the most recent frame; overlay detection boxes and flags.
        """
        try:
            while not self.frame_queue.empty():
                frame, src_name, frame_idx, detections = self.frame_queue.get_nowait()
                self.current_frame_bgr = frame
                self.current_frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                self.canvas_manager.set_image(self.current_frame_pil, fit_within=(1000,800))
                # draw detections and flags
                if detections:
                    self.canvas_manager.draw_detections(detections, color="red")
                    # for each detection, find nearest mapped students and draw flags on canvas (visual)
                    for det in detections:
                        cx = int((det["x1"]+det["x2"])/2)
                        cy = int((det["y1"]+det["y2"])/2)
                        nearest = self.mapper.nearest_n_students(cx, cy, n=2)
                        for roll, dist in nearest:
                            stu = self.mapper.mapped_student_objects.get(roll)
                            if stu:
                                sx, sy = self.mapper.mapped_students.get(roll)
                                self.canvas_manager.draw_flag_for_student(sx, sy, stu.name, color="orange")
                # redraw mapped markers so they remain visible
                self.canvas_manager.redraw_all_markers(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        except Exception:
            pass
        # schedule next poll
        self.root.after(30, self._poll_queues)

    # ----- Click handlers from canvas (display coords) -----
    def _on_canvas_left_click_display(self, dx, dy):
        # Convert display coords to image coords before mapping
        ix, iy = self.canvas_manager.display_to_image(dx, dy)
        # map selected unmapped student if any selected in list
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Select an unmapped student in the list to map at this position.")
            return
        stu = self.mapper.unmapped_students[idx]
        # map using image coords (store original-image coordinates)
        self.mapper.map_student(ix, iy, stu)
        self._apply_unmapped_filter()
        self.list_manager.populate_mapped(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        # draw marker using image coords (CanvasManager draws with scaling)
        self.canvas_manager.draw_marker(ix, iy, stu.name)
        self._update_counts()
        self.status_bar.config(text=f"Mapped: {stu.name} at ({int(ix)},{int(iy)}) [image coords]")

    def _on_canvas_right_click_display(self, dx, dy):
        # right-click -> unmap nearest student (convert to image coords)
        ix, iy = self.canvas_manager.display_to_image(dx, dy)
        nearest_roll = self.mapper.nearest_student(ix, iy)
        if nearest_roll:
            stu = self.mapper.mapped_student_objects.get(nearest_roll)
            if stu and messagebox.askyesno("Unmap", f"Unmap {stu.name} ({stu.roll})?"):
                self.mapper.unmap_student(nearest_roll)
                self.refresh_views()
                self.status_bar.config(text=f"Unmapped: {stu.name}")

    # ----- Add/Edit/Remove/Other UI functions (reused from previous version) -----
    def open_add_student_dialog(self):
        AddStudentDialog(self.root, self._on_student_added)

    def _on_student_added(self, student):
        if self.mapper.get_student_by_roll(student.roll):
            messagebox.showerror("Error", f"Roll number '{student.roll}' already exists.")
            return
        self.mapper.add_student(student)
        self._apply_unmapped_filter()
        self._update_counts()
        self.status_bar.config(text=f"Added student: {student.name} ({student.roll})")

    def edit_student_ui(self):
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a student to edit from the Unmapped list.")
            return
        stu = self.mapper.unmapped_students[idx]
        res = prompt_edit_student(self.root, stu)
        if not res:
            return
        name, dept, roll = res
        existing = self.mapper.get_student_by_roll(roll)
        if existing and existing.roll != stu.roll:
            messagebox.showerror("Error", f"Roll number '{roll}' already exists.")
            return
        stu.name, stu.department, stu.roll = name, dept, roll
        self._apply_unmapped_filter()
        self.status_bar.config(text=f"Updated student: {stu.name}")

    def remove_student_ui(self):
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a student to remove from the Unmapped list.")
            return
        stu = self.mapper.unmapped_students[idx]
        if messagebox.askyesno("Confirm Delete", f"Remove student '{stu.name}' ({stu.roll})?"):
            self.mapper.unmapped_students.pop(idx)
            self._apply_unmapped_filter()
            self.status_bar.config(text=f"Removed student: {stu.name}")
            self._update_counts()

    def import_from_csv(self):
        parsed_students, path = import_students_from_csv(self.root)
        if parsed_students is None:
            return
        added = 0
        skipped_duplicates = 0
        for stu in parsed_students:
            if self.mapper.get_student_by_roll(stu.roll):
                skipped_duplicates += 1
                continue
            self.mapper.add_student(stu)
            added += 1
        self._apply_unmapped_filter()
        self._update_counts()
        summary = f"Imported: {added}. Skipped duplicates: {skipped_duplicates}. From: {path}"
        self.status_bar.config(text=summary)
        messagebox.showinfo("Import Complete", summary, parent=self.root)

    def export_to_csv(self):
        path = export_students_to_csv(self.mapper, self.root)
        if path:
            self.status_bar.config(text=f"Exported to: {path}")

    def remove_selected_mapping(self):
        idx = self.list_manager.get_selected_mapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a mapped student to remove.")
            return
        roll = self.list_manager.get_mapped_roll_at(idx)
        if not roll:
            messagebox.showerror("Error", "Could not determine roll for selected mapping.")
            return
        stu = self.mapper.mapped_student_objects.get(roll)
        if not stu:
            messagebox.showerror("Error", "Selected mapping does not correspond to a known student.")
            return
        if not messagebox.askyesno("Remove Mapping", f"Remove mapping for {stu.name} ({stu.roll})?"):
            return
        self.mapper.unmap_student(roll)
        self.refresh_views()
        self.status_bar.config(text=f"Removed mapping: {stu.name} ({stu.roll})")
        self._update_counts()

    def clear_all_mappings(self):
        if not self.mapper.mapped_students:
            messagebox.showinfo("Info", "No mappings to clear.")
            return
        if not messagebox.askyesno("Confirm Clear", "Clear all mappings? This will move all mapped students back to unmapped."):
            return
        self.mapper.clear_mappings()
        self.refresh_views()
        self.status_bar.config(text="All mappings cleared")
        messagebox.showinfo("Cleared", "All mappings have been removed.", parent=self.root)

    def refresh_views(self):
        self.list_manager.populate_unmapped(self.mapper.unmapped_students)
        self.list_manager.populate_mapped(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        self.canvas_manager.redraw_all_markers(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        self._update_counts()

    def _apply_unmapped_filter(self):
        query = self.search_var.get().strip().lower()
        if not query:
            self.list_manager.populate_unmapped(self.mapper.unmapped_students)
        else:
            filtered = [s for s in self.mapper.unmapped_students if query in s.name.lower() or query in s.roll.lower() or query in s.department.lower()]
            self.list_manager.populate_unmapped(filtered)

    def _clear_search(self):
        self.search_var.set("")
        self._apply_unmapped_filter()

    def _update_counts(self):
        unmapped = len(self.mapper.unmapped_students)
        mapped = len(self.mapper.mapped_students)
        try:
            self.counts_label.config(text=f"Unmapped: {unmapped} | Mapped: {mapped}")
        except Exception:
            self.status_bar.config(text=f"Unmapped: {unmapped} | Mapped: {mapped}")

    # ----- File operations -----
    def save_data(self):
        path = save_mapper_dialog(self.mapper, self.root)
        if path:
            self.status_bar.config(text=f"Project saved to: {path}")

    def load_data(self):
        mapper_obj, path = load_mapper_dialog(self.root)
        if not mapper_obj:
            return
        if isinstance(mapper_obj, CoordinateMapper):
            self.mapper = mapper_obj
            self.refresh_views()
            self.status_bar.config(text=f"Project loaded from: {path}")
            messagebox.showinfo("Loaded", "Project loaded successfully.", parent=self.root)
        else:
            messagebox.showerror("Error", "Loaded file does not contain a mapper instance.", parent=self.root)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = ImageTaggerUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")