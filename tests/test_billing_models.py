import pytest
from sqlalchemy.exc import IntegrityError
from app.extensions import db
from app.models import Org, BillingCustomer, Subscription

def test_billing_customer_uniqueness(app):
    with app.app_context():
        org = Org(name="Acme Electric")
        db.session.add(org)
        db.session.commit()

        bc1 = BillingCustomer(org_id=org.id, stripe_customer_id="cus_123")
        db.session.add(bc1)
        db.session.commit()

        bc2 = BillingCustomer(org_id=org.id, stripe_customer_id="cus_123")
        db.session.add(bc2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()

def test_subscription_one_per_org_uniqueness(app):
    with app.app_context():
        org = Org(name="Volt Co")
        db.session.add(org)
        db.session.commit()

        s1 = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_001",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
        )
        db.session.add(s1)
        db.session.commit()

        s2 = Subscription(
            org_id=org.id,
            stripe_subscription_id="sub_002",
            product_id="prod_pro",
            price_id="price_pro_annual",
            status="active",
        )
        db.session.add(s2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
