from app.models.models import Base, User
from sqlalchemy.schema import CreateTable
from sqlalchemy.dialects import postgresql
import logging

# Ensure models are loaded
print("Loaded Models:")
for table_name in Base.metadata.tables:
    print(f" - {table_name}")

if not Base.metadata.tables:
    print("WARNING: No tables found in Base.metadata!")
else:
    print("\nGenerating SQL for User table:")
    print(CreateTable(User.__table__).compile(dialect=postgresql.dialect()))
