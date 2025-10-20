from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from app.extensions import db

class AppSettings(db.Model):
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True)  # singleton: id=1
    settings = db.Column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    settings_version = db.Column(db.Integer, nullable=False, server_default=text("1"))
    created_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = db.Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    org_id = db.Column(db.Integer, db.ForeignKey("orgs.id", ondelete="CASCADE"), index=True, nullable=True)



    def to_dict(self):
        return dict(
            id=self.id,
            settings=self.settings or {},
            settings_version=self.settings_version,
            created_at=self.created_at.isoformat() if self.created_at else None,
            updated_at=self.updated_at.isoformat() if self.updated_at else None,
        )
