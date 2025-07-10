from flask import Flask, render_template
from flask_cors import CORS
import os

# Import database initialization
from utils.database import init_database

# Import API blueprints
from api.students import students_api

app = Flask(__name__)
CORS(app)

# Register API blueprints
app.register_blueprint(students_api, url_prefix="/api")

# Web routes (that render templates)
@app.route("/")
def index():
    """Serve the main HTML page"""
    return render_template("index.html")

@app.route("/about")
def about():
    """About page (example of another web route)"""
    return render_template("about.html")

if __name__ == "__main__":
    # Initialize the database if not already done (does not print twice)
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        init_database()
    app.run(debug=True)
