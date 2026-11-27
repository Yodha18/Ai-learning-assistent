#!/usr/bin/env python3
"""
Quick start script for accessing individual modules.
Run this script to get information about available modules.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_info():
    """Print module information."""
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     Stitch SmartStudy AI Assistant - Module Information        ║
    ╚════════════════════════════════════════════════════════════════╝
    
    Available Modules:
    
    1. Academic Intelligence
       Location: stitch_smartstudy_ai_assistant/academic_intelligence/
       Description: Design specifications and academic features
       
    2. Landing Page
       Location: stitch_smartstudy_ai_assistant/landing_page/
       Description: Application landing page
       
    3. Login Page  
       Location: stitch_smartstudy_ai_assistant/login_page/
       Description: User authentication page
       
    4. Registration Page
       Location: stitch_smartstudy_ai_assistant/registration_page/
       Description: User registration page
    
    Main Application:
    ─────────────────
    To run the main FastAPI application:
    
        cd ../.. (navigate to project root)
        python -m uvicorn app.main:app --reload
    
    The application will be available at:
        http://127.0.0.1:8000
    
    API Documentation:
        http://127.0.0.1:8000/docs
        http://127.0.0.1:8000/redoc
    """)


def main():
    """Main entry point."""
    print_info()


if __name__ == "__main__":
    main()
