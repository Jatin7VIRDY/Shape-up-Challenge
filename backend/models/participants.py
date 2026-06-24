from datetime import datetime, timezone
from extensions import db
class Participant(db.Model):
    __tablename__ = "participant"
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),)
    submissions = db.relationship("Submission", back_populates="participant", lazy="dynamic")
    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "name": self.name,
            "batch": self.batch,
        }