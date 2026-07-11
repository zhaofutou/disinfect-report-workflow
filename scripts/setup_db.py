#!/usr/bin/env python3
"""Setup database tables for disinfection report workflow."""

import sys
sys.path.insert(0, '.')
from utils import get_db_connection

def setup_tables():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Create event_inspections table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS event_inspections (
        id BIGSERIAL PRIMARY KEY,
        eventID TEXT NOT NULL,
        sampleCount TEXT,
        clientInfo TEXT,
        inspectionDate DATE,
        inspectionTarget TEXT,
        inspectionStandards TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """)
    print("✓ event_inspections table ready")
    
    # Create sample_details table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sample_details (
        id BIGSERIAL PRIMARY KEY,
        event TEXT NOT NULL,
        client TEXT,
        sampleID TEXT NOT NULL,
        sampleLocation TEXT,
        sampleName TEXT,
        sampleArea TEXT,
        bacCount INTEGER DEFAULT 0,
        ronglian INTEGER DEFAULT 0,
        jinpu INTEGER DEFAULT 0,
        tonglv INTEGER DEFAULT 0,
        UV INTEGER DEFAULT 0,
        observation TEXT,
        created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """)
    print("✓ sample_details table ready")
    
    # Add observation column if missing (for existing tables)
    cur.execute("""
    ALTER TABLE sample_details 
    ADD COLUMN IF NOT EXISTS observation TEXT;
    """)
    
    conn.commit()
    cur.close()
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    setup_tables()
