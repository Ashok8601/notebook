import sqlite3

DATABASE = "notebook.db"


def create_connection():
    connection = sqlite3.connect(DATABASE)
    return connection


def create_tables():

    connection = create_connection()
    cursor = connection.cursor()

    # USER TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        dob TEXT,
        is_deleted INTEGER DEFAULT 0,
        delete_request_at TEXT
    )
    """)

    # NOTEBOOK TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notebook(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        content TEXT,
        category TEXT,
        user_id INTEGER,
        created_at TEXT,
        is_deleted INTEGER DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_tables()
    print("Database and tables created successfully.")