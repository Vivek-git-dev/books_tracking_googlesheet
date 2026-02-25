import os
import unittest
# ensure minimum env variables so Config class doesn't raise
os.environ.setdefault('SECRET_KEY', 'testing-key')
os.environ.setdefault('AUTH_USERNAME', 'testuser')
os.environ.setdefault('AUTH_PASSWORD', 'password')
os.environ.setdefault('GOOGLE_SHEET_ID', 'fake-sheet')
os.environ.setdefault('GOOGLE_CREDS_JSON', '{}')

from app import create_app

# simple in-memory fake sheet client used during tests
class FakeSheetClient:
    def __init__(self):
        self._books = []

    def books_for_user(self, user_id):
        return [b for b in self._books if b.get('user_id') == user_id]

    def fetch_all_books(self):
        return list(self._books)

    def append_book(self, book_data):
        book_data = book_data.copy()
        book_data['id'] = len(self._books) + 1
        self._books.append(book_data)
        return book_data['id']

    def update_book(self, book_id, updates):
        for b in self._books:
            if b.get('id') == book_id:
                b.update(updates)
                return True
        return False

    def delete_book(self, book_id):
        for i, b in enumerate(self._books):
            if b.get('id') == book_id:
                self._books.pop(i)
                return True
        return False


def patch_sheets(app):
    # replace the real client singleton with fake
    from services import sheets
    sheets.GoogleSheetClient._instance = FakeSheetClient()


class TestBookTracker(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

        with self.app.app_context():
            patch_sheets(self.app)

    def login(self, username, password):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_auth_and_dashboard(self):
        # Login with env credentials (testuser/password)
        resp = self.login('testuser', 'password')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'read', resp.data.lower())

    def test_invalid_credentials(self):
        # Try logging in with wrong credentials
        resp = self.login('wronguser', 'wrongpass')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'invalid', resp.data.lower())

    def test_add_book_logged_in(self):
        # Login first
        self.login('testuser', 'password')
        # Add a book
        resp = self.client.post('/add_book', data=dict(
            title='Test Book',
            author='Test Author',
            status='Reading',
            current_page=0,
            total_pages=100
        ), follow_redirects=True)
        # the book was added successfully if we don't get an error
        self.assertEqual(resp.status_code, 200)


if __name__ == '__main__':
    unittest.main()
