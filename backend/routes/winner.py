import os
import uuid
from flask import Blueprint, request, jsonify, current_app, send_file
from services.winner_service import WinnerService

bp = Blueprint("winner", __name__, url_prefix="/api/winner")

ALLOWED_EXCEL_EXTENSIONS = {"xlsx", "xls"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in ALLOWED_EXCEL_EXTENSIONS

@bp.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"success": False, "message": "No file part in the request"}), 400
    
    file = request.files["file"]
    day = request.form.get("day")
    session_id = request.form.get("session_id")

    if not day or day not in {"day0", "day45", "day90"}:
        return jsonify({"success": False, "message": "Invalid or missing 'day' parameter. Must be day0, day45, or day90."}), 400

    if not file or file.filename == "":
        return jsonify({"success": False, "message": "No file selected for uploading"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Only Excel files (.xlsx, .xls) are allowed."}), 400

    if not session_id:
        session_id = uuid.uuid4().hex

    try:
        # Read file into memory first to validate
        file_bytes = file.read()
        
        # Friendly label for validation messages
        label = "Day 0" if day == "day0" else "Day 45" if day == "day45" else "Day 90"
        
        # Parse and validate the sheet structure and data
        parsed_res = WinnerService.parse_and_validate_sheet(file_bytes, label)
        
        if not parsed_res["success"]:
            return jsonify({
                "success": False,
                "message": parsed_res["file_error"],
                "session_id": session_id
            }), 400

        # Save the file to disk in the session directory
        upload_root = current_app.config["UPLOAD_FOLDER"]
        dest_dir = os.path.join(upload_root, "winner_declaration", session_id)
        os.makedirs(dest_dir, exist_ok=True)

        dest_path = os.path.join(dest_dir, f"{day}.xlsx")
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "filename": file.filename,
            "message": f"{label} Excel uploaded successfully!",
            "total_rows": parsed_res["total_rows"],
            "valid_count": parsed_res["valid_count"],
            "incomplete_count": parsed_res["incomplete_count"],
            "incomplete_participants": parsed_res["incomplete_participants"]
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Internal error uploading file: {str(e)}"}), 500


@bp.route("/calculate", methods=["POST"])
def calculate_leaderboard():
    if request.is_json:
        data = request.get_json() or {}
        session_id = data.get("session_id")
    else:
        session_id = request.form.get("session_id")

    if not session_id:
        session_id = uuid.uuid4().hex

    upload_root = current_app.config["UPLOAD_FOLDER"]
    session_dir = os.path.join(upload_root, "winner_declaration", session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Save any files passed directly in the request (e.g. day0, day45, day90)
    for day_key in ["day0", "day45", "day90"]:
        if day_key in request.files:
            uploaded_f = request.files[day_key]
            if uploaded_f and uploaded_f.filename != "":
                dest_path = os.path.join(session_dir, f"{day_key}.xlsx")
                uploaded_f.save(dest_path)

    # Verify that all three files are present
    required_files = {"day0.xlsx": "Day 0", "day45.xlsx": "Day 45", "day90.xlsx": "Day 90"}
    missing = []
    for filename, label in required_files.items():
        if not os.path.isfile(os.path.join(session_dir, filename)):
            missing.append(label)

    if missing:
        return jsonify({
            "success": False,
            "session_id": session_id,
            "message": f"Missing files for: {', '.join(missing)}. Please upload all three Excel sheets."
        }), 400

    try:
        # Read the files
        with open(os.path.join(session_dir, "day0.xlsx"), "rb") as f:
            day0_bytes = f.read()
        with open(os.path.join(session_dir, "day45.xlsx"), "rb") as f:
            day45_bytes = f.read()
        with open(os.path.join(session_dir, "day90.xlsx"), "rb") as f:
            day90_bytes = f.read()

        d0_res = WinnerService.parse_and_validate_sheet(day0_bytes, "Day 0")
        d45_res = WinnerService.parse_and_validate_sheet(day45_bytes, "Day 45")
        d90_res = WinnerService.parse_and_validate_sheet(day90_bytes, "Day 90")

        if not d0_res["success"]:
            return jsonify({"success": False, "message": f"Day 0 File Error: {d0_res['file_error']}"}), 400
        if not d45_res["success"]:
            return jsonify({"success": False, "message": f"Day 45 File Error: {d45_res['file_error']}"}), 400
        if not d90_res["success"]:
            return jsonify({"success": False, "message": f"Day 90 File Error: {d90_res['file_error']}"}), 400

        # Calculate rankings
        summary, rankings, incomplete_records, warnings = WinnerService.calculate_results(d0_res, d45_res, d90_res)

        return jsonify({
            "success": True,
            "session_id": session_id,
            "summary": summary,
            "rankings": rankings,
            "incomplete_records": incomplete_records,
            "warnings": warnings
        })

    except ValueError as val_err:
        return jsonify({"success": False, "message": str(val_err)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Internal error during calculation: {str(e)}"}), 500


@bp.route("/export", methods=["GET"])
def export_winner_rankings():
    session_id = request.args.get("session_id")
    export_type = request.args.get("type", "all")  # all or top10

    if not session_id:
        return jsonify({"success": False, "message": "Missing 'session_id' parameter"}), 400

    upload_root = current_app.config["UPLOAD_FOLDER"]
    session_dir = os.path.join(upload_root, "winner_declaration", session_id)

    if not os.path.isdir(session_dir):
        return jsonify({"success": False, "message": "Session not found"}), 404

    try:
        # Load and parse files
        with open(os.path.join(session_dir, "day0.xlsx"), "rb") as f:
            day0_bytes = f.read()
        with open(os.path.join(session_dir, "day45.xlsx"), "rb") as f:
            day45_bytes = f.read()
        with open(os.path.join(session_dir, "day90.xlsx"), "rb") as f:
            day90_bytes = f.read()

        day0_data, _ = WinnerService.parse_and_validate_sheet(day0_bytes, "Day 0")
        day45_data, _ = WinnerService.parse_and_validate_sheet(day45_bytes, "Day 45")
        day90_data, _ = WinnerService.parse_and_validate_sheet(day90_bytes, "Day 90")

        # Recalculate
        _, rankings, _ = WinnerService.calculate_results(day0_data, day45_data, day90_data)

        if export_type == "top10":
            rankings = rankings[:10]
            title = "Top 10 Rankings"
            filename = f"ShapeUp_Top10_Rankings_{session_id[:8]}.xlsx"
        else:
            title = "Full Rankings"
            filename = f"ShapeUp_Full_Rankings_{session_id[:8]}.xlsx"

        excel_bytes = WinnerService.generate_excel_bytes(rankings, title)

        import io
        buf = io.BytesIO(excel_bytes)
        return send_file(
            buf,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to export Excel: {str(e)}"}), 500
