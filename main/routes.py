from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from services.sheets import GoogleSheetClient
from types import SimpleNamespace

main_bp = Blueprint('main', __name__)


def _to_obj(book_dict):
    """Convert a book dictionary into an object for template consumption."""
    return SimpleNamespace(**book_dict)


@main_bp.route('/')
@login_required
def index():
    client = GoogleSheetClient.get_instance()
    books = [ _to_obj(b) for b in client.books_for_user(current_user.id) ]

    # categorise the list in memory (previously done via ORM queries)
    reading = [b for b in books if b.status == 'Reading']
    planned = [b for b in books if b.status == 'Planned']
    completed = [b for b in books if b.status == 'Completed']
    favourites = [b for b in books if b.is_favourite]

    hero_book = reading[0] if reading else None
    # Queue shows only Reading and Planned books (exclude Completed from this view)
    queue_books = [b for b in books if b != hero_book and b.status != 'Completed']
    status_order = {'Reading': 1, 'Planned': 2, 'Completed': 3}
    queue_books.sort(key=lambda x: status_order.get(x.status, 4))

    return render_template(
        'index.html',
        hero_book=hero_book,
        queue_books=queue_books,
        reading_count=len(reading),
        planned_count=len(planned),
        completed_count=len(completed),
        favourites=favourites,
    )


@main_bp.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        client = GoogleSheetClient.get_instance()
        # coerce numeric fields to ints so templates can perform arithmetic
        current_page = request.form.get('current_page', 0)
        total_pages = request.form.get('total_pages', 0)
        try:
            current_page = int(current_page)
        except (TypeError, ValueError):
            current_page = 0
        try:
            total_pages = int(total_pages)
        except (TypeError, ValueError):
            total_pages = 0

        book_data = {
            'title': request.form.get('title'),
            'author': request.form.get('author'),
            'status': request.form.get('status'),
            'current_page': current_page,
            'total_pages': total_pages,
            'is_favourite': False,
            'user_id': current_user.id,
            'cover_image': request.form.get('cover_image', ''),
            'created_at': '',
        }
        client.append_book(book_data)
        flash('Book added to tracking system')
        return redirect(url_for('main.index'))

    return render_template('add_book.html')


@main_bp.route('/book/<int:id>/update', methods=['POST'])
@login_required
def update_book(id):
    client = GoogleSheetClient.get_instance()
    # find the book dict and convert to object for easier attribute access
    book_dict = next((b for b in client.fetch_all_books() if b.get('id') == id), None)
    if not book_dict or book_dict.get('user_id') != current_user.id:
        flash('Access Denied')
        return redirect(url_for('main.index'))

    action = request.form.get('action')
    updates = {}

    if action == 'delete':
        client.delete_book(id)
        flash(f'Book "{book_dict.get("title")}" deleted')
        return redirect(url_for('main.index'))
    elif action == 'update_progress':
        new_page = int(request.form.get('current_page', book_dict.get('current_page', 0)))
        updates['current_page'] = new_page
        if new_page >= int(book_dict.get('total_pages', 0)) and int(book_dict.get('total_pages', 0)) > 0:
            updates['status'] = 'Completed'
        client.update_book(id, updates)
    elif action == 'change_status':
        updates['status'] = request.form.get('status')
        client.update_book(id, updates)
    elif action == 'toggle_favourite':
        updates['is_favourite'] = not book_dict.get('is_favourite', False)
        client.update_book(id, updates)
        return redirect(request.referrer or url_for('main.index'))

    return redirect(url_for('main.index'))


@main_bp.route('/book/<int:id>')
@login_required
def book_details(id):
    client = GoogleSheetClient.get_instance()
    book_dict = next((b for b in client.fetch_all_books() if b.get('id') == id), None)
    if not book_dict or book_dict.get('user_id') != current_user.id:
        flash('Access Denied')
        return redirect(url_for('main.index'))
    book = _to_obj(book_dict)
    return render_template('book_details.html', book=book)


@main_bp.route('/book/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(id):
    client = GoogleSheetClient.get_instance()
    book_dict = next((b for b in client.fetch_all_books() if b.get('id') == id), None)
    if not book_dict or book_dict.get('user_id') != current_user.id:
        flash('Access Denied')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        updates = {
            'title': request.form.get('title'),
            'author': request.form.get('author'),
            'status': request.form.get('status'),
            'current_page': int(request.form.get('current_page', 0)),
            'total_pages': int(request.form.get('total_pages', 0)),
            'cover_image': request.form.get('cover_image'),
            'is_favourite': True if request.form.get('is_favourite') else False,
        }
        if updates['current_page'] >= updates['total_pages'] and updates['total_pages'] > 0:
            if book_dict.get('status') != 'Completed':
                updates['status'] = 'Completed'
                flash('Book marked as Completed due to progress')

        client.update_book(id, updates)
        flash('Book details updated')
        return redirect(url_for('main.book_details', id=id))

    book = _to_obj(book_dict)
    return render_template('edit_book.html', book=book)


@main_bp.route('/favourites')
@login_required
def favourites():
    client = GoogleSheetClient.get_instance()
    books = [ _to_obj(b) for b in client.books_for_user(current_user.id) if b.get('is_favourite') ]
    return render_template('favourites.html', favourites=books)


@main_bp.route('/all_books')
@login_required
def all_books():
    client = GoogleSheetClient.get_instance()
    books = [ _to_obj(b) for b in client.books_for_user(current_user.id) ]
    # sort by status then title
    books.sort(key=lambda x: (x.status or '', x.title or ''))
    return render_template('all_books.html', books=books)

