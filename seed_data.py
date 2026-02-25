# load environment variables from .env before importing the app
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app import create_app
from services.sheets import GoogleSheetClient
import random

def seed_data():
    app = create_app()
    with app.app_context():
        print("Seeding books into Google Sheet...")
        client = GoogleSheetClient.get_instance()
        existing = client.books_for_user(1)  # user_id is always 1
        existing_titles = {b.get('title') for b in existing}

        # 2. Define Books
        books_data = [
            {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "status": "Completed", "total": 180},
            {"title": "1984", "author": "George Orwell", "status": "Reading", "total": 328},
            {"title": "To Kill a Mockingbird", "author": "Harper Lee", "status": "Planned", "total": 281},
            {"title": "Pride and Prejudice", "author": "Jane Austen", "status": "Completed", "total": 279},
            {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "status": "Planned", "total": 277},
            {"title": "The Hobbit", "author": "J.R.R. Tolkien", "status": "Reading", "total": 310},
            {"title": "Fahrenheit 451", "author": "Ray Bradbury", "status": "Completed", "total": 158},
            {"title": "The Alchemist", "author": "Paulo Coelho", "status": "Planned", "total": 163},
            {"title": "Brave New World", "author": "Aldous Huxley", "status": "Reading", "total": 268},
            {"title": "Moby Dick", "author": "Herman Melville", "status": "Planned", "total": 635},
        ]

        # 3. Add Books to sheet
        added_count = 0
        for data in books_data:
            if data["title"] in existing_titles:
                continue
            current_page = 0
            if data["status"] == "Completed":
                current_page = data["total"]
            elif data["status"] == "Reading":
                current_page = random.randint(10, data["total"] - 10)

            book = {
                'title': data["title"],
                'author': data["author"],
                'status': data["status"],
                'current_page': current_page,
                'total_pages': data["total"],
                'is_favourite': random.choice([True, False]),
                'user_id': 1,  # single user app
                'cover_image': '',
                'created_at': '',
            }
            client.append_book(book)
            added_count += 1

        print(f"Successfully added {added_count} books for 'testuser'.")

if __name__ == "__main__":
    seed_data()
