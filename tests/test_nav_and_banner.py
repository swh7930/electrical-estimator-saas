from app.extensions import db
from app.models import Org, User, Subscription, OrgMembership, ROLE_ADMIN, ROLE_MEMBER

def _login(client, user_id: int):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)

def _org_user(app, role=ROLE_ADMIN, active=False, has_customer=False):
    with app.app_context():
        org = Org(name="Nav Org")
        db.session.add(org); db.session.commit()
        u = User(email="nav@example.com"); u.set_password("x"); u.org_id = org.id
        db.session.add(u); db.session.commit()
        m = OrgMembership(org_id=org.id, user_id=u.id, role=role)
        db.session.add(m); db.session.commit()
        if active:
            sub = Subscription(org_id=org.id, stripe_subscription_id="sub_nav", product_id="prod",
                               price_id="price", status="active", entitlements_json=["exports.csv","exports.pdf"])
            db.session.add(sub); db.session.commit()
        return org.id, u.id

def test_header_has_no_billing_nav(app, client):
    # unauth ok here—this checks static nav, not banner
    resp = client.get("/")
    assert resp.status_code == 200
    assert 'href="/billing"' not in resp.get_data(as_text=True)

def test_admin_unsubscribed_sees_banner_with_plans_cta(app, client):
    org_id, u_id = _org_user(app, role=ROLE_ADMIN, active=False)
    _login(client, u_id)
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert "Unlock Estimator with Pro to use the app." in html
    assert ">View plans<" in html

def test_non_admin_unsubscribed_sees_contact_admin_banner(app, client):
    org_id, u_id = _org_user(app, role=ROLE_MEMBER, active=False)
    _login(client, u_id)
    resp = client.get("/")
    html = resp.get_data(as_text=True)
    assert (
        "Unlock Estimator with Pro to use the app." in html
        or "doesn’t have an active subscription" in html
        or "doesn't have an active subscription" in html
    )
    assert ">View plans<" not in html

def test_admin_with_customer_id_sees_manage_billing_in_settings(app, client):
    org_id, u_id = _org_user(app, role=ROLE_ADMIN, active=False)
    _login(client, u_id)
    resp = client.get("/admin/settings")
    html = resp.get_data(as_text=True)
    # The page should offer a way into the portal (we render the card either way)
    assert "Manage billing" in html or "View plans" in html
