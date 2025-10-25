from .assembly import Assembly, AssemblyComponent
from .material import Material
from .dje_item import DjeItem
from .app_settings import AppSettings
from .customer import Customer
from .estimate import Estimate
from .user import User
from .org import Org
from .org_membership import OrgMembership
from .email_log import EmailLog
from .billing_customer import BillingCustomer
from .subscription import Subscription
from .billing_event import BillingEventLog

# Re-export role constants for tests and callers expecting them under app.models
try:
    from app.security.entitlements import ROLE_ADMIN, ROLE_MEMBER
except Exception:  # dev fallback only; production code should keep entitlements as the source of truth
    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"

# Ensure package exports include these constants without clobbering existing __all__
try:
    __all__
except NameError:
    __all__ = []

if "ROLE_ADMIN" not in __all__:
    __all__.extend(["ROLE_ADMIN", "ROLE_MEMBER"])