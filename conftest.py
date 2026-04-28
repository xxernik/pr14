import os
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app import create_app

TEST_DB_NAME = "library_test_db"

# 1. Конфігурація для адміністрування (ЗАВЖДИ підключаємось до 'postgres')
ADMIN_DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "dbname": "postgres", 
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "secret"),
}

# 2. Конфігурація для самої тестової БД
TEST_DB_CONFIG = ADMIN_DB_CONFIG.copy()
TEST_DB_CONFIG["dbname"] = TEST_DB_NAME

@pytest.fixture(scope="session")
def test_db():
    # Підключаємось до дефолтної БД 'postgres', щоб створити тестову
    conn = psycopg2.connect(**ADMIN_DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE);")
    cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")
    cur.close()
    conn.close()

    # Підключаємось до нової тестової БД для створення таблиць
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE authors (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            birth_year INT
        );
        CREATE TABLE books (
            id SERIAL PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            genre VARCHAR(100),
            year_published INT,
            author_id INT REFERENCES authors(id) ON DELETE SET NULL,
            created_by VARCHAR(255) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

    yield TEST_DB_CONFIG

    # Видаляємо тестову БД після всіх тестів (знову підключаємось до 'postgres')
    conn = psycopg2.connect(**ADMIN_DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE);")
    cur.close()
    conn.close()

@pytest.fixture(scope="session")
def app(test_db):
    app = create_app(test_db)
    yield app

@pytest.fixture(scope="function")
def client(app, test_db):
    conn = psycopg2.connect(**test_db)
    cur = conn.cursor()
    cur.execute("TRUNCATE books, authors RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()
    conn.close()
    return app.test_client()