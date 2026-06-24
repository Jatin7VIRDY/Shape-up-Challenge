from datetime import date
from flask import Blueprint, request, jsonify
from extensions import db
from models import Challenge

bp = Blueprint("challenges", __name__, url_prefix="/api/challenges")


@bp.route("", methods=["GET"])
def list_challenges():
    # Auto-update statuses
    challenges = Challenge.query.order_by(Challenge.start_date.desc()).all()
    for c in challenges:
        c.auto_update_status()
    db.session.commit()
    return jsonify([c.to_dict() for c in challenges])


@bp.route("/active", methods=["GET"])
def get_active():
    c = Challenge.query.filter_by(status="Active").first()
    if not c:
        return jsonify(None)
    return jsonify(c.to_dict())


@bp.route("", methods=["POST"])
def create_challenge():
    data = request.get_json()
    try:
        start = date.fromisoformat(data["start_date"])
        end = date.fromisoformat(data["end_date"])
    except (KeyError, ValueError):
        return jsonify({"message": "start_date and end_date required (YYYY-MM-DD)"}), 400

    if end < start:
        return jsonify({"message": "end_date must be after start_date"}), 400

    c = Challenge(name=data.get("name", "Weekly Challenge"), start_date=start, end_date=end)
    c.auto_update_status()
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201


@bp.route("/<int:cid>", methods=["PUT"])
def update_challenge(cid):
    c = Challenge.query.get_or_404(cid)
    data = request.get_json()
    if "name" in data:
        c.name = data["name"]
    if "start_date" in data:
        c.start_date = date.fromisoformat(data["start_date"])
    if "end_date" in data:
        c.end_date = date.fromisoformat(data["end_date"])
    if "status" in data:
        c.status = data["status"]
    else:
        c.auto_update_status()
    db.session.commit()
    return jsonify(c.to_dict())


@bp.route("/<int:cid>", methods=["DELETE"])
def delete_challenge(cid):
    c = Challenge.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Deleted"})