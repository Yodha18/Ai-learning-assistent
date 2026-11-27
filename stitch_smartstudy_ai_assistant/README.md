"""
Stitch SmartStudy AI Assistant - Main Entry Point

This package contains the AI Learning Assistant application with multiple
components for personalized learning assistance.
"""

__version__ = "1.0.0"
__author__ = "AI Learning Assistant Team"

# Import key components
from . import academic_intelligence
from . import landing_page
from . import login_page
from . import registration_page

__all__ = [
    "academic_intelligence",
    "landing_page", 
    "login_page",
    "registration_page"
]
