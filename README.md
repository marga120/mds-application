# MDS Application Project

A Flask web application for managing Masters of Data Science (MDS) student applications at the University of British Columbia (UBC).

## 📋 Prerequisites

Before running this application, make sure you have the following installed:

- **Python** - [Download here](https://www.python.org/downloads/)
- **Node.js** - [Download here](https://nodejs.org/)
- **PostgreSQL** - [Download here](https://www.postgresql.org/download/)
- **Git** - [Download here](https://git-scm.com/)

## 🚀 Local Setup & Installation

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
# Install Node.js packages
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

## 🎮 Running the Application

### Run Everything with One Command
```bash
npm run dev
```
This will start both the Tailwind CSS compiler and Flask server simultaneously.

## 🌐 Access the Application

Once running, open your browser and navigate to:
```
http://localhost:5000
```

## 🗃️ Database Setup & Seeding

### Initialize Database Tables
The database will be automatically initialized when you first run the application. 

### Seed Test Data
To populate the database with test users and roles:
```bash
python seed.py
```

This will create:
- **Roles**: Admin, Faculty, Viewer
- **Test Users**: Various users with different roles
- **Sample Data**: Ready for testing

### Test Login Credentials
After seeding, you can use these test accounts:
- **Admin**: `testuser1@example.com` / `password` and `testuser2@example.com` / `password`
- **Faculty**: `testuser3@example.com` / `password`
- **Viewer**: `testuser4@example.com` / `password`

## 🛠️ Troubleshooting

### Common Issues

**Database Connection Error:**
- Verify PostgreSQL is running
- Check `.env` file credentials
- Ensure database exists

**CSS Not Loading:**
- Run `npm run build-css` to generate styles
- Check if `static/css/output.css` exists
- Verify Tailwind dependencies are installed

**Port Already in Use:**
- Flask default port is 5000
- Kill existing processes or change port in `main.py`

**npm Command Errors:**
- Ensure Node.js is installed and updated
- Try deleting `node_modules` and running `npm install` again

**Tailwind CSS Issues:**
- If `npm run dev` fails, try running `npm run build-css` separately first
- Check that `static/css/input.css` exists
- Verify `@tailwindcss/cli@next` is installed

## 🎨 Customization

### UBC Colors
The application uses official UBC colors defined in `static/css/input.css`:
- **UBC Blue**: `#002145`
- **UBC Light Blue**: `#0055B7`
- **Gray Light**: `#F5F5F5`
- **Gray**: `#6B7280`

### Adding New Features
1. **API Routes**: Add to `api/`
2. **Database Operations**: Add to `models/`
3. **Frontend**: Modify `templates/index.html` and `static/js/main.js`
4. **Styling**: Update `static/css/input.css` with new Tailwind classes

## 📄 License

This project is created for the University of British Columbia's Masters of Data Science program.

---

**Need Help?** Check the troubleshooting section above or review the project structure to understand how components work together.
