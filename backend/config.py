import os
import urllib.parse
from dotenv import load_dotenv

BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BACKEND_DIR, ".env"))

BASE_DIR = os.path.abspath(os.path.join(BACKEND_DIR, ".."))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/x-msvideo", "video/webm"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024   # 10 MB
MAX_VIDEO_SIZE = 200 * 1024 * 1024  # 200 MB


def format_db_url(url: str) -> str:
    if not url:
        return ""
    if not url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
        return url
    try:
        # Find the last '@' separating credentials from host/port
        r_index = url.rfind("@")
        if r_index == -1:
            return url
        creds_part = url[:r_index]
        host_part = url[r_index + 1:]

        # Split scheme and user_pass
        scheme_sep = "://"
        sep_index = creds_part.find(scheme_sep)
        if sep_index == -1:
            return url
        scheme = creds_part[:sep_index]
        user_pass = creds_part[sep_index + len(scheme_sep):]

        # Split username and password
        user_sep = ":"
        u_index = user_pass.find(user_sep)
        if u_index == -1:
            return url
        username = user_pass[:u_index]
        password = user_pass[u_index + 1:]

        # URL-encode the password
        encoded_password = urllib.parse.quote_plus(password)
        return f"{scheme}://{username}:{encoded_password}@{host_part}"
    except Exception:
        return url


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_CONTENT_LENGTH = MAX_VIDEO_SIZE


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = format_db_url(os.environ.get("DATABASE_URL")) or f"sqlite:///{os.path.join(BACKEND_DIR, 'instance', 'shapeup.db')}"


class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = format_db_url(os.environ.get("DATABASE_URL")) or ""


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}