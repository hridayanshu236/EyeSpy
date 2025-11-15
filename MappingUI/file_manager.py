import pickle
import csv
from tkinter import filedialog, messagebox
from Student import Student

def save_mapper_dialog(mapper, parent):
    path = filedialog.asksaveasfilename(
        defaultextension=".pkl",
        filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")],
        title="Save Project"
    )
    if not path:
        return None
    try:
        data = {"mapper": mapper}
        with open(path, "wb") as f:
            pickle.dump(data, f)
        messagebox.showinfo("Saved", "Project saved successfully.", parent=parent)
        return path
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save project:\n{e}", parent=parent)
        return None

def load_mapper_dialog(parent):
    path = filedialog.askopenfilename(
        filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")],
        title="Load Project"
    )
    if not path:
        return None, None
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        # Expect dict with 'mapper' or mapper instance
        if isinstance(data, dict) and "mapper" in data:
            return data["mapper"], path
        else:
            # If pickled mapper directly
            return data, path
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load project:\n{e}", parent=parent)
        return None, None

def import_students_from_csv(parent):
    """
    Open file dialog to select a CSV and parse students.
    Expected columns (case-insensitive): Name, Department, Roll_number (roll or roll_number accepted)
    Returns (students_list, path) or (None, None) on cancel/error.
    """
    path = filedialog.askopenfilename(
        title="Import Students from CSV",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
    )
    if not path:
        return None, None

    students = []
    skipped = []
    try:
        with open(path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            # reader.fieldnames has type Sequence[str] | None, so capture into a local var and check
            fieldnames = reader.fieldnames
            if not fieldnames:
                messagebox.showerror("Error", "CSV has no header row.", parent=parent)
                return None, path

            # Normalize headers
            headers_norm = [h.strip().lower() for h in fieldnames]

            # Helper to find header key by possible names
            def find_key(possible_names):
                for name in possible_names:
                    target = name.lower()
                    for original, norm in zip(fieldnames, headers_norm):
                        if norm == target or norm.replace(' ', '_') == target or norm.replace('-', '_') == target:
                            return original  # return original header name to use with row.get()
                return None

            name_key = find_key(['name'])
            dept_key = find_key(['department', 'dept'])
            roll_key = find_key(['roll_number', 'rollnumber', 'roll', 'roll no', 'roll_no'])

            if not (name_key and dept_key and roll_key):
                messagebox.showerror("Error", "CSV must contain Name, Department and Roll_number columns (headers are case-insensitive).", parent=parent)
                return None, path

            row_num = 1  # header
            for row in reader:
                row_num += 1
                raw_name = row.get(name_key, "")
                raw_dept = row.get(dept_key, "")
                raw_roll = row.get(roll_key, "")

                name = raw_name.strip() if raw_name is not None else ""
                dept = raw_dept.strip() if raw_dept is not None else ""
                roll = str(raw_roll).strip() if raw_roll is not None else ""

                if not (name and dept and roll):
                    skipped.append((row_num, "missing fields"))
                    continue

                students.append(Student(name, dept, roll))

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read CSV:\n{e}", parent=parent)
        return None, path

    # return parsed students list and path; UI will handle duplicates & adding to mapper
    return students, path