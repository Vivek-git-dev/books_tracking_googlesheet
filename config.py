import os
import json

class Config:
    # secret key must be provided by environment; no defaults allowed in prod
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise RuntimeError('SECRET_KEY environment variable must be set')

    # Authentication via environment variables (no database)
    AUTH_USERNAME = os.environ.get('AUTH_USERNAME')
    AUTH_PASSWORD = os.environ.get('AUTH_PASSWORD')
    if not AUTH_USERNAME or not AUTH_PASSWORD:
        raise RuntimeError('AUTH_USERNAME and AUTH_PASSWORD must be set')

    # Google Sheets configuration
    # either provide a path to a service account JSON or the raw JSON itself
    GOOGLE_CREDS_PATH = os.environ.get('GOOGLE_CREDS_PATH')
    GOOGLE_CREDS_JSON = os.environ.get('GOOGLE_CREDS_JSON')
    if not (GOOGLE_CREDS_PATH or GOOGLE_CREDS_JSON):
        # allow the instance/credentials.json file when running locally, but
        # make it explicit in production setups
        if not os.path.exists(os.path.join(os.getcwd(), 'instance', 'credentials.json')):
            raise RuntimeError('Either GOOGLE_CREDS_PATH or GOOGLE_CREDS_JSON must be set and point to valid credentials')

    # the ID portion of the spreadsheet URL (e.g. docs.google.com/spreadsheets/d/<ID>/...)
    GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID')
    if not GOOGLE_SHEET_ID:
        raise RuntimeError('GOOGLE_SHEET_ID environment variable must be set')
