"""Registration Page Module - Entry point and utilities."""

from pathlib import Path


class RegistrationPageConfig:
    """Configuration for registration page."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.html_file = self.base_dir / "code.html"
    
    def get_html(self) -> str:
        """Get HTML content."""
        if self.html_file.exists():
            with open(self.html_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "<p>Registration page not found</p>"


# Create global config instance
config = RegistrationPageConfig()


__all__ = ["RegistrationPageConfig", "config"]
