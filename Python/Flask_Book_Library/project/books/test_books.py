import pytest
from project import app as flask_app, db as flask_db
from project.books.models import Book

@pytest.fixture(scope="module")
def app():
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    })

    with flask_app.app_context():
        yield flask_app

@pytest.fixture(scope="function")
def session(app):
    flask_db.create_all()
    yield flask_db.session
    flask_db.session.remove()
    flask_db.drop_all()

def test_create_book_valid_default_status(session):
    book = Book(
        name="Sample Book",
        author="John Doe",
        year_published=2020,
        book_type="Fiction"
    )
    session.add(book)
    session.commit()

    stored = Book.query.filter_by(name="Sample Book").first()
    assert stored is not None
    assert stored.author == "John Doe"
    assert stored.year_published == 2020
    assert stored.book_type == "Fiction"
    assert stored.status == "available"

def test_create_book_valid_given_status(session):
    book = Book(
        name="Status Book",
        author="John Doe",
        year_published=2020,
        book_type="Fiction",
        status="unavailable"
    )
    session.add(book)
    session.commit()

    stored = Book.query.filter_by(name="Status Book").first()
    assert stored is not None
    assert stored.status == "unavailable"

def test_create_book_missing_name(session):
    with pytest.raises(Exception):
        book = Book(
            name=None,
            author="John Doe",
            year_published=2020,
            book_type="Fiction"
        )
        session.add(book)
        session.commit()

def test_create_book_invalid_year(session):
    with pytest.raises(Exception):
        book = Book(
            name="Invalid Year Book",
            author="Jane Doe",
            year_published="abcd",
            book_type="Fiction"
        )
        session.add(book)
        session.commit()

def test_create_book_name_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="a"*65,
            author="Jane Doe",
            year_published=2024,
            book_type="Fiction"
        )
        session.add(book)
        session.commit()

def test_create_book_author_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="a"*65,
            year_published=2024,
            book_type="Fiction"
        )
        session.add(book)
        session.commit()

def test_create_book_book_type_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="Jane Doe",
            year_published=2024,
            book_type="a"*21
        )
        session.add(book)
        session.commit()

def test_create_book_book_type_too_long(session):
    with pytest.raises(Exception):
        book = Book(
            name="Sample Book",
            author="Jane Doe",
            year_published=2024,
            book_type="Fiction",
            status="a"*21
        )
        session.add(book)
        session.commit()

def test_create_book_name_not_unique(session):
    book1 = Book(
            name="Sample Book",
            author="John Doe",
            year_published=2020,
            book_type="Fiction"
        )
    book2 = Book(
            name="Sample Book",
            author="John Doe2",
            year_published=2022,
            book_type="Fiction"
        )
    with pytest.raises(Exception):
        session.add(book1)
        session.add(book2)
        session.commit()

def test_sql_injection(session):
    malicious_name = "Book'); DROP TABLE books;--"
    book = Book(
        name=malicious_name,
        author="Hacker",
        year_published=2023,
        book_type="Fiction"
    )
    with pytest.raises(Exception):
        session.add(book)
        session.commit()

def test_javascript_injection(session):
    malicious_name = "<script>alert('Hacked!');</script>"
    book = Book(
        name=malicious_name,
        author="Hacker",
        year_published=2023,
        book_type="Fiction"
    )
    with pytest.raises(Exception):
        session.add(book)
        session.commit()

def test_extremely_long_input(session):
    long_value = "a" * 10000

    fields_to_test = ["name", "author", "book_type", "status"]

    for field in fields_to_test:
        data = {
            "name": "Normal Name",
            "author": "Normal Author",
            "year_published": 2023,
            "book_type": "Fiction",
            "status": "available"
        }

        data[field] = long_value

        book = Book(**data)
        session.add(book)
        session.commit()

        stored = Book.query.filter_by(**{field: long_value}).first()

        assert stored is not None
        assert getattr(stored, field) == long_value
        assert len(getattr(stored, field)) == 10000

        session.delete(stored)
        session.commit()

def test_negative_year(session):
    book = Book(
        name="Boundary Year Book",
        author="Author",
        year_published=-2,
        book_type="Non-Fiction"
    )
    # negative year should not be possible
    with pytest.raises(Exception):
        session.add(book)
        session.commit()
