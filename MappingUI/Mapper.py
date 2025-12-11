import math
import pickle
from Student import Student

class CoordinateMapper:
    def __init__(self):
        # Dictionary: roll -> (x, y)
        self.mapped_students = {}  # {roll: (x, y)}
        # Dictionary to store Student objects for mapped students
        self.mapped_student_objects = {}  # {roll: Student}
        # List of unmapped Student objects
        self.unmapped_students = []

    def add_student(self, student):
        """Add a student to unmapped list if not already present"""
        # Use roll-based comparison to avoid duplicate rolls
        if student.roll in self.mapped_students:
            return
        if all(stu.roll != student.roll for stu in self.unmapped_students):
            self.unmapped_students.append(student)

    def map_student(self, x, y, student):
        """Map a student to coordinates"""
        self.mapped_students[student.roll] = (x, y)
        self.mapped_student_objects[student.roll] = student
        # remove from unmapped if present
        self.unmapped_students = [stu for stu in self.unmapped_students if stu.roll != student.roll]

    def nearest_student(self, x, y):
        """Find the nearest student roll to given coordinates"""
        if not self.mapped_students:
            return None

        nearest_roll = None
        min_dist = float('inf')
        for roll, (cx, cy) in self.mapped_students.items():
            dist = math.hypot(cx - x, cy - y)
            if dist < min_dist:
                min_dist = dist
                nearest_roll = roll
        return nearest_roll

    def nearest_n_students(self, x, y, n=2, max_distance=None):
        """
        Return up to n nearest mapped students to (x,y).
        Returns a list of tuples: [(roll, distance), ...] sorted by distance ascending.
        If max_distance is provided, only students within that distance are returned.
        """
        if not self.mapped_students:
            return []

        dists = []
        for roll, (cx, cy) in self.mapped_students.items():
            dist = math.hypot(cx - x, cy - y)
            dists.append((roll, dist))

        dists.sort(key=lambda t: t[1])
        if max_distance is not None:
            dists = [t for t in dists if t[1] <= max_distance]
        return dists[:n]

    def get_student_by_roll(self, roll):
        """Get Student object by roll number"""
        # Check in unmapped students
        for stu in self.unmapped_students:
            if stu.roll == roll:
                return stu
        # Check in mapped students
        return self.mapped_student_objects.get(roll, None)

    def unmap_student(self, roll):
        """Unmap a student by roll and move back to unmapped list"""
        if roll in self.mapped_students:
            student_obj = self.mapped_student_objects.get(roll)
            if student_obj and all(stu.roll != student_obj.roll for stu in self.unmapped_students):
                self.unmapped_students.append(student_obj)
            del self.mapped_students[roll]
            del self.mapped_student_objects[roll]
            return True
        return False

    def clear_mappings(self):
        """Move all mapped students back to unmapped"""
        for roll in list(self.mapped_students.keys()):
            student_obj = self.mapped_student_objects.get(roll)
            if student_obj and all(stu.roll != student_obj.roll for stu in self.unmapped_students):
                self.unmapped_students.append(student_obj)
        self.mapped_students.clear()
        self.mapped_student_objects.clear()

    def save(self, filepath='data.pkl'):
        """Save mapper state to file (pickles the mapper instance)"""
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(filepath='data.pkl'):
        """Load mapper state from file and return CoordinateMapper instance"""
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError:
            return CoordinateMapper()