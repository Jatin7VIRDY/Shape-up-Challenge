import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

# Cloudinary SDK imports
import cloudinary
import cloudinary.uploader

ALLOWED_EXTENSIONS = {
    "steps_proof": {"jpg", "jpeg", "png", "webp", "gif"},
    "fitness_video": {"mp4", "mov", "avi", "webm"},
    "food_photo": {"jpg", "jpeg", "png", "webp", "gif"},
    "fitness_attendance_proof": {"jpg", "jpeg", "png", "webp", "gif"},
}

SUBFOLDER = {
    "steps_proof": "steps",
    "fitness_video": "fitness",
    "food_photo": "food",
    "fitness_attendance_proof": "attendance",
}


def allowed_file(filename: str, field: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS.get(field, set())


def save_upload(file, field: str) -> str | None:
    """Save an uploaded file (to Cloudinary if configured, else locally) and return its path/URL."""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, field):
        raise ValueError(f"File type not allowed for {field}")

    # Check if Cloudinary is configured
    cloudinary_url = os.environ.get("CLOUDINARY_URL")
    if cloudinary_url:
        try:
            # Cloudinary automatically parses CLOUDINARY_URL from the environment.
            # We can upload the file stream directly.
            subfolder = SUBFOLDER[field]
            upload_result = cloudinary.uploader.upload(
                file,
                folder=f"shapeup/{subfolder}",
                resource_type="auto"
            )
            return upload_result.get("secure_url")
        except Exception as e:
            # Fall back to local file storage if Cloudinary upload fails
            current_app.logger.error(f"Cloudinary upload failed: {str(e)}")

    # Local fallback
    subfolder = SUBFOLDER[field]
    upload_root = current_app.config["UPLOAD_FOLDER"]
    dest_dir = os.path.join(upload_root, subfolder)
    os.makedirs(dest_dir, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(dest_dir, unique_name)
    file.save(dest_path)
    return f"{subfolder}/{unique_name}"