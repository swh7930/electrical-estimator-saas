import types
from flask import Flask
from app.services import policy

class DummyUser:
    def __init__(self, uid, auth=True): self.id, self.is_authenticated, self.org_id = uid, auth, 1

class DummyQuery:
    def __init__(self, obj): self._obj = obj
    def filter_by(self, **kw): return self
    def one_or_none(self): return self._obj
    def count(self): return 1

class DummySession:
    def __init__(self, obj): self._obj = obj
    def query(self, *args, **kw): return DummyQuery(self._obj)

def make_app():
    app = Flask(__name__); app.config.update(SECRET_KEY="x", TESTING=True)
    return app

def test_require_member_unauth_json():
    app = make_app()
    @policy.require_member
    def v(): return "ok", 200
    policy.current_user = DummyUser(None, auth=False); policy.session = {}
    with app.test_request_context("/x", headers={"Accept":"application/json"}):
        r = v(); assert r[1] == 401 and r[0].json["error"] == "unauthorized"

def test_require_member_not_found_json():
    app = make_app()
    @policy.require_member
    def v(): return "ok", 200
    policy.current_user = DummyUser(7, auth=True); policy.session = {"current_org_id":1}
    policy.db = types.SimpleNamespace(session=DummySession(None))
    with app.test_request_context("/x", headers={"Accept":"application/json"}):
        r = v(); assert r[1] == 404 and r[0].json["error"] == "not_found"

def test_require_member_ok():
    app = make_app()
    @policy.require_member
    def v(): return "ok", 200
    policy.current_user = DummyUser(7, auth=True); policy.session = {"current_org_id":1}
    policy.db = types.SimpleNamespace(session=DummySession(types.SimpleNamespace(role="member")))
    with app.test_request_context("/x", headers={"Accept":"application/json"}):
        r = v(); assert r == ("ok", 200)

def test_role_required_forbidden():
    app = make_app()
    @policy.role_required("admin","owner")
    def v(): return "ok", 200
    policy.current_user = DummyUser(7, auth=True); policy.session = {"current_org_id":1}
    policy.db = types.SimpleNamespace(session=DummySession(types.SimpleNamespace(role="member")))
    with app.test_request_context("/x", headers={"Accept":"application/json"}):
        r = v(); assert r[1] == 403 and r[0].json["error"] == "forbidden"

def test_role_required_ok():
    app = make_app()
    @policy.role_required("admin","owner")
    def v(): return "ok", 200
    policy.current_user = DummyUser(7, auth=True); policy.session = {"current_org_id":1}
    policy.db = types.SimpleNamespace(session=DummySession(types.SimpleNamespace(role="admin")))
    with app.test_request_context("/x", headers={"Accept":"application/json"}):
        r = v(); assert r == ("ok", 200)
