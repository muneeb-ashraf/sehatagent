#!/usr/bin/env python3
"""
Database Initialization Script
Creates all necessary tables in Cloud SQL PostgreSQL

Run this script once before first deployment.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.database.connection import Base
from app.database.models import HealthSession, AgentLog, SessionFeedback, CachedResponse, AggregatedStats
from app.config import get_settings


def init_database():
    """Initialize database tables"""
    print("=" * 50)
    print("SehatAgent - Database Initialization")
    print("=" * 50)
    
    settings = get_settings()
    
    print(f"\nConnecting to database...")
    print(f"Host: {settings.DB_HOST}")
    print(f"Database: {settings.DB_NAME}")
    
    try:
        # Create sync engine for migrations
        engine = create_engine(settings.sync_database_url, echo=True)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"\nPostgreSQL Version: {version}")
        
        # Create all tables
        print("\nCreating tables...")
        Base.metadata.create_all(engine)
        
        # List created tables
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public'
            """))
            tables = [row[0] for row in result]
            
            print("\nCreated tables:")
            for table in tables:
                print(f"  - {table}")
        
        print("\n" + "=" * 50)
        print("Database initialization complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure your database credentials are correct in .env file")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
