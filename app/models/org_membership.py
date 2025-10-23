from sqlalchemy import func, CheckConstraint, UniqueConstraint
from app.extensions import db

# Keep simple text+CHECK for evolvable roles (no DB enum migration pain)
ROLE_MEMBER = "member"
ROLE_ADMIN = "admin"
ROLE_OWNER = "owner"
ROLE_CHOICES = (ROLE_OWNER, ROLE_ADMIN, ROLE_MEMBER)

class OrgMembership(db.Model):
    __tablename__ = "org_memberships"

    id = db.Column(db.Integer, primary_key=True)

    org_id = db.Column(
        db.Integer,
        db.ForeignKey("orgs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # default is member; owner/admin must be explicit
    role = db.Column(db.String(20), nullable=False, server_default=ROLE_MEMBER)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("org_id", "user_id", name="uq_org_memberships_org_user"),
        CheckConstraint(
            "role IN ('owner','admin','member')",
            name="ck_org_memberships_role_valid",
        ),
    )
