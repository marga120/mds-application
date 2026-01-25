"""
FLASK APPLICATION ENTRY POINT - MDS APPLICATION MANAGEMENT SYSTEM

This is the main Flask application file that initializes and configures the 
MDS (Masters of Data Science) Application Management System. It sets up 
authentication, registers API blueprints, defines web routes, configures 
session management, and handles application startup including database 
initialization. This serves as the central hub for the entire web application.
"""

from flask import Flask, render_template, redirect, url_for, session, request
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os

# Import database initialization
from utils.database import init_database

# Import API blueprints
from api.applicants import applicants_api
from api.auth import auth_api
from api.sessions import sessions_api
from api.ratings import ratings_api
from api.logs import logs_api
from api.test_scores import test_scores_api
from api.database import database_api
from api.statuses import statuses_bp

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
app.register_blueprint(applicants_api, url_prefix="/api")
app.register_blueprint(auth_api, url_prefix="/api/auth")
app.register_blueprint(sessions_api, url_prefix="/api")
app.register_blueprint(ratings_api, url_prefix="/api")
app.register_blueprint(logs_api, url_prefix="/api")
app.register_blueprint(test_scores_api, url_prefix="/api")
app.register_blueprint(database_api, url_prefix="/api")
app.register_blueprint(statuses_bp)


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

@app.route ("/statistics")
@login_required
def statistics_page():
    "Serve as the stats page for admin users"
    return render_template("statistics.html")

    
@app.route("/dashboard")
@login_required
def dashboard():
    """Dashboard page (same as index for now)"""
    return redirect(url_for("index"))


@app.route("/create-new-session")
@login_required
def create_new_session_page():
    """Create new session page (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("index"))  # Redirect non-admin users to main page
    return render_template("create-session.html")


@app.route("/logs")
@login_required
def logs_page():
    """Activity logs page (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("index"))  # Redirect non-admin users to main page
    return render_template("logs.html")


@app.route("/status-config")
@login_required
def status_config_page():
    """Status configuration page (Admin only)"""
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for("index"))  # Redirect non-admin users to main page
    return render_template("status-config.html")


# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for("login_page"))


# Cache headers for static files
@app.after_request
def add_cache_headers(response):
    """Add cache headers for static files to improve performance"""
    if request.path.startswith('/static/'):
        # Cache static files for 1 year (browser will use cached version)
        # Files are cache-busted by changing the filename or adding query params when updated
        response.headers['Cache-Control'] = 'public, max-age=31536000'
    return response

@app.route('/account')
@login_required
def account():
    return render_template('account.html')
@app.route('/users')
@login_required
def users_page():
    """Render the users management page (Admin only)"""
    if not current_user.is_admin:
        return "Access Denied - Admin Only", 403
    return render_template('users.html')

if __name__ == "__main__":
    # Only initialize database if not in reloader process
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        init_database()

    app.run(debug=False)
