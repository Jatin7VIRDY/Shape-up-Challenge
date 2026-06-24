# import os
# from werkzeug.utils import secure_filename
# from flask import Flask, request, jsonify, send_from_directory
# from flask_cors import CORS
# from models.submission import Submission
# from models.participants import Participant
# from extensions import db

# app = Flask(__name__)

# CORS(app)

# app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///shapeup.db"
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# db.init_app(app)
# with app.app_context():
#   db.create_all()

# UPLOAD_FOLDER = "uploads"
# app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# BASE_DIR = os.path.abspath(
#     os.path.join(os.path.dirname(__file__),".."))

# @app.route("/api/submission", methods=["POST"])
# def create_submission():

#     employee_id = request.form.get("employee_id")
#     name = request.form.get("name")
#     steps = request.form.get("steps")
#     if int(steps) > 15000:
#         return jsonify({
#         "message": "Maximum 15000 steps allowed"
#     }), 400

#     steps_proof = request.files.get("steps_proof")
#     fitness_video = request.files.get("fitness_video")
#     food_photo = request.files.get("food_photo")
#     fitness_attendance_proof = request.files.get("fitness_attendance_proof")
#     os.makedirs("uploads/steps", exist_ok=True)
#     os.makedirs("uploads/fitness", exist_ok=True)
#     os.makedirs("uploads/food", exist_ok=True)
#     os.makedirs("uploads/attendance", exist_ok=True)

#     steps_proof_path = None
#     fitness_video_path = None
#     food_photo_path = None
#     attendance_path = None

#     if steps_proof:
#         filename = secure_filename(steps_proof.filename)
#         filepath = os.path.join(BASE_DIR,"uploads","steps",filename)
#         steps_proof.save(filepath)
#         steps_proof_path = f"steps/{filename}"

#     if fitness_video:
#         filename = secure_filename(fitness_video.filename)
#         filepath = os.path.join(BASE_DIR,"uploads","fitness",filename)
#         fitness_video.save(filepath)
#         fitness_video_path = f"fitness/{filename}"

#     if food_photo:
#         filename = secure_filename(food_photo.filename)
#         filepath = os.path.join(BASE_DIR,"uploads","food",filename)
#         food_photo.save(filepath)
#         food_photo_path = f"food/{filename}"
#         attendance_path = None

#     if fitness_attendance_proof:
#         filename = secure_filename(fitness_attendance_proof.filename)
#         filepath = os.path.join(BASE_DIR,"uploads","attendance",filename)
#         fitness_attendance_proof.save(filepath)
#         attendance_path = f"attendance/{filename}"
#     participant = Participant.query.filter_by(employee_id=employee_id).first()
    
#     if not participant:
#         participant = Participant(employee_id=employee_id,name=name)
#         db.session.add(participant)
#         db.session.commit()

#     submission = Submission(
#         participant_id=participant.id,
#         steps=int(steps),
#         approved_steps=int(steps),
#         steps_proof=steps_proof_path,
#         fitness_video=fitness_video_path,
#         fitness_attendance_proof=attendance_path,
#         food_photo=food_photo_path)
#     db.session.add(submission)
#     db.session.commit()
#     return jsonify({
#         "message": "Submission created successfully"
#     }), 201

# @app.route("/api/submission", methods=["GET"])
# def get_submissions():

#     submissions = Submission.query.all()
#     result = []
#     for s in submissions:
#         result.append({
#           "id": s.id,
#           "employee_id": s.participant.employee_id,
#           "name": s.participant.name,
#           "steps": s.steps,
#           "steps_proof": s.steps_proof,
#           "approved_steps": s.approved_steps,
#           "fitness_video": s.fitness_video,
#           "fitness_video_bonus": s.fitness_video_bonus,
#           "food_photo": s.food_photo,
#           "food_bonus": s.food_bonus,
#           "fitness_attendance_proof": s.fitness_attendance_proof,
#           "fitness_attendance_bonus": s.fitness_attendance_bonus,
#           "review_status": s.review_status,
#           "total_points": s.total_points})
#     return jsonify(result)

# @app.route("/api/upload-test", methods=["POST"])
# def upload_test():
#     fitness_video = request.files.get("fitness_video")
#     if not fitness_video:
#         return jsonify({
#             "message": "No file uploaded"
#         }), 400
#     os.makedirs(os.path.join("uploads", "fitness"),exist_ok=True)
#     filename = secure_filename(fitness_video.filename)
#     filepath = os.path.join("uploads","fitness",filename)
#     fitness_video.save(filepath)
#     return jsonify({
#         "message": "uploaded",
#         "filename": filename
#     })

