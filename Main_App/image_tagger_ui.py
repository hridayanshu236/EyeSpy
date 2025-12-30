"""
Image Tagger UI - Refactored and Modular
Main application class for cheating detection system
"""

import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image
import cv2

# Import modular components
from Mapper import CoordinateMapper
from canvas_manager import CanvasManager
from list_manager import ListManager
from dialogs import AddStudentDialog, prompt_edit_student
from file_manager import save_mapper_dialog, load_mapper_dialog, import_students_from_csv
from export_csv import export_students_to_csv
from cheat_detector import CheatDetector

# Import new modular UI components
from ui_styles import COLORS, FONTS, WINDOW, CANVAS, SPACING
from ui_student_controls import StudentControlPanel, FileOperationsPanel
from ui_detection_controls import DetectionControlPanel
from playback_manager import PlaybackManager, FrameSampler
from detection_processor import DetectionProcessor

# Constants
OUTPUT_DIR = Path("output")
FLAGGED_DIR = OUTPUT_DIR / "flagged_frames"
LOG_CSV = OUTPUT_DIR / "flagged_log.csv"
WEIGHTS_DEFAULT = "./weights/bestone.pt"
TOP_N = 20


class ImageTaggerUI:
    """Main application class for Image Tagger / Cheating Detection"""
    
    
    
    def __init__(self, image_path=None):
        """Initialize the application"""
        # Core data
        self.mapper = CoordinateMapper()
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("EyeSpy - Cheating Detection System")
        
        # Set window size and minimum size
        self.root.geometry(f"{WINDOW['default_width']}x{WINDOW['default_height']}")
        self.root.minsize(WINDOW['min_width'], WINDOW['min_height'])
        self.root.configure(bg=COLORS['white'])
        
        # Current frame data
        self.current_frame_bgr = None
        self.current_frame_pil = None
        self.current_frame_info = {}
        
        # Detector
        self.detector = None
        
        # Playback manager
        self.playback_manager = PlaybackManager(frame_queue_size=4)
        
        # Detection processor
        self.detection_processor = DetectionProcessor(
            output_dir=OUTPUT_DIR,
            flagged_dir=FLAGGED_DIR,
            log_csv=LOG_CSV,
            top_n=TOP_N,
            max_entries_per_person=50,
            save_gap_seconds=2
        )
        
        # Build UI
        self._build_ui(image_path)
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Start polling for playback frames
        self.root.after(30, self._poll_playback_queue)
    
    def _build_ui(self, image_path):
        """Responsive UI layout with proper resizing"""
        self.root.grid_rowconfigure(0, weight=1)  # Main content area
        self.root.grid_rowconfigure(1, weight=0)  # Status bar (fixed height)
        self.root.grid_columnconfigure(0, weight=1)  # Canvas expands to fill
        self.root.grid_columnconfigure(1, weight=0)  # Sidebar fixed width

        # Left: Canvas Panel
        self._create_canvas_panel(image_path)
        self.canvas_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Right: Sidebar Panel
        self._create_control_panel()
        self.sidebar_container.grid(row=0, column=1, sticky="ns", padx=(0, 5), pady=5)

        # Status Bar (bottom)
        self._create_status_bar()
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
    
    
    def _create_canvas_panel(self, image_path):
        """Canvas area that scales properly"""
        self.canvas_container = tk.Frame(self.root, bg=COLORS['bg_secondary'])
        self.canvas_container.grid_rowconfigure(0, weight=1)
        self.canvas_container.grid_columnconfigure(0, weight=1)

        # Default or provided image
        if image_path and os.path.isfile(image_path):
            pil = Image.open(image_path)
        else:
            pil = Image.new("RGB", (1000, 750), color=(220, 220, 220))

        self.canvas_manager = CanvasManager(
            self.canvas_container,
            pil,
            fit_within=(CANVAS['fit_width'], CANVAS['fit_height'])
        )

        self.canvas_manager.canvas.grid(
            row=0, column=0, sticky="nsew", padx=8, pady=8
        )

        # Click bindings
        self.canvas_manager.bind_left_click(self._on_canvas_left_click)
        self.canvas_manager.bind_right_click(self._on_canvas_right_click)
        
        # Resize binding to redraw markers when window is resized
        self.canvas_manager.bind_resize(self._on_canvas_resized)
    
    def _create_control_panel(self):
        """Scrollable sidebar panel with clean spacing"""
        # Fixed-width sidebar container
        self.sidebar_container = tk.Frame(
            self.root, 
            bg=COLORS['white'],
            width=WINDOW['sidebar_max_width']
        )
        self.sidebar_container.grid_propagate(False)  # Prevent resizing based on content
        self.sidebar_container.grid_rowconfigure(0, weight=1)
        self.sidebar_container.grid_columnconfigure(0, weight=1)

        # Canvas for scrolling with fixed width
        canvas = tk.Canvas(
            self.sidebar_container, 
            bg=COLORS['white'], 
            highlightthickness=0,
            width=WINDOW['sidebar_max_width'] - 20
        )
        scrollbar = tk.Scrollbar(self.sidebar_container, orient="vertical", command=canvas.yview)

        # Scrollable frame constrained to canvas width
        scrollable_frame = tk.Frame(canvas, bg=COLORS['white'])
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)

        # Create window with width constraint
        canvas_window = canvas.create_window(
            (0, 0), 
            window=scrollable_frame, 
            anchor="nw",
            width=WINDOW['sidebar_max_width'] - 35  # Account for scrollbar
        )
        
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Fix scrolling behavior
        def on_mousewheel(e):
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)

        # Inject list manager + panels into scrollable frame:
        self.list_manager = ListManager(scrollable_frame)

        # Add control panels with spacing
        self.student_panel = StudentControlPanel(scrollable_frame, callbacks=self._student_callbacks())
        self.student_panel.pack(fill=tk.X, pady=6, padx=4)

        self.file_panel = FileOperationsPanel(scrollable_frame, callbacks=self._file_callbacks())
        self.file_panel.pack(fill=tk.X, pady=6, padx=4)

        self.detection_panel = DetectionControlPanel(
            scrollable_frame, callbacks=self._detection_callbacks(),
            default_model_path=WEIGHTS_DEFAULT
        )
        self.detection_panel.pack(fill=tk.X, pady=6, padx=4)
    
    def _create_status_bar(self):
        """Create status bar at bottom of window"""
        self.status_bar = tk.Label(
            self.root,
            text="Ready | EyeSpy Cheating Detection System",
            bd=0,
            relief=tk.FLAT,
            anchor=tk.W,
            font=FONTS['status'],
            bg=COLORS['bg_secondary'],
            fg=COLORS['dark'],
            padx=SPACING['md'],
            pady=SPACING['sm']
        )
    
    # ==================== Keyboard Shortcuts ====================
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind_all("<Control-s>", lambda e: self.save_data())
        self.root.bind_all("<Control-o>", lambda e: self.load_data())
        self.root.bind_all("<Control-i>", lambda e: self.import_from_csv())
        self.root.bind_all("<Control-n>", lambda e: self.open_add_student_dialog())
        self.root.bind_all("<Control-e>", lambda e: self.export_to_csv())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected_mapping())
    
    # ==================== Detector Methods ====================
    
    
    
    def _load_detector(self):
        """Load the detection model"""
        path = self.detection_panel.get_model_path()
        if not path:
            messagebox.showerror("Error", "Please provide a path to the weights file.")
            return
        if not os.path.isfile(path):
            messagebox.showerror("Error", f"Weights file not found: {path}")
            return
        
        try:
            self.detector = CheatDetector(path)
            self.status_bar.config(text=f"✓ Loaded model: {path}")
            messagebox.showinfo("Success", "Detection model loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load model:\n{e}")
            self.detector = None
    
    # ==================== Source Selection ====================
    
    def _select_source_path(self):
        """Select source path based on source type"""
        st = self.detection_panel.get_source_type()
        
        if st == "image_folder":
            path = filedialog.askdirectory(title="Select Image Folder")
            if path:
                self.source_path = path
                self.detection_panel.update_source_label(f"Source: Image Folder → {path}")
        
        elif st == "video_folder":
            path = filedialog.askdirectory(title="Select Video Folder")
            if path:
                self.source_path = path
                self.detection_panel.update_source_label(f"Source: Video Folder → {path}")
        
        elif st == "video_file":
            path = filedialog.askopenfilename(
                title="Select Video File",
                filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv"), ("All files", "*.*")]
            )
            if path:
                self.source_path = path
                self.detection_panel.update_source_label(f"Source: Video File → {path}")
        
        elif st == "camera":
            idx = simpledialog.askinteger(
                "Camera Index",
                "Enter camera index (default 0):",
                initialvalue=0,
                parent=self.root
            )
            if idx is not None:
                self.source_path = int(idx)
                self.detection_panel.update_source_label(f"Source: Camera index → {idx}")
    
    # ==================== Frame Sampling ====================
    
    def _sample_frame_once(self):
        """Sample a single frame from selected source"""
        st = self.detection_panel.get_source_type()
        
        if not hasattr(self, "source_path") or self.source_path is None:
            messagebox.showerror("Error", "Please select source path/index first")
            return
        
        try:
            # Use FrameSampler to get a frame
            if st == "image_folder":
                frame, info = FrameSampler.sample_from_image_folder(self.source_path)
            elif st == "video_folder":
                frame, info = FrameSampler.sample_from_video_folder(self.source_path)
            elif st == "video_file":
                frame, info = FrameSampler.sample_from_video_file(self.source_path)
            elif st == "camera":
                frame, info = FrameSampler.sample_from_camera(self.source_path)
            else:
                messagebox.showerror("Error", "Unsupported source type")
                return
            
            if frame is None:
                messagebox.showinfo("No Frame", "Could not sample a frame from the selected source.")
                return
            
            # Set the sampled frame
            self._set_current_frame(frame, info)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to sample frame:\n{e}")
    
    def _set_current_frame(self, frame_bgr, info):
        """Set the current frame and update UI"""
        self.current_frame_bgr = frame_bgr.copy()
        self.current_frame_pil = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
        self.current_frame_info = info
        
        # Update canvas
        self.canvas_manager.set_image(
            self.current_frame_pil,
            fit_within=(CANVAS['fit_width'], CANVAS['fit_height'])
        )
        self.canvas_manager.redraw_all_markers(
            self.mapper.mapped_students,
            self.mapper.mapped_student_objects
        )
        
        self.status_bar.config(
            text=f"✓ Sampled frame from {info.get('source_type')}: {info.get('source_desc')}"
        )
    
    # ==================== Detection ====================
    
    def _detect_on_sample(self):
        """Run detection on sampled frame"""
        if self.current_frame_bgr is None:
            messagebox.showerror("Error", "Please sample a frame first")
            return
        
        if self.detector is None:
            messagebox.showerror("Error", "Please load the detection model first")
            return
        
        # Run detection
        conf = self.detection_panel.get_conf_threshold()
        dets = self.detector.detect_frame(self.current_frame_bgr, conf_thresh=conf)
        
        if not dets:
            messagebox.showinfo("No Detections", "No cheating behavior detected in this frame")
            return
        
        # Draw detections on canvas
        self.canvas_manager.draw_detections(dets, color="red")
        
        # Save and log using detection processor
        save_path, flagged = self.detection_processor.save_sample_detection(
            self.current_frame_bgr, dets, self.mapper
        )
        
        # Draw flags on canvas
        for stu, det in flagged:
            sx, sy = self.mapper.mapped_students.get(stu.roll)
            if sx and sy:
                self.canvas_manager.draw_flag_for_student(sx, sy, stu.name, color="orange")
        
        messagebox.showinfo(
            "Detection Complete",
            f"Found {len(dets)} detection(s)\nFlagged {len(flagged)} student(s)\nSaved to: {save_path}"
        )
    
    # ==================== Playback Control ====================
    
    def _start_playback(self):
        """Start video/camera playback"""
        if not hasattr(self, "source_path") or self.source_path is None:
            messagebox.showerror("Error", "Please select source first")
            return
        
        if self.detector is None:
            messagebox.showwarning("Warning", "Detector not loaded. Playback will run without detection.")
        
        st = self.detection_panel.get_source_type()
        conf = self.detection_panel.get_conf_threshold()
        
        success = self.playback_manager.start_playback(
            st, self.source_path, self.detector, conf
        )
        
        if success:
            self.status_bar.config(text="▶ Playback started")
            # Switch to detection mode
            self.list_manager.switch_to_detection_mode()
    
    def _toggle_pause(self):
        """Toggle playback pause"""
        is_paused = self.playback_manager.toggle_pause()
        if is_paused:
            self.status_bar.config(text="⏸ Playback paused")
        else:
            self.status_bar.config(text="▶ Playback resumed")
    
    def _stop_playback(self):
        """Stop playback"""
        self.playback_manager.stop_playback()
        self.status_bar.config(text="⏹ Playback stopped")
        # Switch back to normal mode
        self.list_manager.switch_to_normal_mode()
        # Restore unmapped students list
        self.list_manager.populate_unmapped(self.mapper.unmapped_students)
    
    def _terminate_playback(self):
        """Terminate playback aggressively"""
        self.playback_manager.terminate_playback()
        self.status_bar.config(text="⛔ Playback terminated")
        # Switch back to normal mode
        self.list_manager.switch_to_normal_mode()
        # Restore unmapped students list
        self.list_manager.populate_unmapped(self.mapper.unmapped_students)
    
    def _poll_playback_queue(self):
        """Poll playback queue for new frames"""
        frame_data = self.playback_manager.get_frame()
        
        if frame_data:
            frame, src_name, frame_idx, detections = frame_data
            
            # Update current frame
            self.current_frame_bgr = frame
            self.current_frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
            # Update canvas
            self.canvas_manager.set_image(
                self.current_frame_pil,
                fit_within=(CANVAS['fit_width'], CANVAS['fit_height'])
            )
            
            # Process detections
            if detections:
                self.canvas_manager.draw_detections(detections, color="red")
                
                # Process each detection
                for det in detections:
                    flagged = self.detection_processor.process_detection(
                        det, frame, self.mapper, src_name, frame_idx
                    )
                    
                    # Draw flags
                    for stu, _ in flagged:
                        sx, sy = self.mapper.mapped_students.get(stu.roll)
                        if sx and sy:
                            self.canvas_manager.draw_flag_for_student(sx, sy, stu.name, color="orange")
                
                # Update top-N label
                self.detection_panel.update_topn_label(
                    self.detection_processor.get_top_count(), TOP_N
                )
                
                # Update flagged students display
                flagged_summary = self.detection_processor.get_flagged_students_summary(self.mapper)
                self.list_manager.update_flagged_students(flagged_summary)
            
            # Redraw markers
            self.canvas_manager.redraw_all_markers(
                self.mapper.mapped_students,
                self.mapper.mapped_student_objects
            )
        
        # Schedule next poll
        self.root.after(30, self._poll_playback_queue)
    
    # ==================== Canvas Event Handlers ====================
    
    def _on_canvas_resized(self):
        """Handle canvas resize - redraw all markers at correct positions"""
        self.canvas_manager.redraw_all_markers(
            self.mapper.mapped_students,
            self.mapper.mapped_student_objects
        )
        # Also redraw any active detections and flags
        self.canvas_manager.clear_detections()
    
    # ==================== Canvas Click Handlers ====================
    
    def _on_canvas_left_click(self, dx, dy):
        """Handle left click on canvas (map student)"""
        # Convert display coords to image coords
        ix, iy = self.canvas_manager.display_to_image(dx, dy)
        
        # Get selected unmapped student
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror(
                "Error",
                "Please select an unmapped student from the list first"
            )
            return
        
        stu = self.mapper.unmapped_students[idx]
        
        # Map student
        self.mapper.map_student(ix, iy, stu)
        
        # Update UI
        self._apply_unmapped_filter()
        self.list_manager.populate_mapped(
            self.mapper.mapped_students,
            self.mapper.mapped_student_objects
        )
        self.canvas_manager.draw_marker(ix, iy, stu.name)
        self._update_counts()
        
        self.status_bar.config(text=f"✓ Mapped {stu.name} at ({int(ix)}, {int(iy)})")
    
    def _on_canvas_right_click(self, dx, dy):
        """Handle right click on canvas (unmap student)"""
        # Convert to image coords
        ix, iy = self.canvas_manager.display_to_image(dx, dy)
        
        # Find nearest student
        nearest_roll = self.mapper.nearest_student(ix, iy)
        if nearest_roll:
            stu = self.mapper.mapped_student_objects.get(nearest_roll)
            if stu and messagebox.askyesno("Unmap", f"Unmap {stu.name} ({stu.roll})?"):
                self.mapper.unmap_student(nearest_roll)
                self.refresh_views()
                self.status_bar.config(text=f"✓ Unmapped {stu.name}")
    
    # ==================== Student Management ====================
    
    def open_add_student_dialog(self):
        """Open dialog to add new student"""
        AddStudentDialog(self.root, self._on_student_added)
    
    def _on_student_added(self, student):
        """Callback when student is added"""
        if self.mapper.get_student_by_roll(student.roll):
            messagebox.showerror("Error", f"Roll number '{student.roll}' already exists.")
            return
        
        self.mapper.add_student(student)
        self._apply_unmapped_filter()
        self._update_counts()
        self.status_bar.config(text=f"✓ Added student: {student.name} ({student.roll})")
    
    def edit_student_ui(self):
        """Edit selected student"""
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a student to edit from the Unmapped list")
            return
        
        stu = self.mapper.unmapped_students[idx]
        res = prompt_edit_student(self.root, stu)
        if not res:
            return
        
        name, dept, roll = res
        existing = self.mapper.get_student_by_roll(roll)
        if existing and existing.roll != stu.roll:
            messagebox.showerror("Error", f"Roll number '{roll}' already exists")
            return
        
        stu.name, stu.department, stu.roll = name, dept, roll
        self._apply_unmapped_filter()
        self.status_bar.config(text=f"✓ Updated student: {stu.name}")
    
    def remove_student_ui(self):
        """Remove selected student"""
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a student to remove from the Unmapped list")
            return
        
        stu = self.mapper.unmapped_students[idx]
        if messagebox.askyesno("Confirm Delete", f"Remove student '{stu.name}' ({stu.roll})?"):
            self.mapper.unmapped_students.pop(idx)
            self._apply_unmapped_filter()
            self._update_counts()
            self.status_bar.config(text=f"✓ Removed student: {stu.name}")
    
    # ==================== Mapping Operations ====================
    
    def remove_selected_mapping(self):
        """Remove selected mapping"""
        idx = self.list_manager.get_selected_mapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a mapped student to remove")
            return
        
        roll = self.list_manager.get_mapped_roll_at(idx)
        if not roll:
            return
        
        stu = self.mapper.mapped_student_objects.get(roll)
        if not stu:
            return
        
        if messagebox.askyesno("Remove Mapping", f"Remove mapping for {stu.name} ({stu.roll})?"):
            self.mapper.unmap_student(roll)
            self.refresh_views()
            self._update_counts()
            self.status_bar.config(text=f"✓ Removed mapping: {stu.name}")
    
    def clear_all_mappings(self):
        """Clear all mappings"""
        if not self.mapper.mapped_students:
            messagebox.showinfo("Info", "No mappings to clear")
            return
        
        if messagebox.askyesno(
            "Confirm Clear",
            "Clear all mappings? This will move all mapped students back to unmapped."
        ):
            self.mapper.clear_mappings()
            self.refresh_views()
            self.status_bar.config(text="✓ All mappings cleared")
    
    # ==================== File Operations ====================
    
    def import_from_csv(self):
        """Import students from CSV"""
        parsed_students, path = import_students_from_csv(self.root)
        if parsed_students is None:
            return
        
        added = 0
        skipped = 0
        for stu in parsed_students:
            if self.mapper.get_student_by_roll(stu.roll):
                skipped += 1
                continue
            self.mapper.add_student(stu)
            added += 1
        
        self._apply_unmapped_filter()
        self._update_counts()
        
        summary = f"✓ Imported {added} students. Skipped {skipped} duplicates from: {path}"
        self.status_bar.config(text=summary)
        messagebox.showinfo("Import Complete", summary)
    
    def export_to_csv(self):
        """Export students to CSV"""
        path = export_students_to_csv(self.mapper, self.root)
        if path:
            self.status_bar.config(text=f"✓ Exported to: {path}")
    
    def save_data(self):
        """Save project data"""
        path = save_mapper_dialog(self.mapper, self.root)
        if path:
            self.status_bar.config(text=f"✓ Project saved to: {path}")
    
    def load_data(self):
        """Load project data"""
        mapper_obj, path = load_mapper_dialog(self.root)
        if not mapper_obj:
            return
        
        if isinstance(mapper_obj, CoordinateMapper):
            self.mapper = mapper_obj
            self.refresh_views()
            self.status_bar.config(text=f"✓ Project loaded from: {path}")
            messagebox.showinfo("Success", "Project loaded successfully!")
        else:
            messagebox.showerror("Error", "Invalid project file")
    
    # ==================== UI Update Helpers ====================
    
    def refresh_views(self):
        """Refresh all views"""
        self.list_manager.populate_unmapped(self.mapper.unmapped_students)
        self.list_manager.populate_mapped(
            self.mapper.mapped_students,
            self.mapper.mapped_student_objects
        )
        self.canvas_manager.redraw_all_markers(
            self.mapper.mapped_students,
            self.mapper.mapped_student_objects
        )
        self._update_counts()
    
    def _apply_unmapped_filter(self):
        """Apply search filter to unmapped list"""
        query = self.student_panel.get_search_query()
        
        if not query:
            self.list_manager.populate_unmapped(self.mapper.unmapped_students)
        else:
            filtered = [
                s for s in self.mapper.unmapped_students
                if query in s.name.lower()
                or query in s.roll.lower()
                or query in s.department.lower()
            ]
            self.list_manager.populate_unmapped(filtered)
    
    def _update_counts(self):
        """Update student counts"""
        unmapped = len(self.mapper.unmapped_students)
        mapped = len(self.mapper.mapped_students)
        self.student_panel.update_counts(unmapped, mapped)
    
    # ==================== Callback Helpers ====================
    
    def _student_callbacks(self):
        """Return dictionary of student control callbacks"""
        return {
            'on_add_student': self.open_add_student_dialog,
            'on_edit_student': self.edit_student_ui,
            'on_remove_student': self.remove_student_ui,
            'on_clear_mappings': self.clear_all_mappings,
            'on_remove_selected_mapping': self.remove_selected_mapping,
            'on_search_changed': self._apply_unmapped_filter,
        }
    
    def _file_callbacks(self):
        """Return dictionary of file operation callbacks"""
        return {
            'on_save': self.save_data,
            'on_load': self.load_data,
            'on_import_csv': self.import_from_csv,
            'on_export_csv': self.export_to_csv,
        }
    
    def _detection_callbacks(self):
        """Return dictionary of detection control callbacks"""
        return {
            'on_load_detector': self._load_detector,
            'on_select_source': self._select_source_path,
            'on_sample_frame': self._sample_frame_once,
            'on_detect_sample': self._detect_on_sample,
            'on_play': self._start_playback,
            'on_pause': self._toggle_pause,
            'on_stop': self._stop_playback,
            'on_terminate': self._terminate_playback,
        }
    
    # ==================== Main Loop ====================
    
    def run(self):
        """Start the application"""
        self._update_counts()
        self.root.mainloop()


if __name__ == "__main__":
    try:
        app = ImageTaggerUI()
        app.run()
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
