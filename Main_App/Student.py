class Student:
    def __init__(self, name, department, roll):
        self.name = name
        self.department = department
        self.roll = roll
    
    def __repr__(self):
        return f"Student({self.name}, {self.department}, {self.roll})"
    
    def __eq__(self, other):
        if isinstance(other, Student):
            return self.roll == other.roll
        return False
    
    def __hash__(self):
        return hash(self.roll)