# @app.route("/uploads/<folder>/<filename>")
# def uploaded_file(folder, filename):
#     upload_path = os.path.join(BASE_DIR,"uploads",folder)
#     return send_from_directory(upload_path,filename)

# @app.route("/api/submission/<int:id>/review",methods=["PUT"])
# def review_submission(id):
#     submission = Submission.query.get(id)
#     if not submission:
#       return jsonify({
#           "message":"Submission not found"
#       }),404
#     data = request.get_json()
#     submission.approved_steps = int(data.get("approved_steps",submission.steps))
#     submission.fitness_video_bonus = int(data.get("fitness_video_bonus",0))
#     submission.fitness_attendance_bonus = int(data.get("fitness_attendance_bonus",0))
#     submission.food_bonus = int(data.get("food_bonus",0))
#     submission.review_status = data.get("review_status","Approved")
#     if submission.review_status == "Rejected":
#         submission.approved_steps = 0
#         submission.fitness_video_bonus = 0
#         submission.fitness_attendance_bonus = 0
#         submission.food_bonus = 0
#         submission.total_points = 0
#     else:
#         submission.total_points = (submission.approved_steps + submission.fitness_video_bonus + submission.fitness_attendance_bonus + submission.food_bonus)
#     db.session.commit()
#     return jsonify({
#         "message": "Review completed",
#         "total_points": submission.total_points,
#         "review_status": submission.review_status,
#         "approved_steps": submission.approved_steps,
#         "fitness_video_bonus": submission.fitness_video_bonus,
#         "fitness_attendance_bonus": submission.fitness_attendance_bonus,
#         "food_bonus": submission.food_bonus
#     })

# @app.route("/api/leaderboard")
# def leaderboard():
#     submissions = Submission.query.filter_by(review_status="Approved").order_by(Submission.total_points.desc()).all()
#     result=[]
#     rank=1
#     for s in submissions:
#         result.append({
#             "rank": rank,
#             "employee_id": s.participant.employee_id,
#             "name": s.participant.name,
#             "total_points": s.total_points
#         })
#         rank+=1
#     return jsonify(result)

# @app.route("/api/dashboard-stats")
# def dashboard_stats():
#     total = Submission.query.count()
#     pending =Submission.query.filter_by(review_status="Pending").count()
#     approved =Submission.query.filter_by(review_status="Approved").count()
#     rejected =Submission.query.filter_by(review_status="Rejected").count()
#     return jsonify({
#         "total": total,
#         "pending": pending,
#         "approved": approved,
#         "rejected": rejected
#     })

# if __name__ == "__main__":
#     app.run(debug=True)
import os
from flask import Flask, send_from_directory
from extensions import db, cors
from config import config


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[env])

    # Ensure instance & upload dirs exist only if running locally without cloud services
    if not app.config.get("SQLALCHEMY_DATABASE_URI") or "sqlite" in app.config.get("SQLALCHEMY_DATABASE_URI", ""):
        os.makedirs(app.instance_path, exist_ok=True)
    if not os.environ.get("CLOUDINARY_URL"):
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Extensions
    db.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Blueprints
    from routes import submissions_bp, admin_bp, challenges_bp, leaderboard_bp
    app.register_blueprint(submissions_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(challenges_bp)
    app.register_blueprint(leaderboard_bp)

    # Backwards-compat: old frontend used /api/submission/<id>/review and /api/dashboard-stats
    from routes.admin import bp as admin_bp2
    # These are registered via the admin blueprint already (/api/admin/...)
    # Add shim routes for any old code still calling legacy URLs
    from flask import jsonify, request as req
    from models import Submission

    @app.route("/api/submission/<int:sid>/review", methods=["PUT"])
    def legacy_review(sid):
        from routes.admin import review_submission
        return review_submission(sid)

    @app.route("/api/dashboard-stats")
    def legacy_stats():
        from routes.admin import dashboard_stats
        return dashboard_stats()

    @app.route("/api/leaderboard-legacy")
    def legacy_leaderboard():
        submissions = (
            Submission.query.filter_by(review_status="Approved")
            .order_by(Submission.total_points.desc())
            .all()
        )
        return jsonify([
            {"rank": i + 1, "employee_id": s.participant.employee_id,
             "name": s.participant.name, "total_points": s.total_points}
            for i, s in enumerate(submissions)
        ])

    # Serve uploaded files
    upload_root = app.config["UPLOAD_FOLDER"]

    @app.route("/uploads/<folder>/<filename>")
    def serve_upload(folder, filename):
        folder_path = os.path.join(upload_root, folder)
        return send_from_directory(folder_path, filename)

    # Create tables
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)
    app.run(debug=(env == "development"), host="0.0.0.0", port=5000)