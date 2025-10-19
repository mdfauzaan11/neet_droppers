import csv
import mysql.connector

# -------------------
# MySQL connection
# -------------------
db = mysql.connector.connect(
    host="localhost",
    user="root",          # your MySQL username
    password="Fauzaan@123", # your MySQL password
    database="neetdb"     # your database name
)

cursor = db.cursor()

# -------------------
# CSV file path
# -------------------
csv_file_path = "mock_tests.csv"  # place this file in your project folder

# -------------------
# Import CSV into MySQL
# -------------------
with open(csv_file_path, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header row
    for row in reader:
        sql = """
            INSERT INTO mock_tests
            (subject, chapter, question, option_a, option_b, option_c, option_d, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, row)

db.commit()
print("CSV imported successfully!")

cursor.close()
db.close()
