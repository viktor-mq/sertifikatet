# Driving Theory Platform - MySQL Migration

This project has been migrated from SQLite to MySQL with Flask-SQLAlchemy ORM.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy the example environment file and update with your MySQL credentials:
```bash
cp .env.example .env
```

Edit `.env` and set:
- `DATABASE_URL` - Your MySQL connection string
- `SECRET_KEY` - A secure secret key for sessions
- `ADMIN_PASSWORD` - Password for admin panel access

### 3. Create MySQL Database
Create your MySQL database:
```sql
CREATE DATABASE driving_theory_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Initialize Database Tables
Run the initialization script to create all tables:
```bash
python scripts/init_mysql_db.py
```

Or manually with Flask-Migrate:
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Migrate Data from SQLite (Optional)
If you have existing data in SQLite database:
```bash
python scripts/migrate_to_mysql.py
```

### 6. Run the Application
```bash
python run.py
```

The application will be available at http://localhost:5000

## Key Changes Made

1. **Database Layer**:
   - Replaced raw SQLite3 queries with SQLAlchemy ORM
   - Added proper model relationships with foreign keys
   - Implemented cascade deletes where appropriate

2. **Configuration**:
   - Environment-based configuration with python-dotenv
   - Secure defaults with option to override via .env file
   - MySQL connection pooling configuration

3. **Models**:
   - Created comprehensive models for all tables in plan.yaml
   - Added relationships between models
   - Implemented proper constraints and indexes

4. **Admin Panel**:
   - Updated to use SQLAlchemy queries instead of raw SQL
   - Maintained SQL console functionality for admin users
   - Improved error handling and transactions

5. **Application Structure**:
   - Implemented Flask application factory pattern
   - Organized code into blueprints (admin, auth, api, quiz, main)
   - Better separation of concerns

## Database Schema

The MySQL database includes the following main tables:
- `users` - User accounts
- `questions` - Quiz questions
- `options` - Answer options for questions
- `traffic_signs` - Traffic sign information
- `quiz_sessions` - User quiz attempts
- `quiz_responses` - Individual question responses
- And many more (see models.py for complete schema)

## Admin Access

Access the admin panel at http://localhost:5000/admin

Default password: (change via ADMIN_PASSWORD in .env)

## API Endpoints

- `GET /api/questions` - Get questions with filters
- `GET /api/categories` - Get all categories
- `GET /api/traffic-signs` - Get traffic signs
- `GET /api/stats` - Get platform statistics

## Security Notes

1. Change all default passwords and secrets in production
2. Use HTTPS in production
3. Configure proper MySQL user permissions
4. Regular backups recommended
