import pytest
from werkzeug.exceptions import Forbidden
from flask_login import login_user
from app.extensions import db
from app.models import Org, User, Subscription
from app.security.entitlements import require_entitlement

def _dummy_view():
    return "ok"

def test_entitlement_guard_allows_when_active_and_feature_present(app):
    with app.app_context():
        org = Org(name="Guard Org")
        db.session.add(org)
        db.session.commit()

        # minimal user record
        u = User(email="user@example.com", org_id=org.id)
        u.set_password("x")
        db.session.add(u)
        db.session.commit()

        # active subscription with exports.pdf entitlement
        sub = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_ent_1",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
            entitlements_json=["exports.pdf", "exports.csv"],
        )
        db.session.add(sub)
        db.session.commit()

        guarded = require_entitlement("exports.pdf")(_dummy_view)

        with app.test_request_context("/_guard_ok"):
            login_user(u)
            assert guarded() == "ok"

def test_entitlement_guard_blocks_when_missing_feature(app):
    with app.app_context():
        org = Org(name="Guard Org 2")
        db.session.add(org)
        db.session.commit()

        u = User(email="user2@example.com", org_id=org.id)
        u.set_password("x")
        db.session.add(u)
        db.session.commit()

        sub = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_ent_2",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
            entitlements_json=["exports.csv"],  # missing exports.pdf
        )
        db.session.add(sub)
        db.session.commit()

        guarded = require_entitlement("exports.pdf")(_dummy_view)

        with app.test_request_context("/_guard_block"):
            from flask_login import login_user
            login_user(u)
            with pytest.raises(Forbidden):
                guarded()
