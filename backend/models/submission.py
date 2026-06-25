# from extensions import db
# class Submission(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     participant_id = db.Column(db.Integer,db.ForeignKey("participant.id"),nullable=False)
#     participant = db.relationship("Participant",backref="submissions")
#     submission_date = db.Column(db.Date)
#     steps = db.Column(db.Integer, nullable=False)
#     steps_proof = db.Column(db.String(255))
#     approved_steps = db.Column(db.Integer,default=0)
#     fitness_video = db.Column(db.String(255))
#     fitness_video_bonus = db.Column(db.Integer,default=0)
#     food_photo = db.Column(db.String(255))
#     food_bonus = db.Column(db.Integer, default=0)
#     fitness_attendance_bonus = db.Column(db.Integer,default=0)
#     fitness_attendance_proof = db.Column(db.String(255))
#     review_status = db.Column(db.String(20), default="Pending")
#     total_points = db.Column(db.Integer, default=0)
from datetime import datetime, timezone, date
from extensions import db
from utils.dates import get_today_local


class Submission(db.Model):
    __tablename__ = "submission"
    __table_args__ = (
        db.UniqueConstraint("participant_id", "submission_date", "challenge_id",
                            name="uq_participant_date_challenge"),
    )

    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey("challenge.id"), nullable=True)
    submission_date = db.Column(db.Date, nullable=False, default=get_today_local)

    # Steps
    steps = db.Column(db.Integer, nullable=False)
    approved_steps = db.Column(db.Integer, default=0)
    steps_proof = db.Column(db.String(300))

    # Bonuses
    fitness_video = db.Column(db.String(300))
    fitness_video_bonus = db.Column(db.Integer, default=0)
    food_photo = db.Column(db.String(300))
    food_bonus = db.Column(db.Integer, default=0)
    fitness_attendance_proof = db.Column(db.String(300))
    fitness_attendance_bonus = db.Column(db.Integer, default=0)

    # Review
    review_status = db.Column(db.String(20), default="Pending", index=True)
    total_points = db.Column(db.Integer, default=0)
    reviewed_by = db.Column(db.String(100))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    participant = db.relationship("Participant", back_populates="submissions")
    challenge = db.relationship("Challenge", back_populates="submissions")
    review_logs = db.relationship("ReviewLog", back_populates="submission", lazy="dynamic")

    def recalculate_points(self):
        if self.review_status == "Rejected":
            self.approved_steps = 0
            self.fitness_video_bonus = 0
            self.fitness_attendance_bonus = 0
            self.food_bonus = 0
            self.total_points = 0
        else:
            self.total_points = (
                (self.approved_steps or 0)
                + (self.fitness_video_bonus or 0)
                + (self.fitness_attendance_bonus or 0)
                + (self.food_bonus or 0)
            )

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.participant.employee_id,
            "name": self.participant.name,
            "challenge_id": self.challenge_id,
            "challenge_name": self.challenge.name if self.challenge else None,
            "submission_date": self.submission_date.isoformat(),
            "steps": self.steps,
            "approved_steps": self.approved_steps,
            "steps_proof": self.steps_proof,
            "fitness_video": self.fitness_video,
            "fitness_video_bonus": self.fitness_video_bonus,
            "food_photo": self.food_photo,
            "food_bonus": self.food_bonus,
            "fitness_attendance_proof": self.fitness_attendance_proof,
            "fitness_attendance_bonus": self.fitness_attendance_bonus,
            "review_status": self.review_status,
            "total_points": self.total_points,
            "reviewed_by": self.reviewed_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }