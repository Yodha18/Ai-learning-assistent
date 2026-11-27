#!/usr/bin/env python3
"""
AI Learning Assistant - Setup and Initialization Script

This script helps set up the project for development and production environments.
"""

import sys
import subprocess
import os
from pathlib import Path
import shutil


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def check_python_version():
    """Check Python version."""
    if sys.version_info < (3, 9):
        print(f"❌ Python 3.9+ required, found {sys.version_info.major}.{sys.version_info.minor}")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} OK")


def install_requirements():
    """Install project requirements."""
    print("📦 Installing requirements...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True
        )
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True,
            capture_output=False
        )
        print("✅ Requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        sys.exit(1)


def create_directories():
    """Create necessary directories."""
    print("📁 Creating necessary directories...")
    directories = [
        "uploads",
        "vector_store",
        "logs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   ✓ {directory}/")
    
    print("✅ Directories created")


def check_env_file():
    """Check and create .env file if needed."""
    print("⚙️  Checking .env configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("   📝 Creating .env from .env.example")
            shutil.copy(env_example, env_file)
        else:
            print("   ⚠️  No .env or .env.example found")
            print("   📝 Creating default .env")
            with open(env_file, 'w') as f:
                f.write("""# Database
DATABASE_URL=sqlite:///./ai_learning.db

# Security
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Gemini
GEMINI_API_KEY=
GEMINI_CHAT_MODEL=gemini-3.5-flash-lite
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

# File Upload
UPLOAD_DIR=uploads
MAX_UPLOAD_SIZE_MB=20
""")
        print("✅ .env file ready")
    else:
        print("✅ .env file exists")


def initialize_database():
    """Initialize the database."""
    print("🗄️  Initializing database...")
    try:
        from app.database import engine, Base
        Base.metadata.create_all(bind=engine)
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Could not initialize database: {e}")
        print("   This may be OK if database already exists")


def run_tests():
    """Run tests to verify setup."""
    print("🧪 Running tests...")
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            check=False
        )
    except Exception as e:
        print(f"⚠️  Tests not available: {e}")


def main():
    """Main setup routine."""
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║     AI Learning Assistant - Setup & Initialization      ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    print_header("Checking Python Version")
    check_python_version()
    
    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print_header("Installing Requirements")
    install_requirements()
    
    print_header("Creating Directories")
    create_directories()
    
    print_header("Checking Configuration")
    check_env_file()
    
    print_header("Initializing Database")
    initialize_database()
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║              Setup Complete! 🎉                          ║
    ╚══════════════════════════════════════════════════════════╝
    
    Next steps:
    
    1. Configure your .env file with your settings
    2. Start the development server:
       
       python run_dev.py
       
       Or manually:
       
       python -m uvicorn app.main:app --reload
    
    3. Open in browser:
       http://127.0.0.1:8000
    
    4. API Documentation:
       http://127.0.0.1:8000/docs
    
    For more information, see README.md
    """)


if __name__ == "__main__":
    main()
