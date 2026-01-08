# MDS Application Management System

A comprehensive Flask web application for managing Masters of Data Science (MDS) student applications at the University of British Columbia (UBC). This system provides role-based access control for admins, faculty, and viewers to efficiently process, review, and track student applications.

- **Last updated**: 1/8/2026

## Table of Contents

1. [Local Development Steps](#-local-development-steps)
2. [User Documentation](#-user-documentation)
3. [Technical Documentation](#-technical-documentation)

---

## Local Development Steps

### Prerequisites

Before running this application, ensure you have the following installed:

- **Python** - [Download here](https://www.python.org/downloads/)
- **Node.js** - [Download here](https://nodejs.org/)
- **PostgreSQL and pgAdmin** - [Download here](https://www.postgresql.org/download/)
- **Git** - [Download here](https://git-scm.com/)

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd mds-application
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Set Up Node.js Dependencies
```bash
# Install Node.js packages for Tailwind CSS
npm install
```

### 4. Configure Database
Create a `.env` file in the project root with your PostgreSQL credentials:
```env
HOST=localhost
DATABASE=mds_database
USER=your_username
PASSWORD=your_password
PORT=5432
SECRET_KEY=your_secret_key
```

### 5. Create PostgreSQL Database
```sql
-- Connect to PostgreSQL and create database
CREATE DATABASE mds_database;
```

### 6. Run the Application
```bash
# Start both Flask server and Tailwind CSS compiler
npm run dev
```

This creates:
- **Roles**: Admin, Faculty, Viewer
- **Test Users** with different access levels

### 8. Access the Application
Open your browser and navigate to:
```
http://localhost:5000
```

### Test Login Credentials
After seeding, use these test accounts:
- **Admin**: `testuser1@example.com` / `password`, `testuser2@example.com` / `password`
- **Faculty**: `testuser3@example.com` / `password`
- **Viewer**: `testuser4@example.com` / `password`

---

## User Documentation

### System Overview

The MDS Application Management System uses role-based access control with three distinct user types, each with specific permissions and capabilities.

### Admin Users

**Full System Access** - Complete control over all system functions

#### What Admins Can Do:
- **User Management** (NEW - via `/users` page)
  - Create new user accounts for Faculty and Viewers with email and password
  - Edit existing user emails and reset passwords
  - Delete user accounts (cannot delete own account)
  - Search and filter users by name, email, or role
  - Assign and modify user roles (Admin, Faculty, Viewer)
  - View system activity logs and audit trails

- **Session Management**
  - Not implemented yet
  - Assigns which session the applications are in via the CSV

- **Application Data Management**
  - Upload CSV files containing student application data
  - Process and import large batches of applications
  - Delete and modify application records via the CSV

- **Data Export** 
  - Export complete database with all applicants and all data sections
  - Selective export with search, filter, and applicant selection
  - Choose specific data sections to export (Personal Info, Application Data, Test Scores, Ratings, etc.)
  - Sort and filter applicants before export
  - Downloads as CSV files with timestamp naming

- **Student Review Process**
  - View all student applications
  - Update application statuses (Not Reviewed → Reviewed → Offer/Declined/etc.)
  - Edit English proficiency requirements and comments
  - Modify prerequisite course requirements and GPA data
  - Add and edit ratings/comments for students

- **Test Score Management**
  - View all English language test scores (TOEFL, IELTS, etc.)
  - View all  graduate test scores (GRE, GMAT)
  - Update test score validity and requirements

- **System Administration**
  - Access system logs and user activity tracking

#### Admin Workflow:
1. **Setup**: Create user accounts and academic sessions
2. **Import**: Upload student application data via CSV
3. **Review**: Coordinate review process with Faculty
4. **Decisions**: Make final application decisions
5. **Monitor**: Track system usage and maintain data integrity

### Faculty Users

**Academic Review Focus** - Access to review and evaluate student applications

#### What Faculty Can Do:
- **Student Application Review**
  - View comprehensive student profiles and academic history
  - Access all test scores and academic transcripts
  - Review prerequisite course completion
  - View English proficiency test results

- **Rating, Prerequisite, and Feedback**
  - Assign numerical ratings (0.0-10.0) to applicants
  - Add detailed comments about student qualifications (NEW - can save comments independently without rating)
  - View ratings from other Faculty members (aggregate scores)
  - Able to modify the student prerequisite courses
  - Save All button properly persists ratings and comments together

- **Application Status Tracking**
  - Monitor current application status for each student
  - Track review progress across the applicant pool

- **Academic Assessment**
  - Review student GPA and degree information
  - Evaluate prerequisite course completion (CS, Statistics, Mathematics)
  - Assess academic background and institutional history

#### What Faculty Cannot Do:
- Create or modify user accounts
- Upload new application data
- Change application statuses
- Edit English proficiency comments or status
- Access system administration features
- Delete application records

#### Faculty Workflow:
1. **Access**: Log in to view assigned application pool
2. **Review**: Examine student profiles, scores, and backgrounds
3. **Evaluate**: Assign ratings, add evaluation comments, comment on prerequisite courses
4. **Collaborate**: Coordinate with other Faculty on decisions
5. **Recommend**: Provide input for final admission decisions

### Viewer Users

**Read-Only Access** - Limited to viewing application data

#### What Viewers Can Do:
- **View Student Information**
  - Access to student contact and demographic information
  - View application submission status and timelines
  - See academic history and institutional backgrounds

- **Review Test Scores**
  - View English language test results (TOEFL, IELTS, etc.)
  - Access graduate test scores (GRE, GMAT)
  - Review test score validity and dates

- **Monitor Application Progress**
  - Track current application statuses
  - View submission and review timelines

- **Academic Background Review**
  - View student GPA and degree information
  - Review prerequisite course information
  - Access institutional academic history

#### What Viewers Cannot Do:
- Add or edit any data
- Assign ratings or comments
- Change application statuses
- Upload new files or data
- Access user management features
- Modify student information
- Edit test scores or academic records

#### Viewer Workflow:
1. **Monitor**: Track application processing progress
2. **Report**: Generate insights from application data
3. **Support**: Assist in administrative coordination
4. **Observe**: Stay informed about admission cycle status

### Common Features for All Users

#### Navigation and Interface
- **Dashboard**: Centralized view of current session applicants
- **Search and Filter**: Find specific students by name, status, or criteria
- **Statistics Page**: Access via `/statistics` page
- **Account Settings**: Access via `/account` page

#### Statistics Page (NEW - All Users)
All users can view comprehensive application analytics:

- **Overall Statistics**
  - Total submitted applications
  - Total unsubmitted applications
  - Domestic vs International applicant breakdown
  - Gender distribution with visual bar charts

- **Review Status Analytics**
  - Visual breakdown by status (Not Reviewed, Reviewed by PPA, etc.)
  - Percentage calculations for each status category
  - Color-coded progress bars

- **Filtering Options**
  - Filter statistics by review status
  - View submitted applications only
  - View unsubmitted applications only
  - Real-time chart updates based on filters

#### Account Settings (NEW - All Users)
All users can manage their own account through the Account Settings page:

- **View Profile Information**
  - Display current name, email, and role
  - View account creation and last update timestamps

- **Update Email Address**
  - Change account email with password confirmation
  - Email uniqueness validation
  - Immediate session update after successful change

- **Change Password**
  - Requires current password verification
  - Minimum 8 character requirement enforced
  - Password confirmation to prevent typos
  - Secure bcrypt hashing

**Security Features:**
- All changes require current password verification
- Server-side validation of all inputs
- Activity logging for audit trails
- Cannot view or modify other users' accounts

#### Student Profile View
- **Personal Information**: Contact details, demographics
- **Academic History**: Previous institutions and degrees
- **Test Scores**: Comprehensive view of all standardized tests
- **Application Status**: Current stage in review process
- **Ratings**: Faculty evaluations and comments (where permitted)

#### Session Management
- **Session Selection**: Not implemented
- **Data Filtering**: Not implemented
- **Status Tracking**: Not implemented

---

## Technical Documentation

### Project Architecture

The MDS Application Management System is built using a modern web stack with clear separation between frontend and backend components.

#### Technology Stack
- **Backend**: Python Flask with Flask-Login for authentication
- **Frontend**: Vanilla JavaScript with Tailwind CSS
- **Database**: PostgreSQL
- **Build Tools**: Node.js with Tailwind CLI
- **Security**: bcrypt for password hashing, session-based auth

### Project Structure

```
mds-application/
├── api/                        # API route handlers
│   ├── applicants.py          # Student application endpoints
│   ├── auth.py                # Authentication endpoints
│   ├── logs.py                # Activity logging endpoints
│   ├── ratings.py             # Rating/comment endpoints
│   ├── sessions.py            # Session management endpoints
│   └── test_scores.py         # Test score endpoints
├── models/                     # Database interaction layer
│   ├── applicants.py          # Student data operations
│   ├── institutions.py        # Academic institution handling
│   ├── ratings.py             # Rating system operations
│   ├── sessions.py            # Session management
│   ├── test_scores.py         # Test score processing
│   └── users.py               # User authentication & management
├── static/                     # Frontend static assets
│   ├── css/
│   │   ├── input.css          # Tailwind CSS source
│   │   └── output.css         # Compiled CSS (auto-generated)
│   └── js/
│       ├── applicants.js      # Main application logic (includes export modal)
│       ├── auth.js            # Authentication handling
│       ├── account.js         # Account settings 
│       ├── users.js           # User management for admins 
│       ├── statistics.js      # Statistics page logic 
│       ├── sessions.js        # Session creation
│       ├── logs.js            # Activity log viewer
│       └── main.js            # Application entry point
├── templates/                  # HTML template files
│   ├── create-session.html    # Session creation page
│   ├── index.html             # Main application interface
│   ├── login.html             # Login page
│   ├── account.html           # Account settings page 
│   ├── users.html             # User management page (Admin only)
│   ├── statistics.html        # Statistics page 
│   ├── header.html            # Header component
│   └── logs.html              # Activity logs page
├── utils/                      # Utility functions
│   ├── activity_logger.py     # System activity tracking
│   └── database.py            # Database connection & initialization
├── main.py                     # Flask application entry point
├── schema.sql                  # Database schema definition
├── seed.py                     # Database seeding script
├── requirements.txt            # Python dependencies
├── package.json                # Node.js dependencies
└── .env                        # Environment configuration
```

### Database Schema

#### Core Tables

**users & roles**
- `role_user`: User role definitions (Admin, Faculty, Viewer)
- `user`: System users with authentication credentials
- Foreign key relationship maintaining role-based access

**sessions**
- Manages academic application cycles
- Links to specific program codes and years
- Enables multi-session support

**applicant_info**
- Core student information and demographics
- References session for data organization
- Primary key: `user_code` (unique student identifier)

**application_info**
- Application status tracking and metadata
- English proficiency status and comments
- Prerequisite course tracking
- GPA and academic requirements

#### Test Score Tables
- `toefl`: TOEFL test results with detailed scores
- `ielts`: IELTS test results and bands
- `melab`, `pte`, `cael`, `celpip`: Additional English tests
- `duolingo`: Duolingo English test scores
- `gre`: Graduate Record Examination scores
- `gmat`: Graduate Management Admission Test scores

#### Supporting Tables
- `ratings`: Faculty ratings and comments for applicants
- `institution_info`: Academic history and institutional data
- `activity_log`: System audit trail and user activity tracking

### API Endpoints

#### Authentication (`/api/auth/`)
- `POST /login`: User authentication
- `POST /logout`: Session termination
- `GET /check-session`: Session validation
- `GET /user`: Current user information
- `POST /register`: User creation (Admin only)
- `GET /users`: List all users with search (Admin only) 
- `GET /user/<user_id>`: Get specific user details (Admin only)
- `PUT /user/<user_id>`: Update user details (Admin only) 
- `DELETE /delete-user/<user_id>`: Delete user account (Admin only)
- `POST /update-email`: Update current user's email 
- `POST /reset-password`: Change current user's password 

#### Applicants (`/api/`)
- `GET /applicant-status`: List all applicants with status
- `POST /upload`: CSV file processing (Admin only)
- `GET /applicant-application-info/<user_code>`: Detailed applicant data
- `PUT /applicant-application-info/<user_code>/status`: Status updates (Admin only)
- `PUT /applicant-application-info/<user_code>/prerequisites`: Course data updates
- `PUT /applicant-application-info/<user_code>/english-comment`: English comments (Admin only)
- `PUT /applicant-application-info/<user_code>/english-status`: English status (Admin only)

#### Ratings (`/api/ratings/`)
- `GET /<user_code>`: All ratings for applicant
- `GET /<user_code>/my-rating`: Current user's rating
- `POST /<user_code>`: Add/update rating and/or comment (Faculty/Admin only) - supports comment-only saves

#### Export (`/api/export/`)
- `POST /selected`: Export selected applicants with chosen data sections (Admin only) 

#### Sessions (`/api/sessions/`)
- `GET /`: List all sessions
- `POST /`: Create new session (Admin only)
- `POST /switch`: Change active session

#### Test Scores (`/api/test-scores/`)
- `GET /<user_code>/scores`: All test scores for applicant
- `PUT /<user_code>/duolingo`: Update Duolingo scores (Admin only)

#### System Logs (`/api/logs/`)
- `GET /logs`: System activity logs (Admin only)

### Security Implementation

#### Authentication
- **Flask-Login**: Session-based user management
- **bcrypt**: Password hashing with salt
- **Session Security**: HTTPOnly cookies, CSRF protection
- **Role Validation**: Server-side permission checks

#### Authorization Levels
- **Route Protection**: Decorator-based access control
- **Database Security**: Parameterized queries prevent SQL injection
- **Input Validation**: Server-side data sanitization
- **Audit Trail**: Complete activity logging for accountability

#### Permission Matrix
| Feature | Admin | Faculty | Viewer |
|---------|-------|---------|--------|
| View Applications | ✅ | ✅ | ✅ |
| Upload CSV | ✅ | ❌ | ❌ |
| Export Data | ✅ | ❌ | ❌ |
| Rate Students | ✅ | ✅ | ❌ |
| Add Comments | ✅ | ✅ | ❌ |
| Change Status | ✅ | ❌ | ❌ |
| Edit English Status | ✅ | ❌ | ❌ |
| Manage Users | ✅ | ❌ | ❌ |
| Create Sessions | ✅ | ❌ | ❌ |
| View Logs | ✅ | ❌ | ❌ |
| View Statistics | ✅ | ✅ | ✅ |

### Frontend Architecture

#### Component Structure
- **applicants.js**: Main application controller
  - Handles data loading, modal management, user interactions
  - Manages application state and API communications
  - Implements permission-based UI updates

- **auth.js**: Authentication management
  - User session handling and validation
  - Role-based navigation control
  - Logout functionality

#### State Management
- **No External Framework**: Uses vanilla JavaScript for simplicity
- **Event-Driven**: DOM-based event handling for user interactions
- **API-First**: RESTful communication with backend
- **Responsive**: Tailwind CSS for mobile-friendly design

#### Data Flow
1. **User Interaction**: Frontend captures user actions
2. **API Call**: JavaScript makes authenticated requests
3. **Server Processing**: Flask validates permissions and processes data
4. **Database Update**: PostgreSQL handles data persistence
5. **Response**: JSON data returned to frontend
6. **UI Update**: DOM manipulation reflects changes

### Development Workflows

#### Adding New Features

1. **Backend Changes**:
   ```python
   # Add API route in appropriate api/ file
   @blueprint.route("/new-endpoint", methods=["POST"])
   @login_required
   def new_feature():
       # Implement permission checking
       # Process request data
       # Return JSON response
   ```

2. **Database Changes**:
   ```sql
   -- Add to schema.sql
   ALTER TABLE table_name ADD COLUMN new_field VARCHAR(255);
   ```

3. **Frontend Integration**:
   ```javascript
   // Add to appropriate JS file
   async function callNewEndpoint() {
       const response = await fetch('/api/new-endpoint', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify(data)
       });
   }
   ```

#### Testing Approach
- **Manual Testing**: Use provided seed data and test accounts
- **Permission Testing**: Verify role-based access controls
- **Data Validation**: Test with various CSV formats and edge cases
- **Browser Testing**: Ensure cross-browser compatibility

### Deployment Considerations

#### Production Setup
- **Environment Variables**: Use production-grade secrets
- **Database**: Configure PostgreSQL with proper indexing
- **SSL/HTTPS**: Enable secure connections
- **Session Security**: Set secure cookie flags
- **File Upload**: Implement size limits and validation

#### Performance Optimization
- **Database Indexing**: Optimize query performance
- **Static Assets**: Use CDN for CSS/JS delivery
- **Caching**: Implement appropriate caching strategies
- **Connection Pooling**: Optimize database connections

#### Monitoring and Maintenance
- **Activity Logs**: Built-in audit trail for troubleshooting
- **Error Handling**: Comprehensive error reporting
- **Data Backup**: Regular PostgreSQL backups
- **User Management**: Regular review of user access levels

### Troubleshooting

#### Common Issues

**Database Connection Errors**
```bash
# Check PostgreSQL service status
sudo systemctl status postgresql

# Verify credentials in .env file
# Ensure database exists and user has permissions
```

**CSS Not Loading**
```bash
# Rebuild Tailwind CSS
npm run build-css-once

# Check if output.css was generated
ls -la static/css/
```

**Permission Denied Errors**
- Verify user roles in database
- Check Flask-Login session status
- Review API route decorators

**CSV Upload Issues**
- Validate CSV format and column headers
- Check file size limitations
- Verify admin privileges

#### Debug Mode
```bash
# Enable Flask debug mode for development
export FLASK_DEBUG=1
python main.py
```

#### Log Analysis
- Check browser console for JavaScript errors
- Review Flask logs for server-side issues
- Use database logs for query debugging
- Access activity logs through admin interface

---

## License

This project is developed for the University of British Columbia's Masters of Data Science program. All rights reserved.

---

**Need Help?** 
- Check the troubleshooting section for common issues
- Review the user documentation for your specific role
- Examine the technical documentation for implementation details
- Use the provided test accounts to explore system functionality