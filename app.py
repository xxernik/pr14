import os
from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor

DEFAULT_DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",
    "password": "secret",
    "host": "localhost",
    "port": 5432
}

def create_app(db_config=None):
    app = Flask(__name__)
    config = db_config if db_config else DEFAULT_DB_CONFIG

    def get_db_connection():
        return psycopg2.connect(**config)

    # --- AUTHORS ROUTES ---
    @app.route('/api/authors', methods=['GET'])
    def get_authors():
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM authors;")
                return jsonify(cur.fetchall()), 200

    @app.route('/api/authors', methods=['POST'])
    def create_author():
        data = request.get_json()
        if 'name' not in data:
            return jsonify({"error": "name is required"}), 400
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "INSERT INTO authors (name, birth_year) VALUES (%s, %s) RETURNING *;",
                    (data['name'], data.get('birth_year'))
                )
                new_author = cur.fetchone()
                conn.commit()
                return jsonify(new_author), 201

    @app.route('/api/authors/<int:author_id>', methods=['GET'])
    def get_author(author_id):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM authors WHERE id = %s;", (author_id,))
                author = cur.fetchone()
                if not author:
                    return jsonify({"error": "Author not found"}), 404
                return jsonify(author), 200

    @app.route('/api/authors/<int:author_id>', methods=['DELETE'])
    def delete_author(author_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM authors WHERE id = %s RETURNING id;", (author_id,))
                if not cur.fetchone():
                    return jsonify({"error": "Author not found"}), 404
                conn.commit()
                return '', 204

    @app.route('/api/authors/<int:author_id>/books', methods=['GET'])
    def get_author_books(author_id):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Перевірка чи існує автор
                cur.execute("SELECT id FROM authors WHERE id = %s;", (author_id,))
                if not cur.fetchone():
                    return jsonify({"error": "Author not found"}), 404
                
                cur.execute("SELECT * FROM books WHERE author_id = %s;", (author_id,))
                return jsonify(cur.fetchall()), 200

    # --- BOOKS ROUTES ---
    @app.route('/api/books', methods=['GET'])
    def get_books():
        genre = request.args.get('genre')
        author_id = request.args.get('author_id')
        q = request.args.get('q')

        query = "SELECT * FROM books WHERE 1=1"
        params = []

        if genre:
            query += " AND genre = %s"
            params.append(genre)
        if author_id:
            query += " AND author_id = %s"
            params.append(author_id)
        if q:
            query += " AND title ILIKE %s"
            params.append(f"%{q}%")

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return jsonify(cur.fetchall()), 200

    @app.route('/api/books', methods=['POST'])
    def create_book():
        data = request.get_json()
        if 'title' not in data:
            return jsonify({"error": "title is required"}), 400
        if 'created_by' not in data:
            return jsonify({"error": "created_by is required"}), 400

        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if 'author_id' in data and data['author_id'] is not None:
                    cur.execute("SELECT id FROM authors WHERE id = %s;", (data['author_id'],))
                    if not cur.fetchone():
                        return jsonify({"error": "Author not found"}), 400

                cur.execute(
                    """INSERT INTO books (title, genre, year_published, author_id, created_by) 
                       VALUES (%s, %s, %s, %s, %s) RETURNING *;""",
                    (data['title'], data.get('genre'), data.get('year_published'), 
                     data.get('author_id'), data['created_by'])
                )
                new_book = cur.fetchone()
                conn.commit()
                return jsonify(new_book), 201

    @app.route('/api/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM books WHERE id = %s;", (book_id,))
                book = cur.fetchone()
                if not book:
                    return jsonify({"error": "Book not found"}), 404
                return jsonify(book), 200

    @app.route('/api/books/<int:book_id>', methods=['DELETE'])
    def delete_book(book_id):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM books WHERE id = %s RETURNING id;", (book_id,))
                if not cur.fetchone():
                    return jsonify({"error": "Book not found"}), 404
                conn.commit()
                return '', 204

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)