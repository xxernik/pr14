import os
import pytest
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app import create_app, DEFAULT_DB_CONFIG

# Читаємо конфіг зі змінних середовища (з fallback на локальні значення)
TEST_DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
    "dbname": os.environ.get("POSTGRES_DB", "library_test_db"),
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": os.environ.get("POSTGRES_PASSWORD", "secret"),
}

TEST_DB_NAME = "library_test_db"

@pytest.fixture(scope="session")
def test_db():
    # Підключаємось до дефолтної БД, щоб створити тестову
    conn = psycopg2.connect(**TEST_DB_CONFIG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute(f"DROP DATABASE IF EXISTS {TEST_DB_NAME} WITH (FORCE);")
    cur.execute(f"CREATE DATABASE {TEST_DB_NAME};")
    cur.close()
    conn.close()

    # Налаштовуємо конфіг для тестової БД
    test_config = TEST_DB_CONFIG.copy()
    test_config["dbname"] = TEST_DB_NAME

    # Створюємо таблиці у тестовій БД
    conn = psycopg2.connect(**test_config)
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

    yield test_config

    # Видаляємо тестову БД після всіх тестів
    conn = psycopg2.connect(**TEST_DB_CONFIG)
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
    # Очищуємо таблиці перед кожним тестом
    conn = psycopg2.connect(**test_db)
    cur = conn.cursor()
    cur.execute("TRUNCATE books, authors RESTART IDENTITY CASCADE;")
    conn.commit()
    cur.close()
    conn.close()

    return app.test_client()