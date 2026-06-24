from flask import Blueprint, request, jsonify
from sqlalchemy import func
from extensions import db
from models import Submission, Participant, Challenge

bp = Blueprint("leaderboard", __name__, url_prefix="/api/leaderboard")


@bp.route("", methods=["GET"])
def leaderboard():
    challenge_id = request.args.get("challenge_id")

    # Default to active challenge
    if not challenge_id:
        active = Challenge.query.filter_by(status="Active").first()
        if active:
            challenge_id = active.id

    query = (
        db.session.query(
            Participant.employee_id,
            Participant.name,
            func.sum(Submission.total_points).label("total_points"),
            func.count(Submission.id).label("submission_count"),
        )
        .join(Submission, Submission.participant_id == Participant.id)
        .filter(Submission.review_status == "Approved")
    )

    if challenge_id:
        query = query.filter(Submission.challenge_id == challenge_id)

    rows = (
        query
        .group_by(Participant.id)
        .order_by(func.sum(Submission.total_points).desc())
        .all()
    )

    result = []
    for rank, r in enumerate(rows, 1):
        result.append({
            "rank": rank,
            "employee_id": r.employee_id,
            "name": r.name,
            "total_points": int(r.total_points or 0),
            "submission_count": r.submission_count,
        })

    return jsonify({
        "challenge_id": challenge_id,
        "entries": result,
    })