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

    # stub service call to avoid Stripe network (patch the name imported in the route)
    from app.blueprints.billing import routes as billing_routes
    def _fake_checkout_session(price_id: str, org_id: int):
        return {"url": f"https://stripe.example/checkout?price_id={price_id}&org_id={org_id}"}
    monkeypatch.setattr(billing_routes, "create_checkout_session", _fake_checkout_session)

    with app.app_context():
        org = Org(name="Checkout Org")
        db.session.add(org)
        db.session.commit()

        u = User(email="buyer@example.com", org_id=org.id)
        u.set_password("test")
        db.session.add(u)
        db.session.commit()
        uid = u.id

    _login(client, uid)

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
        u.set_password("x")  
        db.session.add(u)
        db.session.commit()
        uid = u.id

        s = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_live",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
            entitlements_json=[],
        )
        db.session.add(s)
        db.session.commit()

    _login(client, uid)

    resp = client.post("/billing/checkout", data={"price_id": "price_pro_monthly"})
    assert resp.status_code == 409
