from flask import current_app
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from threading import Lock
from types import SimpleNamespace

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The header row we expect on the spreadsheet.  This must match the sheet's first
# row exactly.  Adjust if you add/remove fields in the Google Sheet.
FIELDS = [
    'id',
    'title',
    'author',
    'status',
    'current_page',
    'total_pages',
    'is_favourite',
    'user_id',
    'cover_image',
    'created_at',
]


class GoogleSheetClient:
    """Singleton wrapper around the Google Sheets API that also keeps a simple
    in-memory cache of the books.

    The cache is populated the first time ``fetch_all_books`` is called and
    refreshed any time we make a mutating request (append/update/delete).
    """

    _instance = None
    _lock = Lock()

    def __init__(self):
        scopes = SCOPES
        creds = None

        # support credentials either via a file path or raw JSON string (useful
        # for containerized deployments where mounting a file is inconvenient)
        creds_json = current_app.config.get('GOOGLE_CREDS_JSON')
        if creds_json:
            try:
                info = json.loads(creds_json)
            except Exception as e:
                raise RuntimeError('Invalid JSON in GOOGLE_CREDS_JSON') from e
            creds = Credentials.from_service_account_info(info, scopes=scopes)
        else:
            creds_path = current_app.config.get('GOOGLE_CREDS_PATH')
            if not creds_path:
                raise RuntimeError('GOOGLE_CREDS_PATH not set in configuration')
            creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        self.service = build('sheets', 'v4', credentials=creds)
        self.spreadsheet_id = current_app.config.get('GOOGLE_SHEET_ID')
        if not self.spreadsheet_id:
            raise RuntimeError('GOOGLE_SHEET_ID not set in configuration')

        # load header and cache on first use
        self.header = self._get_header()
        if self.header != FIELDS:
            # if you change the FIELDS constant make sure the sheet headers
            # match or the code below will behave unpredictably.
            raise RuntimeError(
                f"Sheet header mismatch: expected {FIELDS}, got {self.header}"
            )
        self.cache = []
        self._load_cache()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = GoogleSheetClient()
            return cls._instance

    def _get_header(self):
        # read the first row of the sheet, which should contain field names
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range='Sheet1!1:1')
            .execute()
        )
        values = result.get('values', [])
        return values[0] if values else []

    def _load_cache(self):
        # grab all data rows starting at row 2
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.spreadsheet_id, range='Sheet1!A2:J')
            .execute()
        )
        rows = result.get('values', [])
        self.cache = []
        for idx, row in enumerate(rows, start=2):
            # zip row to header, fill missing cols with empty string
            data = {k: row[i] if i < len(row) else '' for i, k in enumerate(self.header)}
            data['_row'] = idx
            self.cache.append(self._normalize_book(data))

    def _normalize_book(self, book):
        # convert types and provide defaults
        try:
            book['id'] = int(book.get('id')) if book.get('id') not in (None, '') else None
        except ValueError:
            book['id'] = None
        book['current_page'] = int(book.get('current_page') or 0)
        book['total_pages'] = int(book.get('total_pages') or 0)
        book['is_favourite'] = str(book.get('is_favourite')).lower() in ('true', '1', 'yes')
        try:
            book['user_id'] = int(book.get('user_id') or 0)
        except ValueError:
            book['user_id'] = 0
        # other fields stay as strings
        return book

    def fetch_all_books(self):
        if not self.cache:
            self._load_cache()
        return self.cache

    # helper to convert a dict to a SimpleNamespace for template consumption
    def book_obj(self, d):
        return SimpleNamespace(**d)

    def append_book(self, book_dict):
        # assign a new numeric id sequence if not provided
        ids = [b['id'] for b in self.cache if b.get('id') is not None]
        next_id = max(ids, default=0) + 1
        book_dict['id'] = next_id
        # ensure fields are strings for the sheet
        values = [book_dict.get(f, '') for f in self.header]
        body = {'values': [values]}
        self.service.spreadsheets().values().append(
            spreadsheetId=self.spreadsheet_id,
            range='Sheet1!A:Z',
            valueInputOption='USER_ENTERED',
            body=body,
        ).execute()
        self._load_cache()
        return book_dict['id']

    def update_book(self, book_id, updates):
        book = next((b for b in self.cache if b.get('id') == book_id), None)
        if not book:
            return False
        # apply updates in cache copy
        book.update(updates)
        row = book['_row']
        values = [book.get(f, '') for f in self.header]
        body = {'values': [values]}
        self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f'Sheet1!A{row}:Z{row}',
            valueInputOption='USER_ENTERED',
            body=body,
        ).execute()
        self._load_cache()
        return True

    def delete_book(self, book_id):
        book = next((b for b in self.cache if b.get('id') == book_id), None)
        if not book:
            return False
        row = book['_row']
        self.service.spreadsheets().values().clear(
            spreadsheetId=self.spreadsheet_id,
            range=f'Sheet1!A{row}:Z{row}'
        ).execute()
        self._load_cache()
        return True

    # convenience filtering
    def books_for_user(self, user_id):
        if not self.cache:
            self._load_cache()
        return [b for b in self.cache if b.get('user_id') == user_id]
