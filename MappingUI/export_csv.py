import csv
from tkinter import filedialog, messagebox

def export_students_to_csv(mapper, parent):
    """
    Export all students (mapped and unmapped) to a CSV file with columns:
    Name, Department, Roll_number, X, Y

    Mapped students include X and Y coordinates; unmapped students have empty X/Y.
    Returns the path on success, or None on cancel/error.
    """
    path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        title="Export Students to CSV"
    )
    if not path:
        return None

    try:
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Department", "Roll_number", "X", "Y"])

            # Write mapped students first (with coordinates)
            
            for roll, (x, y) in mapper.mapped_students.items():
                stu = mapper.mapped_student_objects.get(roll)
                if not stu:
                    continue
                writer.writerow([stu.name, stu.department, stu.roll, x, y])

            # unmapped students (X/Y empty)
            for stu in mapper.unmapped_students:
                writer.writerow([stu.name, stu.department, stu.roll, "", ""])

        messagebox.showinfo("Export Complete", f"Exported students to: {path}", parent=parent)
        return path
    except Exception as e:
        messagebox.showerror("Error", f"Failed to export CSV:\n{e}", parent=parent)
        return None