#!/usr/bin/env python3
"""
Run script for the Grant Applicant Vetting Tool.

Usage:
    python run.py              # Run in development mode
    python run.py --prod       # Run in production mode
    python run.py --init-db    # Initialize the database only
"""

import argparse
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def init_database():
    """Initialize the database tables."""
    from app import app, db

    with app.app_context():
        db.create_all()
        print("Database initialized successfully.")


def run_development():
    """Run the app in development mode."""
    from app import app

    print("Starting Grant Applicant Vetting Tool in development mode...")
    print("Dashboard available at: http://localhost:5000")
    print("Press Ctrl+C to stop")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )


def run_production():
    """Run the app in production mode."""
    try:
        from waitress import serve
        from app import app

        print("Starting Grant Applicant Vetting Tool in production mode...")
        print("Dashboard available at: http://localhost:5000")

        serve(app, host='0.0.0.0', port=5000)
    except ImportError:
        print("Error: waitress not installed. Install with: pip install waitress")
        print("Falling back to Flask development server (not recommended for production)")
        run_development()


def main():
    parser = argparse.ArgumentParser(
        description='Grant Applicant Vetting Tool'
    )
    parser.add_argument(
        '--prod', '--production',
        action='store_true',
        help='Run in production mode (requires waitress)'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize the database and exit'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run on (default: 5000)'
    )

    args = parser.parse_args()

    # Load environment variables from .env if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv not installed, skip

    if args.init_db:
        init_database()
        return

    # Initialize database before running
    init_database()

    if args.prod:
        run_production()
    else:
        run_development()


if __name__ == '__main__':
    main()
