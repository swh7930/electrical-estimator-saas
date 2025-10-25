import os
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
        MAIL_SUPPRESS_SEND=True,
        APP_BASE_URL="http://example.test",
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=True,
    )
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
