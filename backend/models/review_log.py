import json
from datetime import datetime, timezone
from extensions import db


class ReviewLog(db.Model):
    __tablename__ = "review_log"

    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("submission.id"), nullable=False)
    reviewer = db.Column(db.String(100), nullable=False)
    old_values = db.Column(db.Text)   # JSON string
    new_values = db.Column(db.Text)   # JSON string
    action = db.Column(db.String(50))  # "Approved" | "Rejected" | "Edited"
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    submission = db.relationship("Submission", back_populates="review_logs")

    def set_old_values(self, data: dict):
        self.old_values = json.dumps(data)

    def set_new_values(self, data: dict):
        self.new_values = json.dumps(data)

    def to_dict(self):
        return {
            "id": self.id,
            "submission_id": self.submission_id,
            "reviewer": self.reviewer,
            "old_values": json.loads(self.old_values) if self.old_values else {},
            "new_values": json.loads(self.new_values) if self.new_values else {},
            "action": self.action,
            "timestamp": self.timestamp.isoformat(),
        }