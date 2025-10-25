import pytest
from app.extensions import db
from app.models import Org, User, Subscription

def _login(client, user_id: int):
    # Simulate Flask-Login session
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)

def test_checkout_creates_session_and_redirects(app, client, monkeypatch):
    # Disable CSRF for this route call in tests
    app.config["WTF_CSRF_ENABLED"] = False

    # Ensure env price id is present for rendering (not strictly required for POST)
    app.config["STRIPE_PRICE_PRO_MONTHLY"] = "price_pro_monthly"

    # stub service call to avoid Stripe network
    from app.services import billing as svc

    def _fake_checkout_session(price_id, org_id, user_id):
        assert price_id == "price_pro_monthly"
        assert isinstance(org_id, int) and isinstance(user_id, int)
        return {"id": "cs_test_123", "url": "https://stripe.example/checkout"}

    monkeypatch.setattr(svc, "create_checkout_session", _fake_checkout_session)

    with app.app_context():
        org = Org(name="Checkout Org")
        db.session.add(org)
        db.session.commit()

        u = User(email="buyer@example.com", org_id=org.id)
        u.set_password("test")
        db.session.add(u)
        db.session.commit()

    _login(client, u.id)

    resp = client.post("/billing/checkout", data={"price_id": "price_pro_monthly"}, follow_redirects=False)
    assert resp.status_code == 303
    assert resp.headers["Location"].startswith("https://stripe.example/checkout")

def test_checkout_conflict_when_active_subscription(app, client):
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        org = Org(name="Active Org")
        db.session.add(org)
        db.session.commit()

        u = User(email="active@example.com", org_id=org.id)
        db.session.add(u)
        db.session.commit()

        s = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_live",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
        )
        db.session.add(s)
        db.session.commit()

    _login(client, u.id)

    resp = client.post("/billing/checkout", data={"price_id": "price_pro_monthly"})
    assert resp.status_code == 409
