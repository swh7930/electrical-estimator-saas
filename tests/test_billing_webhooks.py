import json
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Org, Subscription, BillingCustomer

def _ts(minutes_from_now=30):
    return int((datetime.utcnow() + timedelta(minutes=minutes_from_now)).timestamp())

def test_webhook_checkout_session_completed_creates_subscription(app, client, monkeypatch):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_x"
    app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_test_x"
    app.config["STRIPE_PRICE_PRO_MONTHLY"] = "price_pro_monthly"

    # Prepare Org
    with app.app_context():
        org = Org(id=1, name="Hook Org")
        db.session.add(org)
        db.session.commit()

    # Monkeypatch Stripe signature verification to trust our payload
    import stripe
    def _fake_construct_event(payload, sig_header, secret):
        return json.loads(payload)
    monkeypatch.setattr(stripe.Webhook, "construct_event", staticmethod(_fake_construct_event))

    # Monkeypatch StripeClient.subscriptions.retrieve
    from stripe import StripeClient
    class _FakeSubs:
        def retrieve(self, sub_id):
            assert sub_id == "sub_test"
            # Return dict-like payload with items->data[0]->price.id
            return {
                "id": "sub_test",
                "status": "active",
                "customer": "cus_123",
                "metadata": {"org_id": "1"},
                "current_period_end": _ts(60*24*30),
                "cancel_at": None,
                "cancel_at_period_end": False,
                "items": {
                    "data": [
                        {
                            "quantity": 1,
                            "price": {"id": "price_pro_monthly", "product": "prod_pro"},
                        }
                    ]
                },
            }
    class _FakeClient:
        def __init__(self, key): pass
        @property
        def subscriptions(self): return _FakeSubs()
    monkeypatch.setattr("app.blueprints.webhooks.routes.StripeClient", _FakeClient)

    event = {
        "id": "evt_1",
        "type": "checkout.session.completed",
        "data": {"object": {"subscription": "sub_test", "metadata": {"org_id": "1"}}},
    }
    body = json.dumps(event)
    headers = {"Stripe-Signature": "t=1,v1=fake"}

    resp = client.post("/webhooks/stripe", data=body, headers=headers)
    assert resp.status_code == 200

    with app.app_context():
        sub = Subscription.query.filter_by(org_id=1).first()
        assert sub is not None
        assert sub.status in ("active", "trialing")
        assert sub.price_id == "price_pro_monthly"
        # Entitlements snapshot populated for PRO
        assert "exports.pdf" in (sub.entitlements_json or [])
        bc = BillingCustomer.query.filter_by(stripe_customer_id="cus_123").first()
        assert bc is not None
        assert bc.org_id == 1

def test_webhook_invoice_payment_failed_sets_past_due(app, client, monkeypatch):
    app.config["STRIPE_SECRET_KEY"] = "sk_test_x"
    app.config["STRIPE_WEBHOOK_SECRET"] = "whsec_test_x"

    # Seed org + sub as active
    with app.app_context():
        org = Org(id=99, name="Fail Org")
        db.session.add(org)
        db.session.commit()
        sub = Subscription(
            org_id=99,
            stripe_subscription_id="sub_fail",
            product_id="prod_pro",
            price_id="price_pro_monthly",
            status="active",
        )
        db.session.add(sub)
        db.session.commit()

    import stripe
    def _fake_construct_event(payload, sig_header, secret):
        return json.loads(payload)
    monkeypatch.setattr(stripe.Webhook, "construct_event", staticmethod(_fake_construct_event))

    # Fake Stripe client retrieve to return past_due status
    class _FakeSubs:
        def retrieve(self, sub_id):
            assert sub_id == "sub_fail"
            return {
                "id": "sub_fail",
                "status": "past_due",
                "customer": "cus_999",
                "metadata": {"org_id": "99"},
                "current_period_end": _ts(60*24*30),
                "cancel_at": None,
                "cancel_at_period_end": False,
                "items": {"data": [{"quantity": 1, "price": {"id": "price_pro_monthly", "product": "prod_pro"}}]},
            }
    class _FakeClient:
        def __init__(self, key): pass
        @property
        def subscriptions(self): return _FakeSubs()
    monkeypatch.setattr("app.blueprints.webhooks.routes.StripeClient", _FakeClient)

    event = {
        "id": "evt_2",
        "type": "invoice.payment_failed",
        "data": {"object": {"subscription": "sub_fail"}},
    }
    body = json.dumps(event)
    headers = {"Stripe-Signature": "t=1,v1=fake"}
    resp = client.post("/webhooks/stripe", data=body, headers=headers)
    assert resp.status_code == 200

    with app.app_context():
        sub = Subscription.query.filter_by(org_id=99).first()
        assert sub.status == "past_due"
