import tkinter as tk
from tkinter import messagebox, simpledialog
from Student import Student

class AddStudentDialog:
    """Modal dialog to add a student. On success it returns a Student instance via callback."""
    def __init__(self, parent, on_add_callback):
        self.parent = parent
        self.on_add_callback = on_add_callback
        self._build()

    def _build(self):
        self.win = tk.Toplevel(self.parent)
        self.win.title("Add New Student")
        self.win.geometry("400x250")
        self.win.resizable(False, False)
        self.win.transient(self.parent)
        self.win.grab_set()

        main_frame = tk.Frame(self.win, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Name:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="e", padx=8, pady=8)
        self.name_entry = tk.Entry(main_frame, width=30, font=("Arial", 10))
        self.name_entry.grid(row=0, column=1, padx=8, pady=8)
        self.name_entry.focus()

        tk.Label(main_frame, text="Department:", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="e", padx=8, pady=8)
        self.dept_entry = tk.Entry(main_frame, width=30, font=("Arial", 10))
        self.dept_entry.grid(row=1, column=1, padx=8, pady=8)

        tk.Label(main_frame, text="Roll Number:", font=("Arial", 10, "bold")).grid(row=2, column=0, sticky="e", padx=8, pady=8)
        self.roll_entry = tk.Entry(main_frame, width=30, font=("Arial", 10))
        self.roll_entry.grid(row=2, column=1, padx=8, pady=8)

        btn_frame = tk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)

        tk.Button(btn_frame, text="Add Student", command=self.on_submit, bg="lightgreen", width=12).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.win.destroy, bg="lightgray", width=12).pack(side=tk.LEFT, padx=5)

        self.win.bind('<Return>', lambda e: self.on_submit())
        self.win.bind('<Escape>', lambda e: self.win.destroy())

    def on_submit(self):
        name = self.name_entry.get().strip()
        dept = self.dept_entry.get().strip()
        roll = self.roll_entry.get().strip()
        if not (name and dept and roll):
            messagebox.showerror("Error", "All fields are required.", parent=self.win)
            return
        student = Student(name, dept, roll)
        self.on_add_callback(student)
        self.win.destroy()


def prompt_edit_student(parent, student):
    """Prompt for editing an existing student (unmapped). Returns updated (name, dept, roll) or None if cancelled."""
    name = simpledialog.askstring("Edit Name", "Enter New Name:", initialvalue=student.name, parent=parent)
    if name is None:
        return None
    name = name.strip()

    dept = simpledialog.askstring("Edit Department", "Enter New Department:", initialvalue=student.department, parent=parent)
    if dept is None:
        return None
    dept = dept.strip()

    roll = simpledialog.askstring("Edit Roll", "Enter New Roll:", initialvalue=student.roll, parent=parent)
    if roll is None:
        return None
    roll = roll.strip()

    if not (name and dept and roll):
        messagebox.showerror("Error", "All fields must be filled.", parent=parent)
        return None

    return name, dept, roll