#!/usr/bin/env python3
"""
AI Learning Assistant - Development Server Starter Script

This script provides a convenient way to start the development server
with proper configuration and error handling.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_requirements(venv_python):
    """Check if required packages are installed in the virtual environment."""
    required = ['fastapi', 'uvicorn', 'sqlalchemy', 'pydantic']
    missing = []
    
    for package in required:
        try:
            result = subprocess.run(
                [str(venv_python), "-c", f"import {package}"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append(package)
        except Exception:
            missing.append(package)
    
    if missing:
        print(f"Missing required packages: {', '.join(missing)}")
        print(f"   Install with: pip install -r requirements.txt")
        return False
    
    return True


def main():
    """Main entry point."""
    print("AI Learning Assistant - Development Server")
    print("Powered by FastAPI + Uvicorn")
    print()
    
    # Get the project root directory
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    
    # Use the interpreter that launched this script, including an active virtual environment.
    python_executable = Path(sys.executable)
    
    # Check requirements
    if not check_requirements(python_executable):
        sys.exit(1)
    
    print(f"Project root: {project_root}")
    print(f"Python: {python_executable}")
    print()
    
    # Start the development server
    print("Starting development server...")
    print("   API Documentation: http://127.0.0.1:8000/docs")
    print("   Alternative Docs:  http://127.0.0.1:8000/redoc")
    print()
    print("   Press CTRL+C to stop the server")
    print()
    
    try:
        subprocess.run(
            [str(python_executable), "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000"],
            check=False
        )
    except KeyboardInterrupt:
        print("\n\nDevelopment server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
