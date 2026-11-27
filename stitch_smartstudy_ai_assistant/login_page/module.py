"""Login Page Module - Entry point and utilities."""

from pathlib import Path


class LoginPageConfig:
    """Configuration for login page."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.html_file = self.base_dir / "code.html"
    
    def get_html(self) -> str:
        """Get HTML content."""
        if self.html_file.exists():
            with open(self.html_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "<p>Login page not found</p>"


# Create global config instance
config = LoginPageConfig()


__all__ = ["LoginPageConfig", "config"]
