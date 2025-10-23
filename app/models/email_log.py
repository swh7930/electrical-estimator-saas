from datetime import datetime
from app.extensions import db

class EmailLog(db.Model):
    __tablename__ = "email_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    to_email = db.Column(db.String(320), nullable=False, index=True)
    template = db.Column(db.String(64), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    provider_msg_id = db.Column(db.String(128), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, index=True)  # queued|sent|delivered|bounced|complaint|failed
    meta = db.Column(db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EmailLog id={self.id} to={self.to_email} status={self.status}>"
