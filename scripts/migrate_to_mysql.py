#!/usr/bin/env python
"""
Migration script to transfer data from SQLite to MySQL
"""
import sqlite3
import os
from datetime import datetime
from flask import Flask
from sqlalchemy import create_engine, text
from app import create_app, db
from app.models import (
    User, UserProgress, Achievement, UserAchievement,
    Question, Option, TrafficSign, QuizImage,
    QuizSession, QuizResponse, GameScenario, GameSession,
    Video, VideoCheckpoint, VideoProgress,
    LearningPath, LearningPathItem, UserLearningPath,
    LeaderboardEntry, UserFeedback
)

def migrate_sqlite_to_mysql():
    """Migrate data from SQLite to MySQL"""
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Drop all tables and recreate (BE CAREFUL - this will delete all existing data)
        print("Creating MySQL database schema...")
        db.drop_all()
        db.create_all()
        
        # Connect to SQLite database
        sqlite_db = 'questions.db'
        if not os.path.exists(sqlite_db):
            print(f"SQLite database {sqlite_db} not found!")
            return
        
        conn = sqlite3.connect(sqlite_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Migrate questions table
        print("Migrating questions...")
        cursor.execute("SELECT * FROM questions")
        questions = cursor.fetchall()
        
        question_map = {}  # Map old IDs to new IDs
        
        for row in questions:
            q = Question(
                question=row['question'],
                correct_option=row['correct_option'],
                category=row.get('category', 'Ukategorisert'),
                subcategory=row.get('subcategory'),
                difficulty_level=row.get('difficulty_level', 1),
                explanation=row.get('explanation'),
                image_filename=row.get('image_filename'),
                is_active=True,
                question_type='multiple_choice'
            )
            db.session.add(q)
            db.session.flush()
            question_map[row['id']] = q.id
        
        # Migrate options table
        print("Migrating options...")
        cursor.execute("SELECT * FROM options")
        options = cursor.fetchall()
        
        for row in options:
            if row['question_id'] in question_map:
                opt = Option(
                    question_id=question_map[row['question_id']],
                    option_letter=row.get('option_letter', row.get('option_letter', 'a')),
                    option_text=row['option_text']
                )
                db.session.add(opt)
        
        # Migrate traffic_signs table if it exists
        try:
            print("Migrating traffic signs...")
            cursor.execute("SELECT * FROM traffic_signs")
            signs = cursor.fetchall()
            
            for row in signs:
                ts = TrafficSign(
                    sign_code=row.get('sign_code', row.get('sign_code', '')),
                    description=row.get('description'),
                    category=row.get('category'),
                    filename=row['filename'],
                    explanation=row.get('explanation', '')

                )
                db.session.add(ts)
        except sqlite3.OperationalError:
            print("No traffic_signs table found in SQLite database")
        
        # Migrate quiz_images table if it exists
        try:
            print("Migrating quiz images...")
            cursor.execute("SELECT * FROM quiz_images")
            images = cursor.fetchall()
            
            for row in images:
                qi = QuizImage(
                    filename=row['filename'],
                    folder=row.get('folder'),
                    title=row.get('title'),
                    description=row.get('description')
                )
                db.session.add(qi)
        except sqlite3.OperationalError:
            print("No quiz_images table found in SQLite database")
        
        # Commit all changes
        print("Committing changes to MySQL database...")
        db.session.commit()
        
        # Close SQLite connection
        conn.close()
        
        print("Migration completed successfully!")
        
        # Print summary
        print("\nMigration Summary:")
        print(f"Questions migrated: {len(questions)}")
        print(f"Options migrated: {len(options)}")
        print(f"Total questions in MySQL: {Question.query.count()}")
        print(f"Total options in MySQL: {Option.query.count()}")
        print(f"Total traffic signs in MySQL: {TrafficSign.query.count()}")
        print(f"Total quiz images in MySQL: {QuizImage.query.count()}")


if __name__ == '__main__':
    migrate_sqlite_to_mysql()
