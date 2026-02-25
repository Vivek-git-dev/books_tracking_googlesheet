# Books Tracking App (Google Sheets Backend)

This Flask application tracks books you're reading, planning, or have completed.
Book data lives in a single Google Sheet. The application pulls all data on
startup and caches it in memory; API calls are made only when records change.
User authentication uses simple environment variable credentials (no database).

## Setup

1. Create a Google Cloud project and enable the **Google Sheets API**.
2. Create a **service account** and download the JSON key file.
3. Share your spreadsheet with the service account's email address.
4. In the spreadsheet ensure the first row contains the headers:
   `id,title,author,status,current_page,total_pages,is_favourite,user_id,cover_image,created_at`
5. Place the credentials file in `instance/credentials.json` or point
   `GOOGLE_CREDS_PATH` environment variable to it.
6. Set the `GOOGLE_SHEET_ID` environment variable to your sheet's ID.

You can either set environment variables directly or use a `.env` file at the
project root.  If you install `python-dotenv` (already in
`requirements.txt`), the app will load variables from `.env` automatically at
startup.

Example `.env` file:
```
GOOGLE_CREDS_PATH=C:\path\to\credentials.json
GOOGLE_SHEET_ID=1AbCdEfGhIjKlMnOpQrStuVwXyZ
SECRET_KEY=some-other-secret
```

Or set them manually in PowerShell:
```powershell
$env:GOOGLE_CREDS_PATH = "C:\path\to\credentials.json"
$env:GOOGLE_SHEET_ID = "1AbCdEfGhIjKlMnOpQrStuVwXyZ"
```

7. (Optional) install dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

8. Start the app:
```bash
flask run
```

## Notes

* All data (books) lives exclusively in Google Sheets. The app is fully
  database‑free with no SQLite or other persistent storage.
* The in‑memory cache is refreshed on any write operation.  If you modify the
  sheet externally you can restart the server or add a refresh endpoint.
* Templates continue to treat books as objects rather than dictionaries.

---

## Production & Deployment

This project is ready to run on platforms like **Fly.io** or any container
hosting service. A `Dockerfile` is included so the build can be controlled
precisely, and all secret material must be supplied via environment variables or
Fly secrets.

### Required environment variables

All of the following **must** be set; the application will abort during startup
if any are missing.

* `SECRET_KEY` – random bytes used by Flask sessions and CSRF protection.
* `AUTH_USERNAME` / `AUTH_PASSWORD` – credentials for the single login user.
* `GOOGLE_SHEET_ID` – the ID portion of your spreadsheet URL.
* **One** of the credentials inputs below:
  * `GOOGLE_CREDS_PATH` – path inside the container to a service account JSON
    file (not recommended on Fly).
  * `GOOGLE_CREDS_JSON` – raw JSON contents of the service account key.

Example (local `.env`):
```
SECRET_KEY=somesecretvalue
AUTH_USERNAME=admin
AUTH_PASSWORD=secret
GOOGLE_SHEET_ID=1AbCdEfGh...
GOOGLE_CREDS_JSON={"type": "service_account", ...}
```

On Fly you would use `fly secrets set` instead:
```powershell
flyctl secrets set \
  SECRET_KEY=$(openssl rand -hex 32) \
  AUTH_USERNAME=admin \
  AUTH_PASSWORD='superstrong' \
  GOOGLE_SHEET_ID=1AbCdEfGh... \
  GOOGLE_CREDS_JSON="$(cat path/to/credentials.json)"
```

### Building & running with Docker

The provided `Dockerfile` installs dependencies, copies the source, and
exposes port 8080 for the container.  The default command uses `gunicorn`
so the app runs with a production WSGI server.

Build and run locally:
```bash
docker build -t books-tracker .
docker run -e SECRET_KEY=... -e GOOGLE_SHEET_ID=... -p 8080:8080 books-tracker
```

### Fly.io specific notes

1. Install the [Fly CLI](https://fly.io/docs/getting-started/installing/).
2. `flyctl launch` in the project root; choose an app name or keep the
   suggested one.  The tool will create `fly.toml`.
3. Set your secrets (`flyctl secrets set ...` as shown above).
4. `flyctl deploy` will build using the `Dockerfile` and push the image.
5. The app listens on `$PORT` and binds to `0.0.0.0`; these are configured
   automatically by Fly.

Once deployed you can open the public URL with `flyctl open`.

---

For local development the previous instructions still apply; environment
variables can be stored in a `.env` file and the Flask development server
started with `flask run`.  Remember never to commit real credentials.
