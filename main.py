from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os

# Import database initialization
from utils.database import init_database

# Import API blueprints
from api.student_info import student_info_api
from api.auth import auth_api
from api.session import session_api
from api.rating import rating_api

# Import user model for Flask-Login
from models.users import get_user_by_id

app = Flask(__name__)
CORS(app)

# Configure session and security
app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY", "your-secret-key-change-this-in-production"
)
app.config["PERMANENT_SESSION_LIFETIME"] = 86400 * 30  # 30 days
app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))


# Register API blueprints
app.register_blueprint(student_info_api, url_prefix="/api")
app.register_blueprint(auth_api, url_prefix="/api/auth")
app.register_blueprint(session_api, url_prefix="/api")
app.register_blueprint(rating_api, url_prefix="/api")


# Web routes (that render templates)
@app.route("/")
@login_required
def index():
    """Serve the main HTML page (protected)"""
    return render_template("index.html")


@app.route("/login")
def login_page():
    """Serve the login page"""
    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page (same as index for now)"""
    return redirect(url_for("index"))


@app.route("/create-new-session")
@login_required
def create_new_session_page():
    """Create new session page"""
    return render_template("create-session.html")


# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for("login_page"))


if __name__ == "__main__":
    # Only initialize database if not in reloader process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        init_database()

    app.run(debug=True)