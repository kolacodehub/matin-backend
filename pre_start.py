import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'matin.settings')
django.setup()

def setup_schema():
    with connection.cursor() as cursor:
        print("Creating private schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS matin_schema;")
        cursor.execute("GRANT ALL ON SCHEMA matin_schema TO PUBLIC;")
        print("Schema matin_schema is ready!")

if __name__ == "__main__":
    setup_schema()