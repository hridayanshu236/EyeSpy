import tkinter as tk

class ListManager:
    """Encapsulates the two listboxes and helper functions for updating/getting selections."""
    def __init__(self, parent_frame):
        self.frame = parent_frame
        self.detection_mode = False  # Track if in detection mode
        
        # Container for top section (will switch between unmapped and flagged)
        self.top_container = tk.Frame(self.frame, bg="white")
        self.top_container.pack(fill=tk.BOTH, expand=True)
        
        # Unmapped section with label
        self.unmapped_label = tk.Label(self.top_container, text="Unmapped Students", font=("Segoe UI", 11, "bold"), bg="lightblue", pady=5)
        self.unmapped_label.pack(fill=tk.X)
        self.unmapped_scroll = tk.Scrollbar(self.top_container)
        self.unmapped_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.unmapped_listbox = tk.Listbox(self.top_container, width=40, height=10, yscrollcommand=self.unmapped_scroll.set, font=("Courier", 10))
        self.unmapped_listbox.pack(fill=tk.BOTH, expand=True, padx=(0,6))
        self.unmapped_scroll.config(command=self.unmapped_listbox.yview)

        # Spacer
        self.spacer = tk.Frame(self.frame, height=6)
        self.spacer.pack(fill=tk.X)

        # Mapped section with label
        self.mapped_label = tk.Label(self.frame, text="Mapped Students", font=("Segoe UI", 11, "bold"), bg="lightgreen", pady=5)
        self.mapped_label.pack(fill=tk.X, pady=(6,0))
        self.mapped_scroll = tk.Scrollbar(self.frame)
        self.mapped_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.mapped_listbox = tk.Listbox(self.frame, width=40, height=10, yscrollcommand=self.mapped_scroll.set, font=("Courier", 10))
        self.mapped_listbox.pack(fill=tk.BOTH, expand=True, padx=(0,6), pady=(0,6))
        self.mapped_scroll.config(command=self.mapped_listbox.yview)

    # Unmapped helpers
    def populate_unmapped(self, students):
        """Replace entire unmapped listbox contents (students: iterable of Student)"""
        self.unmapped_listbox.delete(0, tk.END)
        for stu in students:
            self.unmapped_listbox.insert(tk.END, f"{stu.name:20} | {stu.roll}")

    def get_selected_unmapped_index(self):
        sel = self.unmapped_listbox.curselection()
        return sel[0] if sel else None

    def remove_unmapped_at(self, idx):
        self.unmapped_listbox.delete(idx)

    def insert_unmapped_at_end(self, student):
        self.unmapped_listbox.insert(tk.END, f"{student.name:20} | {student.roll}")

    def update_unmapped_item(self, idx, student):
        self.unmapped_listbox.delete(idx)
        self.unmapped_listbox.insert(idx, f"{student.name:20} | {student.roll}")

    # Mapped helpers
    def populate_mapped(self, mapped_students, mapped_objects):
        self.mapped_listbox.delete(0, tk.END)
        for roll, (x, y) in mapped_students.items():
            stu = mapped_objects.get(roll)
            if stu:
                self.mapped_listbox.insert(tk.END, f"{stu.name:20} | {stu.roll} → ({x},{y})")

    def clear_all(self):
        self.unmapped_listbox.delete(0, tk.END)
        self.mapped_listbox.delete(0, tk.END)

    # New helpers for mapped selection and parsing
    def get_selected_mapped_index(self):
        sel = self.mapped_listbox.curselection()
        return sel[0] if sel else None

    def get_mapped_roll_at(self, idx):
        try:
            text = self.mapped_listbox.get(idx)
        except Exception:
            return None
        parts = text.split('|')
        if len(parts) < 2:
            return None
        right = parts[1]
        if '→' in right:
            roll_part = right.split('→')[0]
        else:
            roll_part = right
        return roll_part.strip()

    def remove_mapped_at(self, idx):
        self.mapped_listbox.delete(idx)

    def find_mapped_index_by_roll(self, roll):
        for i in range(self.mapped_listbox.size()):
            r = self.get_mapped_roll_at(i)
            if r == roll:
                return i
        return None

    # Expose underlying listboxes for event binding if needed
    def get_mapped_listbox(self):
        """Return the mapped listbox widget (for binding events)."""
        return self.mapped_listbox

    def get_unmapped_listbox(self):
        """Return the unmapped listbox widget (for binding events)."""
        return self.unmapped_listbox
    
    # Detection mode methods
    def switch_to_detection_mode(self):
        """Switch to detection mode - show Flagged Students instead of Unmapped"""
        if self.detection_mode:
            return
        
        self.detection_mode = True
        
        # Update label
        self.unmapped_label.config(text="🚨 Flagged Students", bg="#FFD700")
        
        # Clear and prepare for flagged students display
        self.unmapped_listbox.delete(0, tk.END)
    
    def switch_to_normal_mode(self):
        """Switch back to normal mode - show Unmapped Students"""
        if not self.detection_mode:
            return
        
        self.detection_mode = False
        
        # Update label
        self.unmapped_label.config(text="Unmapped Students", bg="lightblue")
        
        # Clear flagged students display
        self.unmapped_listbox.delete(0, tk.END)
    
    def update_flagged_students(self, flagged_data):
        """
        Update flagged students display with frame counts
        
        Args:
            flagged_data: Dictionary {roll: {'name': str, 'count': int}}
        """
        if not self.detection_mode:
            return
        
        self.unmapped_listbox.delete(0, tk.END)
        
        # Sort by count (descending) for visibility
        sorted_students = sorted(
            flagged_data.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        for roll, data in sorted_students:
            name = data['name']
            count = data['count']
            # Display format: "Name | Roll | Frames: X"
            display_text = f"{name[:18]:18} | {roll:12} | 🚩 {count}"
            self.unmapped_listbox.insert(tk.END, display_text)