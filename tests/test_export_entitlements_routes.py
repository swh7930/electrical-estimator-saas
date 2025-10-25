import pytest
from werkzeug.exceptions import Forbidden
from app.extensions import db
from app.models import Org, User, Estimate, Subscription

def _login(client, user_id: int):
    # Simulate Flask-Login session
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)

def _make_org_user(app):
    with app.app_context():
        org = Org(name="Exports Org")
        db.session.add(org)
        db.session.commit()

        u = User(email="pro@example.com", org_id=org.id)
        u.set_password("testpass")
        db.session.add(u)
        db.session.commit()
        return org.id, u.id
    
def _make_estimate(app, org_id: int):
    with app.app_context():
        est = Estimate(name="Test Estimate", org_id=org_id)
        # Minimal payload; export code tolerates missing fields
        est.work_payload = {}
        db.session.add(est)
        db.session.commit()
        return est.id

def test_saved_export_csv_blocks_without_entitlement(app, client):
    org_id, u_id = _make_org_user(app)
    est_id = _make_estimate(app, org_id)
    _login(client, u_id)
    resp = client.get(f"/estimates/{est_id}/export/summary.csv")
    assert resp.status_code == 403

def test_saved_export_csv_allows_with_entitlement(app, client):
    org_id, u_id = _make_org_user(app)
    est_id = _make_estimate(app, org_id)                 # <-- use est_id
    with app.app_context():
        sub = Subscription(
            org_id=org_id,
            stripe_subscription_id="sub_test_1",
            product_id="prod_test",
            price_id="price_test",
            status="active",
            entitlements_json=["exports.csv", "exports.pdf"],
        )
        db.session.add(sub); db.session.commit()

    _login(client, u_id)
    resp = client.get(f"/estimates/{est_id}/export/summary.csv")   # <-- use est_id
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type", "").startswith("text/csv")

def test_fast_export_csv_blocks_without_entitlement(app, client):
    org_id, u_id = _make_org_user(app)

    _login(client, u_id)
    resp = client.post(
        "/estimates/exports/summary.csv",
        json={"summary_export": {"controls": {}}},  # minimal valid shape
        headers={"Accept": "application/json"}
    )
    assert resp.status_code == 403
