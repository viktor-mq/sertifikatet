# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask-based web platform for Norwegian driving theory test preparation. The system includes quizzes, user authentication, admin panel, progress tracking, and gamification features.

**Architecture**: Flask + SQLAlchemy + MySQL with modular blueprint structure

## Essential Files

- `plan/plan.yaml` - Complete project specification and database schema
- `project_checklist.txt` - Authoritative roadmap with phase completion status
- `app/models.py` - Complete database models with relationships
- `run.py` - Application entry point
- `config.py` - Environment-based configuration

## Development Commands

### Database Management
```bash
# Initialize database (first time only)
python scripts/init_mysql_db.py

# Flask migrations
flask db init
flask db migrate -m "Migration description"
flask db upgrade

# Import questions from CSV
python scripts/import_questions.py

# Generate statistics
python scripts/generate_stats.py
```

### Running the Application
```bash
# Development server
python run.py

# With custom environment
HOST=0.0.0.0 PORT=8000 python run.py
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with DATABASE_URL, SECRET_KEY, ADMIN_PASSWORD
```

## Architecture Overview

**Blueprint Structure**:
- `app/main/` - Homepage and general routes
- `app/auth/` - User authentication (login, register, profile)
- `app/quiz/` - Quiz functionality and session management
- `app/admin/` - Admin panel for content management
- `app/api/` - REST API endpoints
- `app/game/` - Interactive driving games
- `app/video/` - Video learning modules

**Key Models**:
- `User` → `UserProgress` (1:1) - User accounts and progress tracking
- `Question` → `Option` (1:many) - Quiz questions and multiple choice options
- `QuizSession` → `QuizResponse` (1:many) - Quiz attempts and individual answers
- `Achievement` ← `UserAchievement` → `User` (many:many) - Gamification system

**Image Management**:
- Static files in `static/images/` with organized folders
- Traffic signs in `static/images/signs/` by category
- Admin panel handles image uploads and organization

## Current Development Status

**✅ Completed (Phases 1-4)**:
- Flask application with MySQL database
- User authentication and profiles
- Admin panel with question management
- Complete quiz functionality with categories

**🚧 In Progress (Phase 5)**:
- User progress tracking and statistics
- Achievement system implementation
- Leaderboard functionality

**📋 Planned (Phases 6-13)**:
- Learning pathways, video modules, interactive games
- Mobile optimization, payment integration
- Advanced AI features and production deployment

## Key Conventions

- **Database**: Use SQLAlchemy ORM, avoid raw SQL except in admin console
- **Routes**: Follow RESTful patterns, use blueprints for organization
- **Templates**: Jinja2 with base.html, Norwegian language throughout
- **Styling**: Tailwind CSS with custom gradient design system
- **Security**: Password hashing with Werkzeug, CSRF protection via Flask-WTF

- Always check `project_checklist.txt` for current phase status — mark tasks as [✅] once completed and maintain indentation and formatting
- Reference `plan/plan.yaml` for database schema and requirements
- Maintain Norwegian language in all user-facing text
- Image uploads go to appropriate `static/images/` subdirectories
- Admin access at `/admin` with environment-configured password