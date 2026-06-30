from datetime import date
import time
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import IntegrityError
from extensions import db, limiter
from models import Participant, Submission, Challenge
from utils.uploads import save_upload
from utils.dates import get_today_local

bp = Blueprint("submissions", __name__, url_prefix="/api")


@bp.route("/r2-presigned-url", methods=["POST"])
@limiter.limit("10 per minute")
def get_r2_presigned_url():
    try:

        data = request.json or {}
        key = data.get("key")
        content_type = data.get("contentType", "application/octet-stream")

        if not key:
            return jsonify({"message": "key is required"}), 400

        r2_account_id = current_app.config.get("R2_ACCOUNT_ID")
        r2_access_key_id = current_app.config.get("R2_ACCESS_KEY_ID")
        r2_secret_access_key = current_app.config.get("R2_SECRET_ACCESS_KEY")
        r2_bucket_name = current_app.config.get("R2_BUCKET_NAME", "shapeup-submission")
        r2_public_url = current_app.config.get("R2_PUBLIC_URL")

        if not all([r2_account_id, r2_access_key_id, r2_secret_access_key]):
            return jsonify({"message": "R2 storage is not configured on the server"}), 500

        import boto3
        from botocore.config import Config as BotoConfig

        s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_access_key_id,
            aws_secret_access_key=r2_secret_access_key,
            config=BotoConfig(signature_version="s3v4"),
            region_name="auto",
        )

        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": r2_bucket_name,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=3600,
        )

        # Normalize public URL to strip trailing slash
        public_url_base = r2_public_url.rstrip("/")
        public_url = f"{public_url_base}/{key}"

        return jsonify({
            "uploadUrl": upload_url,
            "publicUrl": public_url
        }), 200
    except Exception as e:
        return jsonify({"message": f"Failed to generate presigned URL: {str(e)}"}), 500



@bp.route("/submission", methods=["POST"])
@limiter.limit("5 per minute")
def create_submission():
    try:
        employee_id = request.form.get("employee_id", "").strip()
        name = request.form.get("name", "").strip()
        steps_raw = request.form.get("steps", "0")
        challenge_id = request.form.get("challenge_id")

        if not employee_id or not name:
            return jsonify({"message": "employee_id and name are required"}), 400

        try:
            steps = int(steps_raw)
        except ValueError:
            return jsonify({"message": "steps must be a number"}), 400

        if steps < 0 or steps > 15000:
            return jsonify({"message": "Steps must be between 0 and 15000"}), 400

        # Resolve active challenge
        challenge = None
        if challenge_id:
            challenge = Challenge.query.get(challenge_id)
        if not challenge:
            challenge = Challenge.query.filter_by(status="Active").first()

        # Upsert participant
        participant = Participant.query.filter_by(employee_id=employee_id).first()
        if not participant:
            participant = Participant(employee_id=employee_id, name=name)
            db.session.add(participant)
            db.session.flush()
        else:
            participant.name = name  # keep name in sync

        today = get_today_local()

        # Duplicate check
        existing = Submission.query.filter_by(
            participant_id=participant.id,
            submission_date=today,
            challenge_id=challenge.id if challenge else None,
        ).first()
        if existing:
            return jsonify({"message": "You have already submitted for today"}), 409

        # Save uploads (either file upload or pre-uploaded URL)
        steps_proof_path = None
        if "steps_proof" in request.files:
            steps_proof_path = save_upload(request.files.get("steps_proof"), "steps_proof")
        else:
            steps_proof_path = request.form.get("steps_proof") or None

        fitness_video_path = None
        if "fitness_video" in request.files:
            fitness_video_path = save_upload(request.files.get("fitness_video"), "fitness_video")
        else:
            fitness_video_path = request.form.get("fitness_video") or None

        food_photo_path = None
        if "food_photo" in request.files:
            food_photo_path = save_upload(request.files.get("food_photo"), "food_photo")
        else:
            food_photo_path = request.form.get("food_photo") or None

        attendance_path = None
        if "fitness_attendance_proof" in request.files:
            attendance_path = save_upload(request.files.get("fitness_attendance_proof"), "fitness_attendance_proof")
        else:
            attendance_path = request.form.get("fitness_attendance_proof") or None

        submission = Submission(
            participant_id=participant.id,
            challenge_id=challenge.id if challenge else None,
            submission_date=today,
            steps=steps,
            approved_steps=steps,
            steps_proof=steps_proof_path,
            fitness_video=fitness_video_path,
            food_photo=food_photo_path,
            fitness_attendance_proof=attendance_path,
        )
        db.session.add(submission)
        db.session.commit()
        return jsonify({"message": "Submission created successfully", "id": submission.id}), 201

    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "You have already submitted for today"}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@bp.route("/submission", methods=["GET"])
def get_submissions():
    status_filter = request.args.get("status")
    challenge_id = request.args.get("challenge_id")
    search = request.args.get("search", "").strip().lower()

    query = Submission.query.join(Participant)

    if status_filter and status_filter != "All":
        query = query.filter(Submission.review_status == status_filter)
    if challenge_id:
        query = query.filter(Submission.challenge_id == challenge_id)
    if search:
        query = query.filter(
            db.or_(
                Participant.employee_id.ilike(f"%{search}%"),
                Participant.name.ilike(f"%{search}%"),
            )
        )

    submissions = query.order_by(Submission.created_at.desc()).all()
    return jsonify([s.to_dict() for s in submissions])


@bp.route("/my-submissions/<employee_id>", methods=["GET"])
def get_my_submissions(employee_id):
    participant = Participant.query.filter_by(employee_id=employee_id).first()
    if not participant:
        return jsonify([])

    challenge_id = request.args.get("challenge_id")
    query = Submission.query.filter_by(participant_id=participant.id)
    if challenge_id:
        query = query.filter_by(challenge_id=challenge_id)

    subs = query.order_by(Submission.submission_date.desc()).all()

    # Compute rank within challenge
    rank = None
    if challenge_id:
        lb = _leaderboard_for_challenge(int(challenge_id))
        for entry in lb:
            if entry["employee_id"] == employee_id:
                rank = entry["rank"]
                break

    return jsonify({
        "participant": participant.to_dict(),
        "rank": rank,
        "submissions": [s.to_dict() for s in subs],
        "total_points": sum(s.total_points for s in subs),
    })


def _leaderboard_for_challenge(challenge_id):
    from sqlalchemy import func
    rows = (
        db.session.query(
            Participant.employee_id,
            Participant.name,
            func.sum(Submission.total_points).label("total"),
        )
        .join(Submission, Submission.participant_id == Participant.id)
        .filter(Submission.challenge_id == challenge_id, Submission.review_status == "Approved")
        .group_by(Participant.id)
        .order_by(func.sum(Submission.total_points).desc())
        .all()
    )
    return [
        {"rank": i + 1, "employee_id": r.employee_id, "name": r.name, "total_points": r.total}
        for i, r in enumerate(rows)
    ]