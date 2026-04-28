import pytest
MY_NAME = "Ернест Стоянович" 
class TestBooks:
    def test_get_books_empty(self, client):
        response = client.get("/api/books")
        assert response.status_code == 200
        assert response.get_json() == []

    def test_create_book(self, client):
        response = client.post("/api/books", json={
            "title": "knyga",
            "genre": "poetry",
            "year_published": 2007,
            "created_by": MY_NAME
        })
        assert response.status_code == 201
        data = response.get_json()
        assert data["title"] == "knyga"
        assert data["created_by"] == MY_NAME

    def test_create_book_without_title(self, client):
        response = client.post("/api/books", json={"created_by": MY_NAME})
        assert response.status_code == 400

    def test_create_book_without_created_by(self, client):
        response = client.post("/api/books", json={"title": "knyga"})
        assert response.status_code == 400

    def test_create_book_with_author(self, client):
        author = client.post("/api/authors", json={"name": "Ернест стоянович"}).get_json()
        response = client.post("/api/books", json={
            "title": "Lisova Pisnia",
            "author_id": author["id"],
            "created_by": MY_NAME
        })
        assert response.status_code == 201
        assert response.get_json()["author_id"] == author["id"]

    def test_create_book_with_nonexistent_author(self, client):
        response = client.post("/api/books", json={
            "title": "Ghost Book",
            "author_id": 999,
            "created_by": MY_NAME
        })
        assert response.status_code == 400

    def test_get_book_by_id(self, client):
        book = client.post("/api/books", json={
            "title": "knyga2",
            "created_by": MY_NAME
        }).get_json()
        
        response = client.get(f"/api/books/{book['id']}")
        assert response.status_code == 200
        assert response.get_json()["title"] == "knyga2"

    def test_get_book_not_found(self, client):
        response = client.get("/api/books/999")
        assert response.status_code == 404

    def test_delete_book(self, client):
        book = client.post("/api/books", json={
            "title": "To Delete",
            "created_by": MY_NAME
        }).get_json()
        
        response = client.delete(f"/api/books/{book['id']}")
        assert response.status_code == 204
        
        get_response = client.get(f"/api/books/{book['id']}")
        assert get_response.status_code == 404

    def test_create_book_default_status(self, client):
        """Книга створюється зі статусом за замовчуванням"""
        response = client.post("/api/books", json={
            "title": "Test Book PR",
            "created_by": "Ернест Стоянович",
        })
        assert response.status_code == 201

class TestBooksFilter:
    def test_filter_by_genre(self, client):
        client.post("/api/books", json={"title": "Book 1", "genre": "poetry", "created_by": MY_NAME})
        client.post("/api/books", json={"title": "Book 2", "genre": "novel", "created_by": MY_NAME})
        
        response = client.get("/api/books?genre=poetry")
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Book 1"

    def test_filter_by_author_id(self, client):
        author1 = client.post("/api/authors", json={"name": "Author 1"}).get_json()
        author2 = client.post("/api/authors", json={"name": "Author 2"}).get_json()
        
        client.post("/api/books", json={"title": "A1B1", "author_id": author1["id"], "created_by": MY_NAME})
        client.post("/api/books", json={"title": "A2B1", "author_id": author2["id"], "created_by": MY_NAME})
        
        response = client.get(f"/api/books?author_id={author1['id']}")
        assert len(response.get_json()) == 1
        assert response.get_json()[0]["title"] == "A1B1"

    def test_search_by_title(self, client):
        client.post("/api/books", json={"title": "knyga", "created_by": MY_NAME})
        client.post("/api/books", json={"title": "knyga2", "created_by": MY_NAME})
        
        response = client.get("/api/books?q=knyga")
        assert len(response.get_json()) == 1
        assert response.get_json()[0]["title"] == "knyga"

    def test_filter_no_results(self, client):
        client.post("/api/books", json={"title": "knyga", "genre": "poetry", "created_by": MY_NAME})
        response = client.get("/api/books?genre=scifi")
        assert response.status_code == 200
        assert response.get_json() == []