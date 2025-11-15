import os
import tkinter as tk
from tkinter import messagebox

from Student import Student
from Mapper import CoordinateMapper
from dialogs import AddStudentDialog, prompt_edit_student
from list_manager import ListManager
from canvas_manager import CanvasManager
from file_manager import save_mapper_dialog, load_mapper_dialog, import_students_from_csv
from export_csv import export_students_to_csv
from PIL import Image

# UI constants
APP_FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 11, "bold")

class ImageTaggerUI:
    def __init__(self, image_path):
        self.mapper = CoordinateMapper()

        self.root = tk.Tk()
        self.root.title("Image Student Mapper - Optimized UI")
        self.root.geometry("1400x900")
        self.root.minsize(1100, 650)

        # NOTE: Top toolbar removed as requested. Other layout and features remain.

        # Main paned window (left = canvas, right = controls)
        self.paned = tk.PanedWindow(self.root, sashrelief=tk.RAISED, sashwidth=6)
        self.paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4,8))

        # Left: canvas frame
        self.canvas_frame = tk.Frame(self.paned, bd=1, relief=tk.SOLID)
        self.paned.add(self.canvas_frame, minsize=600)

        # Right: controls frame
        self.right_frame = tk.Frame(self.paned, bd=1, relief=tk.FLAT, width=380)
        self.paned.add(self.right_frame, minsize=300)

        # Load and prepare image
        self.image_path = image_path
        if not os.path.isfile(self.image_path):
            choice = messagebox.askyesno("Image Not Found", f"Image '{self.image_path}' not found. Choose another?")
            if choice:
                from tkinter import filedialog
                chosen = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")])
                if chosen:
                    self.image_path = chosen
                else:
                    raise FileNotFoundError(self.image_path)
            else:
                raise FileNotFoundError(self.image_path)

        img = Image.open(self.image_path)
        # scale for a good fit
        max_width, max_height = 1000, 800
        try:
            resample = Image.Resampling.LANCZOS
        except AttributeError:
            resample = Image.Resampling.LANCZOS if hasattr(Image, "LANCZOS") else None
        if img.width > max_width or img.height > max_height:
            ratio = min(max_width / img.width, max_height / img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, resample)

        # Canvas manager inside left frame
        self.canvas_manager = CanvasManager(self.canvas_frame, img)
        # Bind canvas callbacks
        self.canvas_manager.bind_left_click(self._on_canvas_left_click)
        self.canvas_manager.bind_right_click(self._on_canvas_right_click)

        # Create list manager inside right frame
        list_container = tk.Frame(self.right_frame, padx=10, pady=10)
        list_container.pack(fill=tk.BOTH, expand=True)
        self.list_manager = ListManager(list_container)

        # Create grouped controls and buttons (below lists)
        self._build_controls()

        # status bar at bottom
        self.status_bar = tk.Label(self.root, text="Ready | Click on image to map selected student", bd=1, relief=tk.SUNKEN, anchor=tk.W, font=("Segoe UI", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Bind keyboard shortcuts
        self._bind_shortcuts()

        # Hook double-click on mapped list to unmap quickly
        mapped_lb = self.list_manager.get_mapped_listbox()
        mapped_lb.bind("<Double-Button-1>", lambda e: self.remove_selected_mapping())

        # Populate (empty) views and counts
        self.refresh_views()

    def _build_controls(self):
        # Right column controls: counts, search + action groups
        # Place counts label near the top of the controls area (since top toolbar is removed)
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

        # Buttons groups (student management)
        group_frame = tk.Frame(self.right_frame, padx=10, pady=6)
        group_frame.pack(fill=tk.X)

        tk.Label(group_frame, text="Student Management", font=TITLE_FONT).pack(anchor="w")
        btn_frame = tk.Frame(group_frame)
        btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(btn_frame, text="➕ Add Student", command=self.open_add_student_dialog, bg="#90EE90", font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="✏️ Edit Student", command=self.edit_student_ui, bg="#FFD700", font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(btn_frame, text="🗑️ Remove Student", command=self.remove_student_ui, bg="#FFA07A", font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        tk.Label(group_frame, text="Mapping Tools", font=TITLE_FONT).pack(anchor="w", pady=(8,0))
        map_btn_frame = tk.Frame(group_frame)
        map_btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(map_btn_frame, text="🔄 Clear All Mappings", command=self.clear_all_mappings, bg="#DC143C", fg="white", font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(map_btn_frame, text="🧾 Remove Selected Mapping", command=self.remove_selected_mapping, bg="#FFA500", font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

        tk.Label(group_frame, text="File Operations", font=TITLE_FONT).pack(anchor="w", pady=(8,0))
        file_btn_frame = tk.Frame(group_frame)
        file_btn_frame.pack(fill=tk.X, pady=4)
        tk.Button(file_btn_frame, text="💾 Save Project", bg="#87CEEB", command=self.save_data, font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(file_btn_frame, text="📂 Load Project", bg="#87CEEB", command=self.load_data, font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        tk.Button(file_btn_frame, text="📥 Add from CSV", bg="#ADD8E6", command=self.import_from_csv, font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        # New: Export to CSV button
        tk.Button(file_btn_frame, text="📤 Export CSV", bg="#98FB98", command=self.export_to_csv, font=APP_FONT, cursor="hand2").pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)

    # ----- Shortcuts -----
    def _bind_shortcuts(self):
        self.root.bind_all("<Control-s>", lambda e: self.save_data())
        self.root.bind_all("<Control-o>", lambda e: self.load_data())
        self.root.bind_all("<Control-i>", lambda e: self.import_from_csv())
        self.root.bind_all("<Control-n>", lambda e: self.open_add_student_dialog())
        self.root.bind_all("<Control-e>", lambda e: self.export_to_csv())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected_mapping())

    # ----- Add/Edit/Remove Students -----
    def open_add_student_dialog(self):
        AddStudentDialog(self.root, self._on_student_added)

    def _on_student_added(self, student):
        if self.mapper.get_student_by_roll(student.roll):
            messagebox.showerror("Error", f"Roll number '{student.roll}' already exists.")
            return
        self.mapper.add_student(student)
        self._apply_unmapped_filter()  # repopulate (maybe filtered)
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

    # ----- Import from CSV -----
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

    # ----- Export to CSV -----
    def export_to_csv(self):
        path = export_students_to_csv(self.mapper, self.root)
        if path:
            self.status_bar.config(text=f"Exported to: {path}")

    # ----- Canvas callbacks -----
    def _on_canvas_left_click(self, x, y):
        if not self.mapper.unmapped_students:
            messagebox.showinfo("No Students", "Please add students before mapping.")
            return
        idx = self.list_manager.get_selected_unmapped_index()
        if idx is None:
            messagebox.showerror("Error", "Please select a student from the Unmapped list to map.")
            return
        stu = self.mapper.unmapped_students[idx]
        self.mapper.map_student(x, y, stu)
        # Update UI
        self._apply_unmapped_filter()
        self.list_manager.populate_mapped(self.mapper.mapped_students, self.mapper.mapped_student_objects)
        self.canvas_manager.draw_marker(x, y, stu.name)
        self._update_counts()
        self.status_bar.config(text=f"Mapped: {stu.name} at ({x}, {y})")

    def _on_canvas_right_click(self, x, y):
        if not self.mapper.mapped_students:
            return
        nearest_roll = self.mapper.nearest_student(x, y)
        if nearest_roll is None:
            return
        stu = self.mapper.mapped_student_objects.get(nearest_roll)
        if stu and messagebox.askyesno("Unmap Student", f"Unmap {stu.name} ({stu.roll})?"):
            self.mapper.unmap_student(nearest_roll)
            self.refresh_views()
            self.status_bar.config(text=f"Unmapped: {stu.name}")

    # ----- Remove Selected Mapping -----
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

    # ----- Clear all mappings -----
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

    # ----- Views / helpers -----
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
        # ensure counts_label exists (it does after _build_controls)
        try:
            self.counts_label.config(text=f"Unmapped: {unmapped} | Mapped: {mapped}")
        except Exception:
            # fallback: put counts in status bar
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