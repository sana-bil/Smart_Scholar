import pyodbc

try:
    conn = pyodbc.connect(
        'Driver={ODBC Driver 17 for SQL Server};'
        'Server=DESKTOP-2G14Q4N\MSSQLSERVER01;'
        'Trusted_Connection=yes;'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT @@version")
    print("SQL Server Connected Successfully!")
    print(cursor.fetchone()[0])
    conn.close()
except Exception as e:
    print(f"Connection Failed: {e}")
    print("Make sure SQL Server is running and server name is correct")