import os
from app import create_app

_flask_app = create_app(os.environ.get("FLASK_ENV", "production"))


class CORSMiddleware:
    """
    WSGI-level CORS middleware.
    Fires BEFORE Flask handles the request — works even if Flask crashes with 500.
    Handles OPTIONS preflight and injects headers on every response.
    """
    CORS_HEADERS = [
        ("Access-Control-Allow-Origin", "*"),
        ("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With"),
        ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH"),
        ("Access-Control-Max-Age", "86400"),
    ]

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        if environ.get("REQUEST_METHOD") == "OPTIONS":
            # Immediately respond to preflight without going into Flask
            start_response("200 OK", self.CORS_HEADERS)
            return [b""]

        def add_cors_start_response(status, headers, exc_info=None):
            existing = {h[0].lower() for h in headers}
            for name, value in self.CORS_HEADERS:
                if name.lower() not in existing:
                    headers.append((name, value))
            return start_response(status, headers, exc_info)

        return self.wsgi_app(environ, add_cors_start_response)


# Wrap Flask app with WSGI-level CORS so headers are always present
app = CORSMiddleware(_flask_app)

if __name__ == "__main__":
    _flask_app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
