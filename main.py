from flask import Flask, render_template, redirect, url_for, request
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os

# Import database initialization
from utils.database import init_database

# Import API blueprints
from api.students import students_api
from api.auth import auth_api

# Import user model for Flask-Login
from models.users import get_user_by_id
from models.students import get_all_students, get_upload_history

app = Flask(__name__)
CORS(app)

# Configure session and security
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = 86400 * 30  # 30 days
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

# Register API blueprints
app.register_blueprint(students_api, url_prefix='/api')
app.register_blueprint(auth_api, url_prefix='/api/auth')

# Make vite development mode available in templates
@app.context_processor
def inject_debug_info():
    return dict(
        is_development=app.debug,
        vite_dev_server='http://localhost:3000'
    )

# Fragment Routes for Htmx
@app.route('/fragments/students')
@login_required
def students_fragment():
    """Return students table fragment with search functionality"""
    print("Students fragment route called")
    
    search_term = request.args.get('search', '').strip().lower()
    filter_by = request.args.get('filter', 'all')
    
    print(f"Search term: '{search_term}', Filter: '{filter_by}'")
    
    students, error = get_all_students()
    if error:
        print(f"Error getting students: {error}")
        return f'<div class="text-red-600">Error: {error}</div>'
    
    print(f"Found {len(students)} students")
    
    # Apply search filter if provided
    if search_term:
        filtered_students = []
        for student in students:
            if filter_by == 'all':
                # Search across all fields
                if (search_term in str(student['student_id']).lower() or
                    search_term in student['student_name'].lower() or
                    search_term in student['university'].lower() or
                    search_term in student['degree'].lower() or
                    search_term in str(student['year'])):
                    filtered_students.append(student)
            else:
                # Search in specific field
                field_value = str(student.get(filter_by, '')).lower()
                if search_term in field_value:
                    filtered_students.append(student)
        
        students = filtered_students
        print(f"After filtering: {len(students)} students")
    
    return render_template('fragments/students_table.html', 
                         students=students, 
                         search_term=search_term,
                         total_count=len(students))

@app.route('/fragments/upload-status')
@login_required
def upload_status_fragment():
    """Return upload status fragment"""
    print("Upload status fragment route called")
    
    history, error = get_upload_history()
    if error:
        print(f"Error getting upload history: {error}")
        return f'<div class="text-red-600">Error: {error}</div>'
    
    print(f"Upload history: {len(history) if history else 0} entries")
    
    return render_template('fragments/upload_status.html', history=history)

# Test routes
@app.route('/test-htmx')
def test_htmx():
    """Test route to verify Htmx functionality"""
    import datetime
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print(f"Test route called, returning time: {current_time}")
    return f'<div>Htmx is working! Current time: {current_time}</div>'

@app.route('/test')
def test_page():
    """Manual test page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Htmx Manual Test</title>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
        <style>
            .test-box { border: 2px solid blue; padding: 15px; margin: 10px; background: #f0f0f0; }
            button { padding: 10px; margin: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>Manual Htmx Test</h1>
        
        <button hx-get="/test-htmx" hx-target="#time-display">Click to Get Time</button>
        
        <div id="time-display" class="test-box">
            Click button to load time...
        </div>
        
        <div id="auto-time" 
             hx-get="/test-htmx" 
             hx-trigger="load, every 5s"
             class="test-box">
            Auto-loading time...
        </div>
        
        <script>
            console.log('Htmx loaded:', typeof htmx !== 'undefined');
            
            document.body.addEventListener('htmx:beforeRequest', function(evt) {
                console.log('Making request to:', evt.detail.requestConfig.path);
            });
            
            document.body.addEventListener('htmx:afterRequest', function(evt) {
                console.log('Request completed:', evt.detail.xhr.status);
                console.log('Response text:', evt.detail.xhr.responseText);
            });
            
            document.body.addEventListener('htmx:responseError', function(evt) {
                console.log('Request failed:', evt.detail);
            });
        </script>
    </body>
    </html>
    '''

# Main routes
@app.route('/')
@login_required
def index():
    """Serve the main HTML page (protected)"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Serve the login page"""
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page (same as index for now)"""
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    # Only initialize database if not in reloader process
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        init_database()

    app.run(debug=True, port=5000)