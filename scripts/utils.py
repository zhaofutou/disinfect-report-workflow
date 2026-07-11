"""Shared utilities for disinfection report workflow."""

import os
import yaml
import psycopg2
from pathlib import Path

def load_config():
    """Load config from config/config.yaml."""
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_db_connection():
    """Get PostgreSQL connection using config."""
    config = load_config()
    db = config['database']
    return psycopg2.connect(
        host=db['host'],
        port=db['port'],
        database=db['name'],
        user=db['user'],
        password=db['password']
    )

def get_supabase_client():
    """Get Supabase client using config."""
    from supabase import create_client
    config = load_config()
    return create_client(
        config['supabase']['url'],
        config['supabase']['service_role_key']
    )

def to_binary(val):
    """Convert √ mark to 1, else 0."""
    return 1 if '√' in str(val) else 0

def get_event_id(sample_id):
    """Extract eventID (first 9 chars) from sampleID."""
    return sample_id[:9]

def list_files(directory, extensions=None):
    """List files in directory, optionally filtered by extension."""
    path = Path(directory)
    if extensions:
        return [f for f in path.iterdir() if f.suffix.lower() in extensions]
    return list(path.iterdir())

def print_table(rows, headers):
    """Print formatted table."""
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    
    # Print header
    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        print(" | ".join(str(cell).ljust(widths[i]) for i, cell in enumerate(row)))
