import mysql.connector

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="your_mysql_user",
        password="your_mysql_password",
        database="your_database_name"
    )

def create_user_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255),
            kakao_id VARCHAR(255) UNIQUE
        )
    """)

    # Insert example entries (use INSERT IGNORE to avoid duplicates in MySQL)
    cursor.execute("INSERT IGNORE INTO users (email, password) VALUES (%s, %s)", 
                   ("donor1@example.com", "password123"))
    cursor.execute("INSERT IGNORE INTO users (kakao_id) VALUES (%s)", 
                   ("kakao_abc123",))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_user_table()
