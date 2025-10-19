"""
Database initialization script for Speech Coach application.
Run this script to create database tables and set up initial data.
"""

import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, User, Speech, Session
from database_config import get_database_config, print_database_info

def create_app():
    """Create Flask app with database configuration"""
    app = Flask(__name__)
    
    # Load database configuration
    db_config = get_database_config()
    for key, value in db_config.items():
        app.config[key] = value
    
    # Initialize database
    db.init_app(app)
    
    # Initialize Flask-Migrate
    migrate = Migrate(app, db)
    
    return app, migrate

def init_database():
    """Initialize database with tables"""
    app, migrate_instance = create_app()
    
    with app.app_context():
        print("🚀 Initializing Speech Coach Database...")
        print_database_info()
        
        try:
            # Create all tables
            print("\n📋 Creating database tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Created {len(tables)} tables:")
            for table in tables:
                print(f"   • {table}")
            
            # Initialize Flask-Migrate if migrations folder doesn't exist
            if not os.path.exists('migrations'):
                print("\n🗂️ Initializing Flask-Migrate...")
                from flask_migrate import init
                init()
                print("✅ Flask-Migrate initialized")
            
            print("\n🎉 Database initialization completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Database initialization failed: {str(e)}")
            return False

def create_migration(message="Auto migration"):
    """Create a new database migration"""
    app, migrate_instance = create_app()
    
    with app.app_context():
        try:
            print(f"🔄 Creating migration: {message}")
            from flask_migrate import migrate as create_migrate
            create_migrate(message=message)
            print("✅ Migration created successfully")
            return True
        except Exception as e:
            print(f"❌ Migration creation failed: {str(e)}")
            return False

def run_migrations():
    """Run pending database migrations"""
    app, migrate_instance = create_app()
    
    with app.app_context():
        try:
            print("🔄 Running database migrations...")
            from flask_migrate import upgrade
            upgrade()
            print("✅ Migrations completed successfully")
            return True
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            return False

def reset_database():
    """Reset database - drop all tables and recreate"""
    app, migrate_instance = create_app()
    
    with app.app_context():
        print("⚠️ RESETTING DATABASE - All data will be lost!")
        response = input("Are you sure? Type 'yes' to continue: ")
        
        if response.lower() == 'yes':
            try:
                print("🗑️ Dropping all tables...")
                db.drop_all()
                
                print("📋 Creating fresh tables...")
                db.create_all()
                
                print("✅ Database reset completed successfully!")
                return True
            except Exception as e:
                print(f"❌ Database reset failed: {str(e)}")
                return False
        else:
            print("❌ Database reset cancelled")
            return False

def check_database_connection():
    """Check if database connection is working"""
    app, migrate_instance = create_app()
    
    with app.app_context():
        try:
            print("🔍 Checking database connection...")
            print_database_info()
            
            # Try to execute a simple query
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1"))
                result.close()
            
            print("✅ Database connection successful!")
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {str(e)}")
            print("\n💡 Make sure PostgreSQL is running and credentials are correct")
            print("💡 Check your environment variables:")
            print("   • DATABASE_HOST")
            print("   • DATABASE_PORT") 
            print("   • DATABASE_NAME")
            print("   • DATABASE_USER")
            print("   • DATABASE_PASSWORD")
            return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Speech Coach Database Management')
    parser.add_argument('command', choices=['init', 'migrate', 'upgrade', 'reset', 'check'], 
                       help='Database command to run')
    parser.add_argument('--message', '-m', default='Auto migration', 
                       help='Migration message (for migrate command)')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_database()
    elif args.command == 'migrate':
        create_migration(args.message)
    elif args.command == 'upgrade':
        run_migrations()
    elif args.command == 'reset':
        reset_database()
    elif args.command == 'check':
        check_database_connection()
