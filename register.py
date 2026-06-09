from database import create_tables
from services.register_service import register_student

create_tables()
print("=" * 38)
print("      Student Registration")
print("=" * 38)
name       = input("Full Name   : ").strip()
roll_no    = input("Roll No     : ").strip()
department = input("Department  : ").strip()
register_student(name, roll_no, department)
