import pytest
from app.extensions import db
from app.models import Org, User, Subscription, OrgMembership, ROLE_ADMIN

def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)

def _make_org_user(app, role=ROLE_ADMIN):
    with app.app_context():
        org = Org(name="Coarse Org")
        db.session.add(org); db.session.commit()
        u = User(email="coarse@example.com")
        u.set_password("x"); u.org_id = org.id
        db.session.add(u); db.session.commit()
        m = OrgMembership(org_id=org.id, user_id=u.id, role=role)
        db.session.add(m); db.session.commit()
        return org.id, u.id

def test_estimator_requires_active_html_redirects_to_billing(app, client):
    org_id, u_id = _make_org_user(app)
    _login(client, u_id)
    resp = client.get("/estimator/", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/billing" in (resp.headers.get("Location") or "")

def test_estimates_requires_active_json_returns_403(app, client):
    org_id, u_id = _make_org_user(app)
    _login(client, u_id)
    # list.json triggers JSON path suffix detection
    resp = client.get("/estimates/list.json")
    assert resp.status_code == 403
    assert resp.is_json
    data = resp.get_json()
    assert data.get("error") == "entitlement_required"
    assert data.get("missing") == "active_subscription"

def test_cancel_at_period_end_treated_active(app, client):
    org_id, u_id = _make_org_user(app)
    with app.app_context():
        sub = Subscription(org_id=org_id, stripe_subscription_id="sub_x", product_id="prod", price_id="price",
                           status="active", cancel_at_period_end=True, entitlements_json=["exports.csv","exports.pdf"])
        db.session.add(sub); db.session.commit()
    _login(client, u_id)
    resp = client.get("/estimator/")
    assert resp.status_code == 200

def test_past_due_blocked_but_billing_allowed(app, client):
    org_id, u_id = _make_org_user(app)
    with app.app_context():
        sub = Subscription(org_id=org_id, stripe_subscription_id="sub_y", product_id="prod", price_id="price",
                           status="past_due", entitlements_json=["exports.csv","exports.pdf"])
        db.session.add(sub); db.session.commit()
    _login(client, u_id)
    # Product surface blocked
    resp = client.get("/estimator/", follow_redirects=False)
    assert resp.status_code in (302, 303)
    assert "/billing" in (resp.headers.get("Location") or "")
    # Billing page still reachable
    resp2 = client.get("/billing")
    assert resp2.status_code == 200
