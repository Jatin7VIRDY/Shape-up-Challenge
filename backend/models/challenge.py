from datetime import datetime, timezone, date
from extensions import db
class Challenge(db.Model):
    __tablename__ = "challenge"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Upcoming")  # Upcoming | Active | Completed
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    submissions = db.relationship("Submission", back_populates="challenge", lazy="dynamic")

    def auto_update_status(self):
        today = date.today()
        if today < self.start_date:
            self.status = "Upcoming"
        elif self.start_date <= today <= self.end_date:
            self.status = "Active"
        else:
            self.status = "Completed"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "status": self.status,
        }