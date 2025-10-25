import os
# Ensure the app factory picks the Testing config & SQLite memory DB
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("TEST_DATABASE_URL", "sqlite:///:memory:")
# Webhook tests read this at import time
os.environ.setdefault("EMAIL_WEBHOOK_SECRET", "testsecret")

import pytest
from app import create_app
from app.extensions import db

@pytest.fixture(scope="session")
def app():
    os.environ.setdefault("EMAIL_WEBHOOK_SECRET", "testsecret")
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_EXPIRE_ON_COMMIT=False,  # avoid DetachedInstanceError in tests
        MAIL_SUPPRESS_SEND=True,
        APP_BASE_URL="http://example.test",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=True,
        APP_ENV="test",
        EMAIL_WEBHOOK_SECRET=os.environ.get("EMAIL_WEBHOOK_SECRET", "testsecret"),
    )
    with app.app_context():
        db.create_all()
         db.session.expire_on_commit = False
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def _db_clean(app):
    # Clean BEFORE each test
    with app.app_context():
        db.session.rollback()
        for tbl in reversed(db.metadata.sorted_tables):
            db.session.execute(tbl.delete())
        db.session.commit()
    yield
    # And AFTER each test (keeps state hermetic even if a test fails mid-transaction)
    with app.app_context():
        db.session.rollback()
        for tbl in reversed(db.metadata.sorted_tables):
            db.session.execute(tbl.delete())
        db.session.commit()
