"""Landing Page Module - Entry point and utilities."""

from pathlib import Path


class LandingPageConfig:
    """Configuration for landing page."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.html_file = self.base_dir / "code.html"
        self.screenshot = self.base_dir / "screen.png"
    
    def get_html(self) -> str:
        """Get HTML content."""
        if self.html_file.exists():
            with open(self.html_file, 'r', encoding='utf-8') as f:
                return f.read()
        return "<p>Landing page not found</p>"
    
    def has_screenshot(self) -> bool:
        """Check if screenshot exists."""
        return self.screenshot.exists()
    
    def get_screenshot_path(self) -> str:
        """Get screenshot path."""
        return str(self.screenshot) if self.has_screenshot() else None


# Create global config instance
config = LandingPageConfig()


__all__ = ["LandingPageConfig", "config"]
